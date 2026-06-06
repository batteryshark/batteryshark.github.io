# BatteryShark Writeup Archive

This is the canonical source for the BatteryShark security research and reverse engineering writeup archive.

The public surface is the Jekyll site. The repository can stay private while still publishing GitHub Pages through the existing workflow.

## What Lives Here

- `_posts/` contains the article source of truth.
- `assets/images/` contains article images and downloadable research snippets.
- `topics.md`, `series.md`, and `about.md` provide the reader-facing navigation routes.
- `MAINTAINING.md` explains how to edit or add future posts.

The older `todo/writeups` wiki-style tree is intentionally retired after migration so content does not drift between two sources.

## Build

```powershell
bundle install
bundle exec jekyll build --trace
```

The local Windows environment used for this cleanup did not have Ruby/Bundler installed, so the GitHub Actions workflow remains the reference build until local tooling is added.
