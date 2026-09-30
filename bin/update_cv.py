#!/usr/bin/env python3
"""Refresh the downloadable CV (assets/pdf/maxisi_cv.pdf) and its date stamp.

The CV is maintained as LaTeX in the private maxisi/cv repository, whose
GitHub Actions workflow compiles it and force-pushes the PDF to a "<branch>-pdf"
branch.  This script copies the latest PDF into the site and records its date
in the `cv_pdf_updated` front-matter field of _pages/cv.md:

    python3 bin/update_cv.py                 # from ~/src/cv/maxisi_cv.pdf (local build)
    python3 bin/update_cv.py --github        # from the master-pdf branch via the gh CLI
    python3 bin/update_cv.py --source PATH   # from any PDF

The text of the CV page (_data/cv.yml) is not generated: edit it by hand when
maxisi_cv.tex changes.  Only the standard library is used (plus `gh` for --github).
"""

import argparse
import datetime as dt
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "assets" / "pdf" / "maxisi_cv.pdf"
PAGE = ROOT / "_pages" / "cv.md"
DEFAULT_SOURCE = Path(os.environ.get("CV_SOURCE", Path.home() / "src" / "cv" / "maxisi_cv.pdf"))
GITHUB_REPO = "maxisi/cv"
GITHUB_BRANCH = "master-pdf"


def rel(path):
    try:
        return str(Path(path).relative_to(ROOT))
    except ValueError:
        return str(path)


def fetch_github(dest):
    """Download maxisi_cv.pdf from the PDF branch of the CV repo with `gh`."""
    cmd = ["gh", "api", f"repos/{GITHUB_REPO}/contents/maxisi_cv.pdf?ref={GITHUB_BRANCH}",
           "-H", "Accept: application/vnd.github.raw+json"]
    with open(dest, "wb") as f:
        proc = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        sys.exit(f"error: could not fetch the PDF from {GITHUB_REPO}@{GITHUB_BRANCH}: "
                 f"{proc.stderr.decode().strip()}")
    return dt.date.today()


def stamp(date, dry_run):
    text = PAGE.read_text()
    line = f"cv_pdf_updated: {date.isoformat()}"
    new_text, n = re.subn(r"^cv_pdf_updated: .*$", line, text, count=1, flags=re.M)
    if n == 0:
        new_text = text.replace("\ntoc:", f"\n{line}\ntoc:", 1)
    if new_text != text and not dry_run:
        PAGE.write_text(new_text)
    return new_text != text


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE,
                        help=f"PDF to copy (default: {DEFAULT_SOURCE})")
    parser.add_argument("--github", action="store_true",
                        help=f"fetch the PDF from the {GITHUB_BRANCH} branch of {GITHUB_REPO} instead")
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    args = parser.parse_args()

    if args.github:
        tmp = Path(tempfile.mkstemp(suffix=".pdf")[1])
        date = fetch_github(tmp)
        source = tmp
    else:
        source = args.source
        if not source.is_file():
            sys.exit(f"error: {source} not found (build the CV with `make` in its repository first)")
        date = dt.date.fromtimestamp(source.stat().st_mtime)

    if source.stat().st_size < 10_000 or source.read_bytes()[:5] != b"%PDF-":
        sys.exit(f"error: {source} does not look like a PDF")

    changed = not TARGET.is_file() or TARGET.read_bytes() != source.read_bytes()
    if changed and not args.dry_run:
        TARGET.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, TARGET)
    stamped = stamp(date, args.dry_run) if changed else False

    prefix = "would update" if args.dry_run else "updated"
    if changed:
        print(f"{rel(TARGET)}: {prefix} ({source.stat().st_size // 1024} kB, dated {date})")
        if stamped:
            print(f"{rel(PAGE)}: {prefix} cv_pdf_updated")
    else:
        print(f"{rel(TARGET)}: unchanged")
    if args.github:
        source.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
