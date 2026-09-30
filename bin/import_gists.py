#!/usr/bin/env python3
"""Turn the notebooks in the owner's public gists into Markdown notes.

Each entry in _data/gists.yml names a gist that holds a single Jupyter
notebook with stored outputs.  For every entry this script

  * fetches the gist from the GitHub API,
  * saves the notebook verbatim to assets/notebooks/<slug>.ipynb,
  * writes the figures it contains to assets/img/notes/<slug>/output_NN.png,
  * and converts the cells to a post at _posts/<date>-<slug>.md, with code
    cells as fenced Python blocks and their stored outputs directly below.

Nothing is re-executed: only the outputs stored in the notebook are used.
The post's front matter records the gist's updated_at timestamp, and a post
whose timestamp already matches the API is left alone, so the script can be
run repeatedly (e.g. from a workflow) and only touches what changed.

Run from the repository root:

    python3 bin/import_gists.py                   # import everything
    python3 bin/import_gists.py --dry-run         # report, write nothing
    python3 bin/import_gists.py --only <slug>     # a single entry
    python3 bin/import_gists.py --force           # rewrite unchanged posts too

Only the standard library is used (the small YAML parser below is enough for
the flat format documented at the top of _data/gists.yml).  Set GITHUB_TOKEN
to raise the API rate limit.

Conversion notes
  * The notebook's leading H1 heading is dropped; the layout shows the title.
  * Inline math written as $x$ becomes $$x$$, which kramdown turns into
    \\(x\\) for MathJax (single dollars are not recognised by this site).
  * Any block containing Liquid syntax ({{ or {%) is wrapped in raw tags.
  * Long text outputs are truncated to their first 40 and last 10 lines.
  * Jupyter widget stubs (live progress bars) are not shown; HTML outputs are
    kept only when they are tables.
"""

import argparse
import base64
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "_data" / "gists.yml"
POSTS = ROOT / "_posts"
NOTEBOOKS = ROOT / "assets" / "notebooks"
IMAGES = ROOT / "assets" / "img" / "notes"
API = "https://api.github.com/gists"
GIST_URL = "https://gist.github.com/maxisi"
USER_AGENT = "maxisi.github.io gist importer (https://github.com/maxisi/maxisi.github.io)"

# Text outputs longer than MAX_LINES lines keep only their head and tail.
MAX_LINES = 60
HEAD_LINES = 40
TAIL_LINES = 10

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
LIQUID = re.compile(r"\{\{|\{%")
# A bare object repr such as "<IPython.core.display.HTML object>".
OBJECT_REPR = re.compile(r"^<[\w.]+(?: [\w.]+)* object(?: at 0x[0-9a-fA-F]+)?>$|^<[\w.]+ at 0x[0-9a-fA-F]+>$")


# ----------------------------------------------------------------------------
# _data/gists.yml


def parse_gists(path=SOURCE):
    """Parse the flat list of maps in _data/gists.yml (format documented there)."""
    entries, current = [], None
    for lineno, raw in enumerate(path.read_text().splitlines(), 1):
        line = raw.split(" #", 1)[0].rstrip() if not raw.lstrip().startswith("#") else ""
        if not line.strip():
            continue
        item = re.match(r"^-\s+(\w+):\s*(.*)$", line)
        cont = re.match(r"^\s+(\w+):\s*(.*)$", line)
        if item:
            current = {}
            entries.append(current)
            key, value = item.groups()
        elif cont and current is not None:
            key, value = cont.groups()
        else:
            sys.exit(f"{path}:{lineno}: cannot parse line: {raw!r}")
        current[key] = parse_scalar(value)
    for entry in entries:
        missing = {"id", "slug", "title", "date", "tags", "description"} - set(entry)
        if missing:
            sys.exit(f"{path}: entry {entry.get('id', '?')} lacks {sorted(missing)}")
        if not isinstance(entry["tags"], list):
            entry["tags"] = [entry["tags"]]
    return entries


def parse_scalar(value):
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        return [parse_scalar(v) for v in value[1:-1].split(",") if v.strip()]
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


# ----------------------------------------------------------------------------
# GitHub API


def fetch(url, token=None):
    headers = {"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8")


def fetch_gist(gist_id, token=None):
    """Return (gist metadata, notebook filename, notebook text) for a gist."""
    gist = json.loads(fetch(f"{API}/{gist_id}", token))
    notebooks = [f for f in gist["files"].values() if f["filename"].endswith(".ipynb")]
    if len(notebooks) != 1:
        raise ValueError(f"expected one .ipynb in gist {gist_id}, found {len(notebooks)}")
    nb = notebooks[0]
    text = fetch(nb["raw_url"], token) if nb.get("truncated") else nb["content"]
    return gist, nb["filename"], text


# ----------------------------------------------------------------------------
# Notebook -> Markdown


def join(source):
    return "".join(source) if isinstance(source, list) else str(source)


def strip_ansi(text):
    return ANSI.sub("", text)


def truncate(text):
    lines = text.splitlines()
    if len(lines) <= MAX_LINES:
        return text
    omitted = len(lines) - HEAD_LINES - TAIL_LINES
    kept = lines[:HEAD_LINES] + [f"... ({omitted} lines omitted) ..."] + lines[-TAIL_LINES:]
    return "\n".join(kept)


def fence(text, lang):
    """Return a fenced block, wrapped in raw tags when Liquid would choke on it."""
    text = text.rstrip("\n")
    ticks = "```"
    while ticks in text:  # a fence longer than any run of backticks inside
        ticks += "`"
    block = f"{ticks}{lang}\n{text}\n{ticks}"
    return raw_if_needed(block)


def raw_if_needed(text):
    if LIQUID.search(text):
        return "{% raw %}\n" + text + "\n{% endraw %}"
    return text


def double_dollars(text):
    """Rewrite $x$ inline math as $$x$$, leaving code spans and fences alone.

    Display math delimited by lone $$ lines is also padded with blank lines,
    since kramdown treats $$...$$ as block math only when it stands apart from
    the surrounding paragraph (Jupyter renders it as display math regardless).
    """
    out, in_fence, in_display, after_display = [], False, False, False
    for line in text.split("\n"):
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        if line.strip() == "$$":
            if not in_display and out and out[-1].strip():
                out.append("")
            in_display = not in_display
            after_display = not in_display
            out.append(line)
            continue
        if in_display:
            out.append(line)
            continue
        if after_display:
            after_display = False
            if line.strip():
                out.append("")
        # Split off inline code spans so their dollars are untouched.
        parts = re.split(r"(`+[^`]*`+)", line)
        for i in range(0, len(parts), 2):
            parts[i] = re.sub(
                r"(?<![\\$])\$(?!\$)((?:[^$\\\n]|\\.)+?)(?<![\\$])\$(?!\$)",
                r"$$\1$$",
                parts[i],
            )
        out.append("".join(parts))
    return "\n".join(out)


def convert_markdown(source, first):
    text = join(source).strip("\n")
    if first:
        lines = text.split("\n")
        if lines and re.match(r"^#\s+\S", lines[0]):
            text = "\n".join(lines[1:]).lstrip("\n")
    if not text.strip():
        return None
    return raw_if_needed(double_dollars(text))


class Figures:
    """Hands out sequential output_NN.png paths under assets/img/notes/<slug>/."""

    def __init__(self, slug):
        self.dir = IMAGES / slug
        self.count = 0
        self.files = {}  # path -> bytes, written at the end

    def add(self, data):
        self.count += 1
        path = self.dir / f"output_{self.count:02d}.png"
        self.files[path] = base64.b64decode(join(data))
        rel = path.relative_to(ROOT).as_posix()
        return (
            "{% include figure.html path=\"" + rel
            + "\" class=\"img-fluid rounded z-depth-1\" zoomable=true %}"
        )


def convert_outputs(outputs, figures):
    blocks, stream = [], None  # merge consecutive stream outputs of one kind

    def flush():
        nonlocal stream
        if stream is not None:
            text = truncate(strip_ansi(stream[1]))
            if text.strip():
                blocks.append(fence(text, "text"))
            stream = None

    for output in outputs:
        kind = output.get("output_type")
        if kind == "stream":
            text = join(output.get("text", ""))
            if stream is not None and stream[0] == output.get("name"):
                stream = (stream[0], stream[1] + text)
            else:
                flush()
                stream = (output.get("name"), text)
            continue
        flush()
        if kind in ("execute_result", "display_data"):
            data = output.get("data", {})
            if "image/png" in data:
                blocks.append(figures.add(data["image/png"]))
            elif "application/vnd.jupyter.widget-view+json" in data:
                continue  # a stub for a live widget (usually a progress bar)
            elif "text/html" in data and "<table" in join(data["text/html"]):
                html = join(data["text/html"]).strip()
                blocks.append(raw_if_needed(
                    "<div class=\"notes-table\">\n{::nomarkdown}\n" + html + "\n{:/nomarkdown}\n</div>"
                ))
            elif "text/plain" in data:
                text = truncate(strip_ansi(join(data["text/plain"])))
                # A bare object repr standing in for a rich output we dropped
                # (e.g. "<IPython.core.display.HTML object>" for a progress
                # bar) says nothing useful, so skip it.
                stub = "text/html" in data and OBJECT_REPR.match(text.strip())
                if text.strip() and not stub:
                    blocks.append(fence(text, "text"))
        elif kind == "error":
            trace = "\n".join(strip_ansi(join(line)) for line in output.get("traceback", []))
            text = f"{output.get('ename', 'Error')}: {output.get('evalue', '')}\n{trace}"
            blocks.append(fence(truncate(text), "text"))
    flush()
    return blocks


def front_matter(entry, gist):
    def quote(value):
        return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'

    return "\n".join([
        "---",
        "layout: post",
        f"title: {quote(entry['title'])}",
        f"date: {entry['date']} 12:00:00-0400",
        f"description: {quote(entry['description'])}",
        f"tags: [{', '.join(entry['tags'])}]",
        f"notebook: /assets/notebooks/{entry['slug']}.ipynb",
        f"gist: {GIST_URL}/{entry['id']}",
        f"gist_updated: {gist['updated_at']}",
        "related_posts: false",
        "---",
    ])


def convert_notebook(entry, gist, text):
    """Return (post markdown, Figures) for the notebook JSON in `text`."""
    nb = json.loads(text)
    figures = Figures(entry["slug"])
    blocks = []
    for index, cell in enumerate(nb.get("cells", [])):
        kind = cell.get("cell_type")
        if kind == "markdown":
            block = convert_markdown(cell.get("source", ""), first=(index == 0))
            if block:
                blocks.append(block)
        elif kind == "code":
            source = join(cell.get("source", "")).strip("\n")
            if not source.strip():
                continue
            blocks.append(fence(source, "python"))
            blocks.extend(convert_outputs(cell.get("outputs", []), figures))
    body = "\n\n".join(blocks)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return front_matter(entry, gist) + "\n\n" + body.strip("\n") + "\n", figures


# ----------------------------------------------------------------------------


def existing_updated_at(post_path):
    if not post_path.exists():
        return None
    match = re.search(r"^gist_updated:\s*(\S+)", post_path.read_text(), re.M)
    return match.group(1) if match else None


def process(entry, args, token):
    slug = entry["slug"]
    post_path = POSTS / f"{entry['date']}-{slug}.md"
    try:
        gist, filename, text = fetch_gist(entry["id"], token)
    except (urllib.error.URLError, ValueError, KeyError) as err:
        print(f"{slug}: failed ({err})", file=sys.stderr)
        return False

    previous = existing_updated_at(post_path)
    if previous == gist["updated_at"] and not args.force:
        print(f"{slug}: unchanged")
        return True

    post, figures = convert_notebook(entry, gist, text)
    action = "updated" if post_path.exists() else "created"
    writes = {
        post_path: post.encode("utf-8"),
        NOTEBOOKS / f"{slug}.ipynb": text.encode("utf-8"),
        **figures.files,
    }
    if args.dry_run:
        print(f"{slug}: would be {action} from {filename} "
              f"({figures.count} figures, {len(post.splitlines())} lines)")
        for path in writes:
            print(f"    {path.relative_to(ROOT)}")
        return True

    # Remove stale figures from an earlier conversion before writing new ones.
    if figures.dir.exists():
        for old in figures.dir.glob("output_*.png"):
            if old not in figures.files:
                old.unlink()
    for path, data in writes.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    print(f"{slug}: {action} ({figures.count} figures)")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--dry-run", action="store_true", help="report what would be written, write nothing")
    parser.add_argument("--only", metavar="SLUG", help="process only the entry with this slug")
    parser.add_argument("--force", action="store_true", help="rewrite posts even when the gist is unchanged")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    entries = parse_gists()
    if args.only and args.only not in {e["slug"] for e in entries}:
        sys.exit(f"no entry with slug {args.only!r} in {SOURCE.relative_to(ROOT)}")

    ok = True
    for entry in entries:
        if args.only and entry["slug"] != args.only:
            print(f"{entry['slug']}: skipped (--only)")
            continue
        ok &= process(entry, args, token)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
