# maxisi.github.io — Rework Plan: from postdoc page to group site

> **Status (2026-09-29):** implemented on branch `faculty-rework` (uncommitted working tree).
> Owner decisions that shaped the build:
> 1. Site title stays "Maximiliano Isi".
> 2. Both titles shown, Columbia first; office address from the Columbia faculty page, Columbia email from the CV.
> 3. Three research lines: black-hole ringdowns, black-hole populations, machine-learning and statistical methods.
>    One page (`/research/`) with anchors; home-page cards link to them. Bib entries tagged with `keywords`.
> 4. Roster in `_data/people.yml`: PI; postdocs Konstantin Leyde, Asad Hussain, Jack Heinzel, Simona Miller (Hubble Fellow, CUNY);
>    PhD students Abigail Moran, Ana Lam, Lauren Mendoza; undergraduates Tata Tirapongprasert, Sarah Yuh, Candice Wu, Nathaniel Rodgers.
>    Alumni list seeded from the mentee markers in the bibliography (details to fill in).
> 5. Teaching from the CV (`~/src/cv/maxisi_cv.tex`, Teaching section) in `_data/teaching.yml`.
> 6. Blog is called "Notes"; no comments.
> 7. Software list extended with `simonajmiller/tdinf` only.
>
> Local builds work with Homebrew `ruby@3.3` (see README). Still open: member photos and links, alumni details,
> news items, course URLs, and whether to add the notes importer to the weekly workflow.

Date: 2026-09-29. Repo: /Users/maxisi/src/maxisi.github.io (Jekyll, al-folio fork, deployed to GitHub Pages via `.github/workflows/deploy.yml` -> gh-pages branch).

## 1. Goals & audience

Turn the current single-person al-folio page into a faculty / group-leader site that communicates the scope of the research program while keeping the things that already work (INSPIRE-synced publications, self-hosted repo cards, dark mode, GitHub Pages deploy).

Audiences, in priority order:
1. Prospective students and postdocs (undergrad through postdoc): what the group works on, who is in it, how to join, what a first project looks like (the "Notes" tutorials serve this directly).
2. Collaborators and colleagues: research areas, papers, software, people to contact.
3. Funders, hiring/tenure committees, press: scale of the program (stats, alumni, selected papers, news), teaching record.

Non-goals: changing static-site stack, changing hosting, rewriting the publications pipeline, adding a CMS.

## 2. Assessment of the current site

### 2.1 What exists (theme baseline)
- al-folio circa v0.10 (July 2023 demo posts present; Bootstrap 4.x + MDB 4.20 + jQuery 3.6; `jekyll-jupyter-notebook`, `jekyll-scholar`, `jekyll-imagemagick`, `jekyll-archives`, `jekyll-paginate-v2`, `jekyll-minifier`, `jekyll-feed`, `jekyll-toc`, `jemoji`, etc.). CI builds with Ruby 3.2.2 (`deploy.yml`), then runs `purgecss`.
- August 2026 "theme-refresh" PR already modernised the CDN dependencies (SRI hashes, pinned versions, polyfill.io removed, mermaid removed, masonry disabled, Actions bumped).
- Nav today: about (/), publications (nav_order 1), software (/repositories/, nav_order 3), cv (nav_order 4). `max_width: 800px`, `navbar_fixed: true`, `footer_fixed: true`, dark mode on, MathJax on, progress bar on.

### 2.2 Owner customizations that MUST be preserved
Publications pipeline (weekly cron `17 6 * * 1` + `workflow_dispatch`, `.github/workflows/update-publications.yml`):
- `bin/update_inspire_stats.py` -> `_data/inspire_stats.yml` (h-index / publications / citations, "all" vs "noncollab" queries; author BAI `Maximiliano.Isi.1`).
- `bin/update_publications.py` -> merges INSPIRE BibTeX into `_bibliography/papers.bib` (matches by texkey, then eprint, then DOI; only `SYNC_FIELDS` are overwritten; hand-edited fields such as `author`, `title`, `preview`, `selected`, `abbr` are never touched; new entries prepended, file is newest-first). It also rewrites the line matching `^years: \[.*\]$` in `_pages/publications.md` — that line, that file path, and that format must survive the rework.
- `bin/update_previews.py` -> thumbnails from the first arXiv figure into `assets/img/publication_preview/<Key>.png`; convention `preview = {none}` opts out; existing PNGs never overwritten.
- `bin/update_repos.py` -> `_data/github_repos.yml` from the list in `_data/repositories.yml` (`github_repos:` list parsed by regex — keep that key and indentation style).
- The workflow's `git add` list: `_data/inspire_stats.yml _data/github_repos.yml _bibliography/papers.bib _pages/publications.md assets/img/publication_preview`. Any new generated file must be added there if it should be auto-committed.
- Templates/data: `_layouts/bib.html` (venue badge colours from `_data/venues.yml`; mentee marker convention `{First Last*}` in `author`; strips `*` when matching self/coauthors), `_includes/inspire_stats.html`, `_includes/selected_papers.html` (`selected={true}`; 5 entries today), `_data/venues.yml`, `_data/coauthors.yml` (currently al-folio demo content — Einstein et al. — safe to repurpose), `_config.yml` `scholar:` block, `filtered_bibtex_keywords`, `max_author_limit: 3`, `enable_publication_thumbnails: true`.

Repo cards: `_includes/repository/repo.html` (rewritten to render from `_data/github_repos.yml`), `.repo`/`.repo-card*` styles in `_sass/_base.scss` (lines ~461–545), `--global-text-color-muted` in `_sass/_themes.scss`, `_pages/repositories.md`, `_data/repositories.yml`.

Content: `_pages/about.md` (bio; subtitle says Assistant Professor, Dept. of Astronomy, Columbia + Associate Research Scientist, CCA/Flatiron — confirm wording), `_data/cv.yml`, `assets/img/prof_pic.jpg`, hand-picked preview images in `assets/img/publication_preview/*.png|gif` (~20 MB).

### 2.3 Boilerplate to delete (see Section 11 for the full list)
18 demo posts in `_posts/`, 6 demo projects in `_projects/`, 3 demo news items in `_news/`, demo `_data/coauthors.yml` content, demo assets (`assets/img/1..12.jpg`, screenshots, `assets/audio`, `assets/video`, `assets/pdf/example_pdf.pdf`, `assets/plotly/demo.html`, `assets/jupyter/blog.ipynb`, `assets/bibliography/2018-12-22-distill.bib`, `assets/json/*`), upstream-only CI (`deploy-image.yml`, `deploy-docker-tag.yml`, `docker-slim.yml`, `.github/stale.yml`, `.github/release.yml`, `.github/ISSUE_TEMPLATE/`), `.all-contributorsrc`, `CONTRIBUTING.md`, `reports/*.svg`, and the `external_sources:` block in `_config.yml`, which makes `_plugins/external-posts.rb` fetch `https://medium.com/@al-folio/feed` on every build.

### 2.4 Theme-upgrade recommendation
- Upstream al-folio: last Bootstrap-era release v0.16.3 (Jan 2024); v1.0 (Jun 2024) moved to a "thin starter + plugin gems" architecture with a Tailwind runtime; v1.2 (Aug 2024) is the latest shown. Bootstrap markup is only supported behind a compat plugin slated for removal.
- Options: (a) stay on the current fork and restyle in place; (b) rebase onto v0.16.3 (gains jekyll-socials, teaching course-schedule widget, RenderCV support; costs a conflict-heavy merge against the custom `bib.html`, `repo.html`, SCSS, and lands on a dead branch); (c) migrate to v1.x (re-implement bib layout, repo cards, and every custom style as plugin overrides on Tailwind — effectively a new site); (d) switch stack (Hugo/Astro) — loses jekyll-scholar, so the publications pipeline would need a new renderer.
- Recommendation: (a). The publications pipeline and repo cards are already bespoke; the security refresh is done; everything this plan needs (data-driven pages, grids, new layouts) is plain Liquid + SCSS on Bootstrap 4. Cherry-pick individual upstream fixes if ever needed.

## 3. Reference-site analysis

### 3.1 kchatziioannou.github.io (HTML5 UP static template, not Jekyll — borrow structure, not code)
Nav: Welcome, About Me, Research Interests, Research Group, Blog, Teaching, Contact. Home is a single long page: hero (name, "Professor of Physics at Caltech", "William H. Hurt Scholar", portrait) -> About -> Research Interests (card/thumbnail per area with "Learn more" links; collaborations list: LIGO, LISA, NANOGrav, ...) -> Research Group blurb + recruiting -> Blog -> Teaching -> Contact (email, office, phone, address).
- /Interests.html: eight areas, each a clickable thumbnail + heading linking to its own page (e.g. "GW250114 and the nature of black holes", "Testing General Relativity", "Populations of compact objects"). Areas are first-class, image-led objects.
- /Group.html: "Join" text first (subsections for undergrads/SURF, PhD applicants, postdoc fellowships), then a table of current members (name, position, years "2023–Present", link) and a "Former group members" table with tenure ranges. No photos.
- /Teaching.html: heading "Classes Taught at Caltech" + a three-item list of course code/title. No terms, no links.

What makes it read as a group site: (1) research areas as visual, named programme lines rather than a paragraph of interests; (2) an explicit roster with alumni and a how-to-join section; (3) a teaching record; (4) institutional titles/honours in the hero; (5) contact block. Where we can do better: photos and blurbs for members, links between areas <-> people <-> papers, live publication stats, software.

### 3.2 dfm.io/posts
Minimal reverse-chronological list: "Mon D YYYY" date + title, no excerpts, tags or read-time chips, no pagination. Posts converted from notebooks: title, date, a "The source for this post can be found here" link to the notebook in GitHub, code cells with syntax highlighting, outputs directly under cells, figures as PNGs, LaTeX math inline. Takeaway: convert notebooks to native Markdown posts (not iframes), keep one "source notebook" link, keep the list dead simple.

## 4. Proposed information architecture

Nav (left to right): Home · Research · Group · Publications · Teaching · Notes · Software · CV. News lives on Home and at /news/ (not in nav). Contact/join info on Group page and footer.

| Route | File | Layout | Data source | Owner must supply |
|---|---|---|---|---|
| / | `_pages/about.md` (keep path; permalink `/`) | new `_layouts/home.html` | `_config.yml`, `site.research`, `_data/people.yml`, bib `selected`, `_news`, latest posts | hero tagline (1 sentence), 2-paragraph bio, updated portrait, 3–5 research area names |
| /research/ | `_pages/research.md` | `page` + `_includes/research_grid.html` | `_research/*.md` collection | per area: title, 1–3 paragraphs, hero image, bib keywords, members |
| /research/<slug>/ | `_research/<slug>.md` | new `_layouts/research.html` | front matter + `{% bibliography -q @*[keywords^=<kw>]* %}` + people | same |
| /group/ | `_pages/group.md` | new `_layouts/group.html` (or `page` + includes) | `_data/people.yml`, `_data/collaborators.yml` | roster (names, roles, years, links, photos), alumni with "now at", collaborator list, join text |
| /publications/ | `_pages/publications.md` (unchanged path) | `page` | bib + `_data/inspire_stats.yml` | nothing (optional: `keywords` tags on entries) |
| /teaching/ | `_pages/teaching.md` | `page` + `_includes/teaching.html` | `_data/teaching.yml` | course list with terms, links |
| /notes/ | `notes/index.html` (renamed from `blog/`) | `default` | `_posts` | approve titles/tags for 11 gists |
| /notes/<year>/<slug>/ | `_posts/*.md` | `post` | generated by `bin/import_gists.py` | — |
| /software/ | `_pages/repositories.md` (permalink changed; stub redirect at /repositories/) | `page` | `_data/github_repos.yml` | extra repos to list |
| /news/ | `news.html` | `page` | `_news/*.md` | news items (papers, awards, arrivals, talks) |
| /cv/ | `_pages/cv.md` | `cv` | `_data/cv.yml` | updated entries; optional PDF |

Home page section order (mirrors the reference): hero -> research area cards -> group strip (avatars + "Meet the group" / "Join us") -> selected publications (existing include) -> news (existing include, limit 5) -> latest notes (existing `latest_posts.html`, limit 3) -> contact/social.

## 5. Design direction (al-folio-compatible)
- Width: keep prose at 800px but allow wide sections. Add `$max-content-width-wide: 1100px` in `_sass/_variables.scss` and a `.container-wide` class used by `home.html`, `group.html`, `research.md`; `_layouts/default.html` keeps `.container` for everything else.
- Typography: replace the Roboto/Roboto Slab Google Fonts link in `_includes/head.html` with a system-ui body stack + one self-hosted display face for h1/h2 (e.g. Source Serif 4 or Fraunces; put woff2 in `assets/webfonts/`). Set sizes in `_sass/_base.scss`; hero h1 ~2.6rem desktop / 1.9rem mobile.
- Colour: one accent per mode via existing CSS variables (`--global-theme-color`); suggest deep indigo (#2b3a8f-ish) light / desaturated cyan dark, checked against WCAG AA on both backgrounds. Keep venue badge colours in `_data/venues.yml`. Add variables in `_sass/_themes.scss`: `--global-hero-bg`, `--global-card-border`, `--global-chip-bg`. Every new component must use `--global-*` vars so dark mode works for free (theme.js already toggles `data-theme`).
- Hero: full-bleed band under the navbar: name, two title lines (Columbia / CCA), one-sentence mission, three buttons (Research, Join the group, Publications), portrait right (`assets/img/prof_pic.jpg` via `figure.html` for webp). Optional background: a faint SVG strain waveform generated once from `simulate_gw_noise.ipynb` and committed to `assets/img/hero-waveform.svg`.
- Cards: reuse the `.card.hoverable` + 6px border pattern already used by repo cards; Bootstrap 4 `row row-cols-1 row-cols-md-3` grids. Research cards: image top (3:2), title, one-line summary. People cards: square photo, name, role, one-line blurb, icon row (site, GitHub, ORCID, email). Alumni: compact two-column list "Name — role, years -> now at X".
- Footer: switch `footer_fixed: false` (fixed footer steals viewport on long pages and mobile); add a second footer row with affiliation logos/links (Columbia Astronomy, CCA) and social icons.
- Responsive: verify at 375, 768, 1100 px; hero stacks portrait under text on < 768.
- Accessibility: alt text from `people.yml` names; `prefers-reduced-motion` respected (disable the more-authors typing animation in `bib.html` when set).

## 6. Data models

`_data/people.yml`
```yaml
# roles used for grouping/ordering on /group/
role_order: [pi, postdoc, phd, masters, undergrad, visitor, staff]
members:
  - id: khusid          # used for photo filename and cross-refs
    name: Nicole M. Khusid
    role: phd            # one of role_order
    title: PhD student, Columbia Astronomy   # free text shown under name
    start: 2023
    end:                 # empty = current
    photo: khusid.jpg    # assets/img/people/; falls back to assets/img/people/placeholder.svg
    blurb: Ringdown polarizations and black-hole spectroscopy.
    research: [ringdown, tests-of-gr]   # slugs of _research/*.md
    links: {website: https://..., github: nkhusid, orcid: 0000-..., email: ...}
    bib_name: "Nicole M Khusid"        # exact braced string used in papers.bib author fields, for linking
alumni:
  - id: mitman
    name: Keefe Mitman
    role: postdoc
    start: 2023
    end: 2026
    now: Assistant Professor, Somewhere University
    now_url: https://...
```

`_data/collaborators.yml`
```yaml
- name: Will M. Farr
  affiliation: CCA / Stony Brook
  url: https://...
- name: LIGO Scientific Collaboration
  url: https://ligo.org
  type: collaboration   # person | collaboration | institution
```

`_research/<slug>.md` (collection; `collections.research: {output: true, permalink: /research/:name/}`)
```yaml
---
layout: research
title: Black-hole spectroscopy and ringdown
slug: ringdown
order: 1
img: assets/img/research/ringdown.png
summary: Measuring the quasinormal-mode spectrum of remnant black holes to test the Kerr hypothesis.
keywords: ringdown          # regex matched against the bib `keywords` field
members: [khusid, siegel]  # ids from people.yml
software: [maxisi/ringdown] # names from _data/repositories.yml
---
Body text (Markdown), 1–3 paragraphs, optional figures.
```

`_data/teaching.yml`
```yaml
courses:
  - code: ASTR GU4xxx
    title: Gravitational-Wave Astrophysics
    institution: Columbia University
    role: Instructor
    terms: [Spring 2026, Spring 2027]
    url: https://courseworks...
    materials: https://github.com/maxisi/...   # optional
    description: One-line description.
mentoring: >
  Free-text paragraph(s) about advising, summer programs, outreach.
```

`_news/YYYY-MM-DD-slug.md` (existing collection; keep)
```yaml
---
layout: post
date: 2026-09-15 09:00:00-0400
inline: true        # true = one-liner on home; false = full post with title
related_posts: false
---
Text with links. (Convention: papers, arrivals/departures, awards, talks.)
```

`_data/gists.yml` (drives the notes import; see Section 7)
```yaml
- id: 7d63b4878a48e5e1c5e0307159bb3e09
  slug: simulate-gw-noise
  title: Simulating detector noise from a power spectral density
  date: 2023-02-03
  tags: [noise, simulation]
  description: Generate coloured Gaussian noise matching a LIGO/Virgo PSD and validate it with a Welch estimate.
```

## 7. Gists -> Notes pipeline

Inventory (all public gists of github.com/maxisi; all are single-file Jupyter notebooks with stored outputs):

| Created | Gist id | File | Proposed title | Tags |
|---|---|---|---|---|
| 2022-04-22 | f768d30911756bc7c805b5097e3c7019 | example_choosefdwaveform.ipynb | Generating frequency-domain waveforms with LALSimulation | waveforms, lalsuite |
| 2022-06-29 | d033b94be8af4b7d3b0e167f7574224f | loading_pe_example.ipynb | Reading LIGO–Virgo posterior samples with h5py | data-access, parameter-estimation |
| 2022-10-10 | e3bb4af28edd892b38448340a3e90a75 | example_choosetdwaveform.ipynb | Generating time-domain waveforms with LALSimulation | waveforms, lalsuite |
| 2023-02-03 | 7d63b4878a48e5e1c5e0307159bb3e09 | simulate_gw_noise.ipynb | Simulating detector noise from a power spectral density | noise, simulation |
| 2023-03-05 | 7c54e438ccc71d45a4b067b883e4d337 | fetching_gwosc_data.ipynb | Downloading and reading strain data from GWOSC | data-access, gwosc |
| 2023-05-15 | e3847dfe3d81d2c306f6efa518f0e732 | fetching_psds.ipynb | Fetching noise PSDs for LIGO–Virgo events | noise, data-access |
| 2023-05-20 | 22e4c460da0edd0cc5a8ea106a7a718a | fetching_gwosc_data_bulk.ipynb | Bulk-downloading GWOSC strain data | data-access, gwosc |
| 2023-05-22 | bc1f20aeafc29422ce33c99fd5817c70 | pymc_hierarchical.ipynb | A hierarchical Gaussian model in PyMC | hierarchical-inference, pymc |
| 2023-07-27 | 2ce82fae45da4f12721d6b981e742732 | hier_numpyro.ipynb | A hierarchical Gaussian model in NumPyro | hierarchical-inference, numpyro, jax |
| 2023-07-27 | db17a3d8d8ae7772a8b298a3b9b1aed3 | hier_numpyro_cuda.ipynb | Running the NumPyro hierarchical model on a GPU (or merge into the previous post as a second section) | hierarchical-inference, numpyro, gpu |
| 2024-03-01 | 9d535e29b11f1829848e89c4af9608cc | get_design_acf.ipynb | The autocovariance function of the LIGO–Virgo design PSD | noise, ringdown |

Topic buckets for the notes index and tag pages: data-access, noise, waveforms, hierarchical-inference. Sampled notebooks: `loading_pe_example` (24 cells, downloads a 357 MB Zenodo file, uses h5py/seaborn) and `simulate_gw_noise` (7 cells, uses lalsimulation). Conclusion: never re-execute in CI; convert stored outputs.

Options considered:
- A. al-folio `{% jupyter_notebook %}` tag (jekyll-jupyter-notebook -> `nbconvert --to html` in an iframe). Already wired and the reason `deploy.yml` runs `pip3 install --upgrade jupyter`. Cons: iframe with fixed height, no site typography, no MathJax consistency, weak SEO/search, extra CI dependency.
- B. Convert to Markdown posts once, commit Markdown + PNG outputs + the .ipynb. Native `post` layout, rouge highlighting, MathJax, dark mode, dfm.io look; no build-time Python. **Chosen.**
- C. `_plugins/external-posts.rb` (RSS) — not applicable to gists.

Implementation (B):
- New `bin/import_gists.py`, stdlib-only like the other scripts. For each entry in `_data/gists.yml`: fetch `https://api.github.com/gists/<id>` (optional `GITHUB_TOKEN`), save the notebook to `assets/notebooks/<slug>.ipynb`, and write `_posts/<date>-<slug>.md` with front matter (`layout: post`, `title`, `date`, `description`, `tags`, `notebook: /assets/notebooks/<slug>.ipynb`, `gist: https://gist.github.com/maxisi/<id>`, `related_posts: false`). Cells: markdown verbatim; code -> fenced ```python; `stream`/`text/plain` outputs -> fenced text (strip ANSI escapes); `image/png` -> base64-decoded to `assets/img/notes/<slug>/output_<n>.png` and emitted via `{% include figure.html path=... class="img-fluid rounded z-depth-1" zoomable=true %}`; `text/html` (pandas/arviz tables) -> wrapped in `{::nomarkdown}...{:/nomarkdown}` and styled with a small `.notes table` rule. Idempotent: skips a post if the gist `updated_at` is unchanged unless `--force`; never touches hand-edited posts unless `--force`. Flags: `--dry-run`, `--only <slug>`. Reasonable alternative if the pure-Python converter grows too hairy: shell out to `uvx --from nbconvert jupyter-nbconvert --to markdown` (uv is installed locally).
- `_layouts/post.html`: add a "Source notebook" line under the date when `page.notebook` is set (download link + gist link + optional Colab link `https://colab.research.google.com/gist/maxisi/<id>`), à la dfm.io.
- `notes/index.html` (moved from `blog/index.html`): dfm.io-style list grouped by year: `<time>Mon D YYYY</time> <a>Title</a> — one-line description`. Drop read-time chips, featured cards and the tag/category header; keep `jekyll-archives` tag pages (`/notes/tag/<tag>/`) for the four topic buckets, and list those four as a small filter line at the top.
- Config changes: `blog_name: Notes`, `blog_nav_title: notes`, `blog_description: tutorials and code notes on gravitational-wave data analysis`, `permalink: /notes/:year/:title/`, `jekyll-archives.permalinks` -> `/notes/:year/`, `/notes/tag/:name/`, `/notes/category/:name/`; `pagination.enabled: false` (11 posts); `display_tags` -> the four buckets; remove `display_categories`. `_includes/header.html`: replace the hardcoded `/blog/` href and `page.url contains 'blog'` test with `/notes/`. `_layouts/post.html` and `_includes/related_posts.html`: same path fix.
- Remove `jekyll-jupyter-notebook` from `Gemfile`/`_config.yml` plugins, the `pip3 install --upgrade jupyter` step from `deploy.yml`, `assets/css/jupyter*.css`, and the jupyter branch in `assets/js/theme.js` (or leave that JS; it is a no-op without notebooks).
- Automation: run by hand when a gist is added (`python3 bin/import_gists.py`), since gists change rarely. Optionally add `.github/workflows/import-notes.yml` with `workflow_dispatch` only, committing `_posts`, `assets/notebooks`, `assets/img/notes`. Do not add it to the weekly publications workflow.
- Future notes can be written directly as Markdown in `_posts/` or as notebooks dropped in `assets/notebooks/` and converted with `bin/import_gists.py --local <path>` (small extension of the script).

## 8. Publications: what stays untouched, what may change

Untouched: `bin/update_publications.py`, `bin/update_inspire_stats.py`, `bin/update_previews.py`, `bin/update_repos.py`, `.github/workflows/update-publications.yml` (except adding paths if a new generated file is introduced), `_bibliography/papers.bib` formatting conventions (newest-first, `bibtex_show = {true}`, `arxiv`, `abbr`, `html`, `preview`, `selected`, `{Name*}` mentee marker), the `years: [...]` line and file path `_pages/publications.md`, `_config.yml` `scholar:` block and `bibliography_template: bib`, `_data/inspire_stats.yml`, `_data/venues.yml`, `assets/img/publication_preview/`.

Light-touch improvements (all additive):
1. Per-area tagging: add a `keywords = {ringdown, tests-of-gr}` field by hand to entries (the sync script never removes or overwrites local fields not in `SYNC_FIELDS`, so this survives). Add `keywords` to `filtered_bibtex_keywords` in `_config.yml` so it is hidden from the displayed BibTeX. Research pages then render `{% bibliography -f {{ site.scholar.bibliography }} -q @*[keywords^=ringdown]* %}` (the same `^=` regex operator `_layouts/page.html` already uses for `related_publications`); verify in a local build.
2. Client-side filter chips on /publications/: in `_layouts/bib.html`, add `data-keywords="{{ entry.keywords }}"` and `data-year` on the entry `<div class="row">`; a ~40-line `assets/js/pub_filter.js` toggles visibility; chips generated from `site.research` titles/keywords. Add the toggled class names to a `safelist` in `purgecss.config.js`.
3. Stats tiles: restyle `_includes/inspire_stats.html` as a 3-tile row (h-index / papers / citations, each "all / non-collab"), same data, same links; reuse on Home as a compact line.
4. Mentee legend + linking: keep the asterisk convention; add a one-line legend include; optionally repurpose `_data/coauthors.yml` to link braced mentee names to `/group/#<id>` (the layout looks up `site.data.coauthors[author_last_name]` after stripping `*`; because braced names parse as a single token the lookup key would be the full string, e.g. `"Keefe Mitman"`; test the `coauthor.firstname contains author.first` guard with a nil `first` before relying on it).
5. Home "selected publications": keep `_includes/selected_papers.html` (5 `selected` entries); optionally cap at 4–5 via `--max` once the group section is above it.
6. Regression check after every phase that touches these files: `python3 bin/update_publications.py --dry-run`, `python3 bin/update_previews.py --dry-run`, `python3 bin/update_repos.py` (with token) and confirm no unexpected diff.

## 9. Build, preview, deploy

Local constraint: system Ruby is 2.6.10 (`/usr/bin/ruby`), no Docker/colima/podman installed; previews were hand-rendered. Options:
- **A (recommended): native Ruby via Homebrew.** `brew install ruby@3.3 imagemagick` (ruby@3.3 = 3.3.12, keg-only: add `/opt/homebrew/opt/ruby@3.3/bin` to PATH in the shell or a `direnv`/`.envrc`), `gem install bundler`, `bundle config set --local path vendor/bundle` (vendor is git-ignored), `bundle install`, `bundle exec jekyll serve --livereload --config _config.yml,_config_dev.yml`. Add `_config_dev.yml` with `imagemagick: {enabled: false}` and `jekyll-minifier` disabled for fast rebuilds (commit it; CI does not use it). Avoid the Homebrew default `ruby` formula (4.0.7) — gem compatibility unknown; also bump `deploy.yml` `ruby-version` to `3.3` so local and CI match. Bootstrap steps documented in README.
- B: containers via `brew install colima docker docker-compose`, `colima start`, `docker compose up` with the existing `docker-compose.yml`/`Dockerfile` (use `build: .` so the fork's Gemfile is honoured; the prebuilt `amirpourmand/al-folio` image tracks upstream). Heavier and slower on file watching; keep as fallback.
- C: CI previews. `deploy.yml` already builds on `pull_request` without deploying. Add `actions/upload-artifact` of `_site` for PR builds so a rendered copy can be downloaded and opened locally (`python3 -m http.server -d _site`). Cheap insurance for anything the local toolchain cannot reproduce (e.g. purgecss output).

CI changes: Ruby 3.3; remove the `pip3 install --upgrade jupyter` step and the giscus `yaml-update-action` step (giscus unused; if kept, harmless); keep `purgecss` with a safelist; delete upstream Docker workflows; leave `update-publications.yml` alone. Deployment target (gh-pages via JamesIves) unchanged.

## 10. Config changes summary (`_config.yml`)
- `description`, `keywords`, `og_image`, `serve_og_meta: true`, `serve_schema_org: true` with real content; `icon` -> a real favicon file in `assets/img/` (replace the emoji).
- `footer_fixed: false`; `footer_text` shortened; `last_updated: true` optional.
- `collections`: remove `projects`; add `research: {output: true, permalink: /research/:name/}`; keep `news`.
- Blog/notes keys as in Section 7; remove `external_sources`, `disqus_shortname`, `giscus` block (or leave giscus empty).
- `enable_project_categories: false`, `enable_progressbar: false` (optional, reads less "blog"), `enable_navbar_social: false`, keep `enable_darkmode`, `enable_math`, `enable_medium_zoom`.
- `plugins`/`Gemfile`: drop `jekyll-jupyter-notebook`, `jekyll-twitter-plugin`, `jekyll-get-json` (unused), `classifier-reborn` only if `--lsi` is also removed from `deploy.yml`/`bin/cibuild` (LSI powers related posts; with 11 posts it is optional).
- Add `keywords` to `filtered_bibtex_keywords`.

## 11. Cleanup (delete)
- `_posts/*` (all 18 demo posts), `_projects/*` and `_includes/projects.html`, `_includes/projects_horizontal.html`, `_includes/scripts/masonry.html`, `assets/js/masonry.js`.
- `_news/announcement_{1,2,3}.md`.
- Demo content of `_data/coauthors.yml` (replace with mentee/collaborator links or an empty mapping).
- `assets/img/{1..12}.jpg`, `assets/img/*-screenshot.png`, `assets/img/al-folio-preview.png`, `assets/img/pagespeed.svg`, `assets/audio/`, `assets/video/`, `assets/pdf/example_pdf.pdf`, `assets/plotly/`, `assets/jupyter/`, `assets/bibliography/`, `assets/json/`, `assets/css/jupyter*.css`, `reports/`.
- `.github/workflows/{deploy-image,deploy-docker-tag,docker-slim}.yml`, `.github/stale.yml`, `.github/release.yml`, `.github/ISSUE_TEMPLATE/`, `.all-contributorsrc`, `CONTRIBUTING.md`, `_includes/scripts/wechatModal.html`, `_includes/disqus.html`, `_includes/audio.html`/`video.html` (if unused), `_includes/repository/repo_trophies.html` + `repo_user.html` (trophy service retired upstream; `repo_trophies.enabled: false`), `_layouts/distill.html` + `_sass/_distill.scss` + `assets/js/distillpub/` (unless distill posts are wanted), `_plugins/external-posts.rb` (with the `feedjira`/`httparty` gems), `bin/deploy` (manual deploy script superseded by Actions), `bin/cibuild` (or keep as the one-liner CI uses).
- Decide on `assets/img/bh.png` (unreferenced; possibly a former favicon/hero) — keep if it becomes the favicon.

Keep: `_includes/cv/*`, `_includes/resume/*` (cv layout), `_layouts/profiles.html` (may serve as fallback for the PI bio), Font Awesome/Academicons assets, `_plugins/{cache-bust,details,file-exists,hideCustomBibtex}.rb`.

## 12. Phased implementation plan

**Phase 0 — Tooling baseline (no visible change).** Tasks: install Ruby 3.3 toolchain (Section 9A); add `_config_dev.yml`; get `bundle exec jekyll build` green locally; bump `deploy.yml` to Ruby 3.3 and add the PR artifact upload; screenshot the current pages for before/after. Files: `deploy.yml`, `_config_dev.yml`, `README.md`, `.gitignore` (`vendor/`, `.bundle/` already there). Owner input: none.

**Phase 1 — Cleanup and re-plumbing.** Tasks: delete everything in Section 11; strip `_config.yml` per Section 10 (except collection `research`, added in Phase 3); rename blog -> notes routes; `/repositories/` -> `/software/` with a redirect stub (`_pages/repositories-redirect.md`, `layout: none`, `<meta http-equiv="refresh">`); `footer_fixed: false`; run the pipeline dry-runs. Files: `_config.yml`, `Gemfile`, `_includes/header.html`, `_layouts/post.html`, `_includes/related_posts.html`, `notes/index.html`, `_pages/repositories.md`, `purgecss.config.js`. Owner input: confirm nav labels and whether to keep the progress bar and distill.

**Phase 2 — Group and Teaching (highest content value, no design risk).** Tasks: create `_data/people.yml`, `_data/collaborators.yml`, `_data/teaching.yml`; `_includes/people_grid.html`, `_includes/people_list.html` (alumni), `_includes/teaching.html`; `_pages/group.md` (join section text, current members grid by `role_order`, alumni, collaborators), `_pages/teaching.md`; `assets/img/people/` with `placeholder.svg`; SCSS for `.people-grid`, `.person-card`, `.alumni-list` in a new `_sass/_group.scss` imported from `assets/css/main.scss`. Owner input: full roster with roles, years, links; alumni with current positions; photos (square, >= 600 px, consent obtained); collaborator list; courses with terms/links; join-the-group text (undergrad/PhD/postdoc paths, Columbia application links, CCA fellowship links).

**Phase 3 — Research areas and Home.** Tasks: add `research` collection; write `_research/<slug>.md` for each area (suggested slugs from the current bio and papers: `ringdown` (black-hole spectroscopy / tests of GR), `populations` (spins, hierarchical inference, mass-function cosmology), `fundamental-physics` (polarizations, birefringence, dark matter/boson clouds), `methods` (Bayesian methods, ML, jim/ringdown software), plus whatever the owner prefers); `_layouts/research.html` (hero image, body, "People" chips from `people.yml`, "Software" cards via `repository/repo.html`, "Selected papers" via keywords query); `_includes/research_grid.html`; `_pages/research.md`; `_layouts/home.html` + rewrite of `_pages/about.md` front matter (hero fields: `tagline`, `titles`, `cta`) and shortened bio; `_sass/_home.scss`. Owner input: area titles, 1–3 paragraphs each, one image per area (own figures preferred; check reuse rights), one-sentence mission statement, 2–3 real news items to seed `_news/`.

**Phase 4 — Notes pipeline.** Tasks: `_data/gists.yml` with the 11 entries above; `bin/import_gists.py`; run it, review generated posts (fix headings, add a one-paragraph intro where the notebook lacks one, add `description`); `_layouts/post.html` source-notebook line; `notes/index.html` list; remove jupyter plugin/CI step; add `.notes table` styles. Owner input: approve titles/tags; decide whether to merge the two NumPyro notebooks; check that each notebook's stored outputs are safe to publish.

**Phase 5 — Publications light touch.** Tasks: add `keywords` to bib entries (hand edit; commit separately so the weekly bot commit stays clean); `filtered_bibtex_keywords`; filter chips + `assets/js/pub_filter.js` + purgecss safelist; stats tiles restyle; mentee legend; verify sync scripts dry-run clean and that the `years:` line is still rewritten correctly. Files: `_bibliography/papers.bib`, `_config.yml`, `_layouts/bib.html`, `_includes/inspire_stats.html`, `_pages/publications.md`, `purgecss.config.js`. Owner input: keyword assignment per paper (can be a quick pass over 69 entries), which mentees to link.

**Phase 6 — Design polish and launch.** Tasks: typography/colour variables, hero background, favicon, OG metadata and `og_image`, 404 page text, dark-mode pass on every page, responsive pass (375/768/1100), Lighthouse check, README documenting content workflows (add a person, add a course, add a note, add a repo, how the weekly bot works). Merge to `master`; watch the `deploy` run; trigger `update publications` via `workflow_dispatch` once to prove the pipeline still commits cleanly on top of the new tree.

Suggested branching: one PR per phase off `master`, each built by the PR job; Phases 2 and 3 can proceed in parallel once Phase 1 merges.

## 13. Open questions for the owner
1. Branding: keep "Maximiliano Isi" as site title, or a group name (e.g. "Isi Group", "Gravity & Black Holes group at Columbia/CCA")? Affects `title`, navbar brand, hero, footer.
2. Exact affiliation lines and order (Columbia Astronomy vs. CCA/Flatiron) and whether to show office/address and a public email.
3. Research area list (3–5) and their names; whether each needs its own page or anchors on one page suffice at launch.
4. Roster: who counts as a member vs. collaborator; include undergrads/visitors; alumni cutoff; photo consent.
5. Teaching: course list with codes/terms; include guest lectures/summer schools? Mentoring text?
6. Notes: publish all 11 notebooks; merge the two NumPyro ones; comments (giscus) on or off; keep the name "Notes" vs. "Blog"/"Resources"/"Tutorials".
7. Software: extend `_data/repositories.yml` (e.g. group members' repos) and whether to group by research area.
8. News: how much to backfill (last 1–2 years of papers/awards/hires) and who maintains it.
9. Design: fonts and accent colour preference; keep the scroll progress bar; keep distill support; footer fixed or not.
10. Analytics (Google/Cronitor/Cloudflare) or none; `serve_og_meta`.
11. Local toolchain choice: Homebrew Ruby 3.3 (recommended) vs. colima/Docker.
12. Whether to drop `--lsi`/`classifier-reborn` (related posts) to speed up builds.

## 14. Risks and mitigations
- Breaking the publications automation: the sync script regex-rewrites `years:` in `_pages/publications.md`; the workflow `git add`s fixed paths. Mitigation: never rename those files; run `--dry-run` after every phase; do a manual `workflow_dispatch` after launch; hand edits to `papers.bib` in a separate commit.
- jekyll-scholar query behaviour for `keywords` (`^=` regex operator) may differ from expectations (e.g. entries without a `keywords` field). Mitigation: verify in a local build early in Phase 5; fall back to `related_publications`-style explicit key lists on research pages.
- purgecss stripping classes toggled by JS (filter chips, dark-mode-only elements). Mitigation: `safelist` in `purgecss.config.js`; check the PR artifact build, not just local serve.
- Native gem builds on macOS (nokogiri, imagemagick bindings) with Ruby 3.3. Mitigation: use bottled ruby@3.3 and `bundle config build.nokogiri --use-system-libraries` if needed; fallback to colima.
- Photo/consent and privacy for members; alumni current positions go stale. Mitigation: `people.yml` is the single source; add a yearly review note in README.
- Notebook outputs may contain paths, tokens or large embedded data. Mitigation: review each generated post; the importer strips ANSI and can drop cells tagged `hide`.
- Site width/typography changes can regress the publications layout (thumbnail column, badges). Mitigation: keep `.publications` at the 800px measure inside the wide container; before/after screenshots from Phase 0.
- Scope creep on research pages. Mitigation: launch with cards + one page per area containing text and a keyword-filtered paper list; enrich later.

### Critical files for implementation
- `_config.yml`
- `_layouts/bib.html` (with `bin/update_publications.py` as the invariant it must respect)
- `_includes/header.html`
- `_layouts/about.html` (basis for the new `home.html`)
- `.github/workflows/deploy.yml` (and `update-publications.yml`, to be left intact)
