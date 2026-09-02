#!/usr/bin/env python3
"""Create publication thumbnails from the first figure of each paper's arXiv source.

Runs after update_publications.py in .github/workflows/update-publications.yml;
can also be run by hand from the repository root:

    python3 bin/update_previews.py            # fetch figures for entries lacking a preview
    python3 bin/update_previews.py --dry-run  # only list which entries would be processed

Rules, so that manual choices are never clobbered:
  * Only entries in _bibliography/papers.bib with NO "preview" field are touched.
    To replace an automatic thumbnail, overwrite the PNG in
    assets/img/publication_preview/ or point "preview" at another file.
    To have no thumbnail at all, set  preview = {none}.
  * An image file that already exists is never overwritten.
  * To redo one paper, delete its "preview" line and its PNG, then run again.

How a figure is chosen: the arXiv e-print (LaTeX source) is unpacked, \\input
files are expanded, and the first \\includegraphics (or AASTeX \\plotone /
\\plottwo) inside the first figure environment is taken.  PDF/EPS figures are
rasterised with Ghostscript; the result is resized to at most MAX_SIZE px with
ImageMagick (or sips on macOS).  Papers whose source has no usable figure are
reported and left without a preview; they will be retried on the next run.
"""

import argparse
import gzip
import io
import pathlib
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from update_publications import BIB, ROOT, parse_bib, rel  # noqa: E402

PREVIEW_DIR = ROOT / "assets" / "img" / "publication_preview"
USER_AGENT = "maxisi.github.io preview updater (https://github.com/maxisi/maxisi.github.io)"
ARXIV_DELAY = 3.0  # seconds between arXiv requests, per arXiv's usage policy
MAX_SIZE = 1000  # px, longest side
NO_PREVIEW = "none"  # preview = {none} opts an entry out

FIGURE_RE = re.compile(r"\\begin\{figure\*?\}(.*?)\\end\{figure\*?\}", re.S)
GRAPHICS_RE = re.compile(r"\\(?:includegraphics\*?\s*(?:\[[^\]]*\])?|plotone|plottwo)\s*\{([^}]+)\}")
GRAPHICSPATH_RE = re.compile(r"\\graphicspath\s*\{((?:\s*\{[^}]*\}\s*)+)\}")
INPUT_RE = re.compile(r"\\(?:input|include)\s*\{([^}]+)\}")
COMMENT_RE = re.compile(r"(?<!\\)%.*")
VECTOR = {".pdf", ".eps", ".ps"}
RASTER = {".png", ".jpg", ".jpeg"}
EXTENSIONS = ["", ".pdf", ".png", ".jpg", ".jpeg", ".eps", ".ps", ".PDF", ".PNG", ".JPG", ".JPEG", ".EPS"]


def safe_name(key):
    return re.sub(r"[^A-Za-z0-9]+", "-", key).strip("-") + ".png"


def fetch_eprint(arxiv_id):
    request = urllib.request.Request(f"https://arxiv.org/e-print/{arxiv_id}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def unpack(data, workdir):
    """Unpack an arXiv e-print into workdir. Returns False for PDF-only submissions."""
    if data[:2] == b"\x1f\x8b":
        data = gzip.decompress(data)
    if data.startswith(b"%PDF"):
        return False
    stream = io.BytesIO(data)
    if tarfile.is_tarfile(stream):
        stream.seek(0)
        with tarfile.open(fileobj=stream) as tar:
            for member in tar.getmembers():
                target = (workdir / member.name).resolve()
                if member.isfile() and workdir in target.parents:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(tar.extractfile(member).read())
    else:
        (workdir / "main.tex").write_bytes(data)
    return True


def read_tex(path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    return COMMENT_RE.sub("", text)


def find_main_tex(workdir):
    candidates = [p for p in workdir.rglob("*.tex") if "\\documentclass" in read_tex(p)]
    with_document = [p for p in candidates if "\\begin{document}" in read_tex(p)]
    pool = with_document or candidates
    return min(pool, key=lambda p: len(p.parts)) if pool else None


def expand_inputs(path, seen=None):
    """Return the tex text with \\input/\\include files spliced in, in document order."""
    seen = seen if seen is not None else set()
    if path in seen or not path.is_file():
        return ""
    seen.add(path)
    text = read_tex(path)

    def splice(match):
        name = match.group(1).strip().strip('"')
        for candidate in (path.parent / name, path.parent / (name + ".tex")):
            if candidate.is_file():
                return expand_inputs(candidate, seen)
        return ""

    return INPUT_RE.sub(splice, text)


def resolve_graphic(workdir, texdir, graphicspaths, name):
    name = name.strip().strip('"')
    dirs = [texdir, workdir] + [texdir / g for g in graphicspaths] + [workdir / g for g in graphicspaths]
    for directory in dirs:
        for ext in EXTENSIONS:
            candidate = directory / (name + ext)
            if candidate.is_file():
                return candidate
    stem = pathlib.Path(name).name.lower()
    for candidate in workdir.rglob("*"):
        if candidate.is_file() and candidate.name.lower() in {stem + e.lower() for e in EXTENSIONS}:
            return candidate
    return None


def first_figure(workdir):
    main = find_main_tex(workdir)
    if main is None:
        return None, "no LaTeX source"
    text = expand_inputs(main)
    graphicspaths = []
    for match in GRAPHICSPATH_RE.finditer(text):
        graphicspaths += re.findall(r"\{([^}]*)\}", match.group(1))
    for figure in FIGURE_RE.finditer(text):
        for graphic in GRAPHICS_RE.findall(figure.group(1)):
            path = resolve_graphic(workdir, main.parent, graphicspaths, graphic)
            if path is not None and path.suffix.lower() in VECTOR | RASTER:
                return path, None
    return None, "no includegraphics inside a figure environment"


def have(tool):
    return shutil.which(tool) is not None


def to_png(src, dst):
    """Rasterise/copy src to dst as PNG, flattened onto white and resized to MAX_SIZE."""
    suffix = src.suffix.lower()
    if suffix in VECTOR:
        subprocess.run(
            ["gs", "-q", "-dNOPAUSE", "-dBATCH", "-dSAFER", "-sDEVICE=png16m", "-r200",
             "-dFirstPage=1", "-dLastPage=1", "-dEPSCrop", "-dUseCropBox",
             f"-sOutputFile={dst}", str(src)],
            check=True, capture_output=True, timeout=300,
        )
    else:
        shutil.copyfile(src, dst)
    geometry = f"{MAX_SIZE}x{MAX_SIZE}>"
    if have("magick"):
        subprocess.run(["magick", str(dst), "-background", "white", "-alpha", "remove", "-alpha", "off",
                        "-resize", geometry, str(dst)], check=True, capture_output=True, timeout=300)
    elif have("convert"):
        subprocess.run(["convert", str(dst), "-background", "white", "-alpha", "remove", "-alpha", "off",
                        "-resize", geometry, str(dst)], check=True, capture_output=True, timeout=300)
    elif have("sips"):
        subprocess.run(["sips", "-s", "format", "png", "--resampleHeightWidthMax", str(MAX_SIZE), str(dst)],
                       check=True, capture_output=True, timeout=300)


def make_preview(arxiv_id, target):
    """Fetch the e-print and write the first figure to target. Returns an error string or None."""
    data = fetch_eprint(arxiv_id)
    with tempfile.TemporaryDirectory() as tmp:
        workdir = pathlib.Path(tmp).resolve()
        if not unpack(data, workdir):
            return "PDF-only submission"
        figure, error = first_figure(workdir)
        if figure is None:
            return error
        try:
            to_png(figure, target)
        except subprocess.CalledProcessError as exc:
            target.unlink(missing_ok=True)
            return f"conversion of {figure.name} failed: {exc.stderr.decode(errors='ignore').strip()[:200]}"
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="list candidates without fetching or writing")
    args = parser.parse_args()

    if not args.dry_run and not have("gs"):
        sys.exit("error: ghostscript (gs) is required to rasterise figures")

    text = BIB.read_text()
    entries, gaps = parse_bib(text)
    todo = [e for e in entries if e.get("preview") is None]
    print(f"{len(entries)} entries, {len(todo)} without a preview")

    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    n_done = 0
    for i, entry in enumerate(todo):
        arxiv_id = entry.get("arxiv") or entry.get("eprint")
        if not arxiv_id:
            print(f"  {entry.key}: no arXiv id, skipped")
            continue
        name = safe_name(entry.key)
        target = PREVIEW_DIR / name
        if args.dry_run:
            print(f"  {entry.key}: would use arXiv:{arxiv_id} -> {name}" + (" (file exists)" if target.exists() else ""))
            continue
        if not target.exists():
            if n_done:
                time.sleep(ARXIV_DELAY)
            try:
                error = make_preview(arxiv_id, target)
            except Exception as exc:  # noqa: BLE001 -- one bad paper must not stop the rest
                error = f"{type(exc).__name__}: {exc}"
            if error:
                print(f"  {entry.key}: arXiv:{arxiv_id}: {error}")
                continue
        entry.set("preview", name)
        n_done += 1
        print(f"  {entry.key}: preview = {name}")

    out = "".join(g + e.text for g, e in zip(gaps, entries)) + gaps[-1]
    if out != text and not args.dry_run:
        BIB.write_text(out)
        print(f"{rel(BIB)}: written")
    print(f"{n_done} previews added")


if __name__ == "__main__":
    main()
