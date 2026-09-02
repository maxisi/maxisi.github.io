#!/usr/bin/env python3
"""Sync _bibliography/papers.bib with INSPIRE-HEP.

Runs on a schedule from .github/workflows/update-publications.yml; can also be
run by hand from the repository root:

    python3 bin/update_publications.py            # apply changes
    python3 bin/update_publications.py --dry-run  # only report what would change

What it does
  * Fetches the BibTeX for every INSPIRE record matching QUERY.
  * Matches each local entry to an INSPIRE record by texkey, then by arXiv
    eprint, then by DOI (so entries whose keys were edited by hand still match).
  * Existing entries: refreshes publication details (journal, volume, number,
    pages, doi, year, ...; see SYNC_FIELDS).  Hand-edited fields such as
    author, title, preview, selected and abbr are never overwritten, and no
    local field is ever removed.  Everything else in the file is preserved
    byte for byte.
  * New records: appended at the top of the file (the file is newest-first)
    with the al-folio extras this site uses (bibtex_show, arxiv, abbr, html).
    Mentee asterisks and preview images still need to be added by hand.
  * Rewrites the "years:" list in _pages/publications.md from the entries.

Only the standard library is used.
"""

import argparse
import pathlib
import re
import sys
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
BIB = ROOT / "_bibliography" / "papers.bib"
PAGE = ROOT / "_pages" / "publications.md"

# Same author identifier and non-collaboration query as update_inspire_stats.py.
AUTHOR = "Maximiliano.Isi.1"
QUERY = f"a {AUTHOR} - abbott - abac"
API = "https://inspirehep.net/api/literature"
USER_AGENT = "maxisi.github.io publication updater (https://github.com/maxisi/maxisi.github.io)"

# INSPIRE entry types that should not be listed as publications.
SKIP_TYPES = {"phdthesis", "mastersthesis"}

# Fields copied from INSPIRE onto existing entries whenever INSPIRE has a value.
SYNC_FIELDS = [
    "journal", "volume", "number", "pages", "doi", "year", "month",
    "booktitle", "reportnumber", "eprint", "archiveprefix", "primaryclass",
]

# Journal name -> venue badge, for venues already used in the bibliography.
ABBR = {
    "Phys. Rev. D": "PRD",
    "Phys. Rev. Lett.": "PRL",
    "Phys. Rev. X": "PRX",
    "Astrophys. J.": "ApJ",
    "Astrophys. J. Lett.": "ApJL",
    "Mon. Not. Roy. Astron. Soc.": "MNRAS",
    "Gen. Rel. Grav.": "GRG",
    "Am. J. Phys.": "AJP",
    "Class. Quant. Grav.": "CQG",
    "Mod. Phys. Lett. A": "MPLA",
    "JHEP": "JHEP",
}

HEADER_RE = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,")
NAME_RE = re.compile(r"([\w\-]+)\s*=\s*")


def rel(path):
    """Path relative to the repository root, for messages."""
    try:
        return path.relative_to(ROOT)
    except ValueError:
        return path


class Entry:
    """One BibTeX entry: its text plus the location of every field value."""

    def __init__(self, kind, key, text):
        self.kind = kind.lower()
        self.key = key
        self.text = text
        self.fields = {}   # lowercase name -> value (without delimiters)
        self.names = {}    # lowercase name -> name as written
        self.spans = {}    # lowercase name -> (value_start, value_end) incl. delimiters
        self._parse()

    def _parse(self):
        text = self.text
        header = HEADER_RE.match(text)
        i = header.end()
        last_end = i
        while True:
            while i < len(text) and text[i] in " \t\r\n,":
                i += 1
            if i >= len(text):
                raise ValueError(f"{self.key}: unterminated entry")
            if text[i] == "}":
                self.close = i
                break
            m = NAME_RE.match(text, i)
            if not m:
                raise ValueError(f"{self.key}: cannot parse near {text[i:i + 30]!r}")
            name = m.group(1)
            j = m.end()
            if text[j] == '"':
                k, depth = j + 1, 0
                while k < len(text):
                    c = text[k]
                    if c == "{":
                        depth += 1
                    elif c == "}":
                        depth -= 1
                    elif c == '"' and depth == 0:
                        break
                    k += 1
                value, end = text[j + 1:k], k + 1
            elif text[j] == "{":
                k, depth = j, 0
                while k < len(text):
                    if text[k] == "{":
                        depth += 1
                    elif text[k] == "}":
                        depth -= 1
                        if depth == 0:
                            break
                    k += 1
                value, end = text[j + 1:k], k + 1
            else:
                k = j
                while k < len(text) and text[k] not in ",}\n":
                    k += 1
                value, end = text[j:k].strip(), k
            if k >= len(text):
                raise ValueError(f"{self.key}: unterminated value for {name}")
            low = name.lower()
            self.fields[low] = value
            self.names[low] = name
            self.spans[low] = (j, end)
            i = last_end = end
        self.last_end = last_end

    def get(self, name):
        return self.fields.get(name.lower())

    def set(self, name, value):
        """Replace an existing field's value (keeping its delimiters) or append a new field."""
        low = name.lower()
        if low in self.spans:
            start, end = self.spans[low]
            delim = self.text[start]
            new = ("{" + value + "}") if delim == "{" else ('"' + value + '"')
            self.text = self.text[:start] + new + self.text[end:]
        else:
            indent_match = re.search(r"\n([ \t]*)[\w\-]+\s*=", self.text)
            indent = indent_match.group(1) if indent_match else "    "
            quoted = ("{" + value + "}") if '"' in value else ('"' + value + '"')
            head = self.text[:self.last_end]
            tail = self.text[self.last_end:self.close]  # e.g. "\n" or ",\n"
            trailing_comma = "," in tail
            rest = tail.replace(",", "", 1).rstrip(" \t") or "\n"
            field = f"\n{indent}{name} = {quoted}" + ("," if trailing_comma else "")
            self.text = head + "," + field + rest + self.text[self.close:]
        self._parse()


def parse_bib(text):
    """Return (entries, gaps): the entries and the text between/around them."""
    entries, gaps, pos = [], [], 0
    for m in HEADER_RE.finditer(text):
        if m.start() < pos:
            continue
        i, depth = m.start(), 0
        while i < len(text):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        if i >= len(text):
            raise ValueError(f"unterminated entry {m.group(2)}")
        gaps.append(text[pos:m.start()])
        entries.append(Entry(m.group(1), m.group(2), text[m.start():i + 1]))
        pos = i + 1
    gaps.append(text[pos:])
    return entries, gaps


def fetch_inspire():
    entries, page = [], 1
    while True:
        params = urllib.parse.urlencode({"q": QUERY, "size": 250, "page": page, "format": "bibtex"})
        request = urllib.request.Request(f"{API}?{params}", headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=120) as response:
            chunk, _ = parse_bib(response.read().decode("utf-8"))
        entries += chunk
        if len(chunk) < 250:
            return entries
        page += 1


def index(entries):
    by_key, by_eprint, by_doi = {}, {}, {}
    for e in entries:
        by_key[e.key] = e
        for f in ("eprint", "arxiv"):
            if e.get(f):
                by_eprint.setdefault(e.get(f), e)
        if e.get("doi"):
            by_doi.setdefault(e.get("doi").lower(), e)
    return by_key, by_eprint, by_doi


def match(local, by_key, by_eprint, by_doi):
    if local.key in by_key:
        return by_key[local.key]
    for f in ("eprint", "arxiv"):
        if local.get(f) in by_eprint:
            return by_eprint[local.get(f)]
    if local.get("doi") and local.get("doi").lower() in by_doi:
        return by_doi[local.get("doi").lower()]
    return None


def add_derived(entry, changes):
    """Add al-folio helper fields that follow from the bibliographic data."""
    if entry.get("eprint") and not entry.get("arxiv"):
        entry.set("arxiv", entry.get("eprint"))
        changes.append(f"+arxiv={entry.get('eprint')}")
    if entry.get("doi") and not entry.get("html"):
        entry.set("html", "https://doi.org/" + entry.get("doi"))
        changes.append("+html")
    abbr = ABBR.get(entry.get("journal") or "")
    if abbr and not entry.get("abbr"):
        entry.set("abbr", abbr)
        changes.append(f"+abbr={abbr}")


def update_existing(local, remote):
    changes = []
    for f in SYNC_FIELDS:
        value = remote.get(f)
        if value is None or local.get(f) == value:
            continue
        name = local.names.get(f, remote.names[f])
        old = local.get(f)
        local.set(name, value)
        changes.append(f"{name}: {old!r} -> {value!r}" if old is not None else f"+{name}={value!r}")
    add_derived(local, changes)
    return changes


def new_entry(remote):
    header_end = HEADER_RE.match(remote.text).end()
    extras = "\n    bibtex_show = {true},"
    if remote.get("eprint"):
        extras += f'\n    arxiv = "{remote.get("eprint")}",'
    entry = Entry(remote.kind, remote.key, remote.text[:header_end] + extras + remote.text[header_end:])
    add_derived(entry, [])
    return entry


def update_years(entries, dry_run):
    years = sorted({int(e.get("year")) for e in entries if (e.get("year") or "").isdigit()}, reverse=True)
    line = "years: [" + ", ".join(map(str, years)) + "]"
    text = PAGE.read_text()
    new_text, n = re.subn(r"^years: \[.*\]$", line, text, count=1, flags=re.M)
    if n != 1:
        sys.exit(f"error: no 'years:' line found in {PAGE}")
    if new_text != text:
        print(f"{rel(PAGE)}: {line}")
        if not dry_run:
            PAGE.write_text(new_text)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="report changes without writing")
    args = parser.parse_args()

    text = BIB.read_text()
    local, gaps = parse_bib(text)
    try:
        remote = fetch_inspire()
    except Exception as error:  # noqa: BLE001 -- report and fail loudly
        sys.exit(f"error: could not fetch INSPIRE records: {error}")
    print(f"{len(local)} local entries, {len(remote)} INSPIRE records")

    by_key, by_eprint, by_doi = index(remote)
    matched = set()
    n_changed = 0
    for entry in local:
        r = match(entry, by_key, by_eprint, by_doi)
        if r is None:
            print(f"  {entry.key}: not found on INSPIRE, left untouched")
            continue
        matched.add(r.key)
        changes = update_existing(entry, r)
        if changes:
            n_changed += 1
            print(f"  {entry.key}: " + "; ".join(changes))

    added = []
    for r in remote:
        if r.key in matched:
            continue
        if r.kind in SKIP_TYPES:
            print(f"  {r.key}: skipped ({r.kind})")
            continue
        added.append(new_entry(r))
        print(f"  {r.key}: NEW {r.get('title')}")

    out = "".join(a.text + "\n\n" for a in added)
    for gap, entry in zip(gaps, local):
        out += gap + entry.text
    out += gaps[-1]

    check, _ = parse_bib(out)
    keys = [e.key for e in check]
    if len(check) != len(local) + len(added) or len(set(keys)) != len(keys):
        sys.exit("error: internal consistency check failed; nothing written")

    print(f"{n_changed} entries updated, {len(added)} added")
    if out != text and not args.dry_run:
        BIB.write_text(out)
        print(f"{rel(BIB)}: written")
    update_years(check, args.dry_run)


if __name__ == "__main__":
    main()
