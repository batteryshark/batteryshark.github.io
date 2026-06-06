# Archive Rebuild Audit

This is a maintenance note for the BatteryShark writeup archive rebuild. It is not part of the public site.

## System Map

- Canonical content source: `_posts/`
- Reader navigation: `index.md`, `topics.md`, `series.md`, `about.md`
- Shared rendering: `_layouts/`, `_includes/post-list-row.html`, `_includes/post-nav.html`
- Presentation: `_sass/` and `assets/css/papicu.min.scss`
- Article media and research snippets: `assets/images/YYYYMMDD/`
- Maintainer workflow: `README.md`, `MAINTAINING.md`, `.github/workflows/jekyll.yml`

The retired wiki mirror in `../writeups/` now points back to this site so content cannot drift between two sources.

## What Changed

- Added topic and series navigation around the fixed topic set.
- Normalized every post with descriptions, tags, TOC flags, hero images, and archival notes.
- Preserved existing permalink format: `/:year/:month/:day/:title.html`.
- Removed generated desktop artifacts and ignored future `.DS_Store`, `Thumbs.db`, `__pycache__`, and `*.pyc` files.
- Cleaned small embedded Python research snippets without changing their role as article artifacts.

## Confusion Register

- Local Jekyll build is not yet proven because Ruby/Bundler are unavailable on the host.
- A Docker-based Ruby build was rejected as too risky because it would mount the private repo into an external image.
- The visual pass still needs a rendered inspection after Ruby/Bundler are installed locally or CI runs.

## Scorecard

- Content source clarity: strong
- Reader navigation: strong
- Metadata consistency: strong
- Asset hygiene: strong
- Local build reproducibility: pending toolchain setup
- Rendered mobile/desktop confidence: pending Jekyll build

## Next Safe Checks

- Install Ruby 3.3 and Bundler locally, then run `bundle install` and `bundle exec jekyll build --trace`.
- Inspect homepage, topics, series, one long image-heavy post, one code-heavy post, and one Masterpiece post in a browser.
- Run the GitHub Pages workflow after pushing to confirm production parity.
