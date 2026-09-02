#!/usr/bin/env python3
"""Fetch GitHub repository metadata and write _data/github_repos.yml.

The cards on the software page (_pages/repositories.md) used to be images
served by the public github-readme-stats instance; that service goes down
regularly, taking every card with it.  The cards are now rendered by
_includes/repository/repo.html from the data written here, so the page only
depends on this repository.

Which repositories are shown is set in _data/repositories.yml; this script
fills in their details.  It is run on a schedule by
.github/workflows/update-publications.yml, but can also be run by hand from the
repository root:

    python3 bin/update_repos.py

Only the standard library is used.  Set GITHUB_TOKEN to raise the API rate
limit (the workflow does).  The output file is left untouched when nothing has
changed, so that the "updated" date reflects the last change rather than the
last run.  A repository that cannot be fetched keeps its previous entry, so a
transient API failure never blanks the page.
"""

import datetime
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE = ROOT / "_data" / "repositories.yml"
OUTPUT = ROOT / "_data" / "github_repos.yml"
API = "https://api.github.com/repos"
USER_AGENT = "maxisi.github.io repo updater (https://github.com/maxisi/maxisi.github.io)"

# GitHub's language colours (github.com/github-linguist/linguist); anything not
# listed falls back to GREY, which only costs the little dot its colour.
LANGUAGE_COLORS = {
    "C": "#555555",
    "C++": "#f34b7d",
    "CMake": "#DA3434",
    "CSS": "#563d7c",
    "Cuda": "#3A4E3A",
    "Dockerfile": "#384d54",
    "Fortran": "#4d41b1",
    "Go": "#00ADD8",
    "HTML": "#e34c26",
    "Java": "#b07219",
    "JavaScript": "#f1e05a",
    "Julia": "#a270ba",
    "Jupyter Notebook": "#DA5B0B",
    "MATLAB": "#e16737",
    "Makefile": "#427819",
    "Mathematica": "#dd1100",
    "Perl": "#0298c3",
    "Python": "#3572A5",
    "R": "#198CE7",
    "Ruby": "#701516",
    "Rust": "#dea584",
    "Shell": "#89e051",
    "Swift": "#F05138",
    "TeX": "#3D6117",
    "TypeScript": "#3178c6",
}
GREY = "#959da5"


def wanted_repos():
    """Return the "owner/name" entries under github_repos: in _data/repositories.yml."""
    repos, in_list = [], False
    for line in SOURCE.read_text().splitlines():
        if re.match(r"^\s*#", line) or not line.strip():
            continue
        if re.match(r"^github_repos:\s*$", line):
            in_list = True
            continue
        item = re.match(r"^\s+-\s*(\S+)\s*$", line)
        if in_list and item:
            repos.append(item.group(1).strip("\"'"))
        elif not line.startswith((" ", "\t", "-")):
            in_list = False
    return repos


def fetch(full_name):
    """Return the GitHub API record for "owner/name"."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(f"{API}/{full_name}", headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def short(n):
    """Format 1234 -> '1.2k', 39 -> '39'."""
    if n >= 10_000:
        return f"{round(n / 1000)}k"
    if n >= 1_000:
        return f"{n / 1000:.1f}k"
    return str(n)


def entry(full_name, data):
    owner, _, name = full_name.partition("/")
    language = data.get("language")
    return {
        "name": full_name,
        "owner": owner,
        "repo": name,
        "description": (data.get("description") or "").strip(),
        "url": data.get("html_url") or f"https://github.com/{full_name}",
        "language": language or "",
        "language_color": LANGUAGE_COLORS.get(language, GREY) if language else "",
        "stars": int(data.get("stargazers_count", 0)),
        "stars_short": short(int(data.get("stargazers_count", 0))),
        "forks": int(data.get("forks_count", 0)),
        "forks_short": short(int(data.get("forks_count", 0))),
        "archived": bool(data.get("archived", False)),
    }


def previous():
    """Return the entries of the existing output file, keyed by name."""
    if not OUTPUT.exists():
        return {}
    entries, current = {}, None
    for line in OUTPUT.read_text().splitlines():
        item = re.match(r"^\s+-\s+name:\s*(.+)$", line)
        field = re.match(r"^\s+(\w+):\s*(.*)$", line)
        if item:
            current = json.loads(item.group(1))
            entries[current] = {"name": current}
        elif current and field:
            key, raw = field.group(1), field.group(2)
            try:
                entries[current][key] = json.loads(raw)
            except json.JSONDecodeError:
                entries[current][key] = raw
    return entries


def render(entries, updated):
    lines = [
        "# GitHub repository metadata for the software page.",
        "# Which repositories appear is set in _data/repositories.yml;",
        "# generated by bin/update_repos.py -- do not edit by hand.",
        f"updated: {updated}",
        "repos:",
    ]
    for e in entries:
        lines.append(f"  - name: {json.dumps(e['name'])}")
        for key in ("owner", "repo", "description", "url", "language", "language_color"):
            lines.append(f"    {key}: {json.dumps(e[key])}")
        for key in ("stars", "forks"):
            lines.append(f"    {key}: {e[key]}")
            lines.append(f"    {key}_short: {json.dumps(e[f'{key}_short'])}")
        lines.append(f"    archived: {str(e['archived']).lower()}")
    return "\n".join(lines) + "\n"


def strip_date(text):
    return "\n".join(line for line in text.splitlines() if not line.startswith("updated:"))


def main():
    names = wanted_repos()
    if not names:
        sys.exit(f"error: no repositories listed under github_repos: in {rel(SOURCE)}")

    old = previous()
    entries, failed = [], []
    for full_name in names:
        try:
            entries.append(entry(full_name, fetch(full_name)))
            e = entries[-1]
            print(f"{full_name:28s} {e['language'] or '-':16s} {e['stars']:5d} stars {e['forks']:5d} forks")
        except (urllib.error.URLError, OSError, ValueError, KeyError) as error:
            failed.append(f"{full_name}: {error}")
            if full_name in old:
                entries.append(old[full_name])
                print(f"{full_name:28s} could not be fetched; keeping previous entry")
            else:
                print(f"{full_name:28s} could not be fetched and has no previous entry; skipped")

    for message in failed:
        print(f"warning: {message}", file=sys.stderr)
    if not entries:
        sys.exit("error: no repository could be fetched")

    new = render(entries, datetime.date.today().isoformat())
    existing = OUTPUT.read_text() if OUTPUT.exists() else ""
    if strip_date(existing) == strip_date(new):
        print(f"{rel(OUTPUT)}: unchanged")
        return
    OUTPUT.write_text(new)
    print(f"{rel(OUTPUT)}: updated")


def rel(path):
    try:
        return str(path.relative_to(pathlib.Path.cwd()))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    main()
