# Maintaining The Archive

This repository is the canonical source for the BatteryShark writeup archive.

## Local Build

The GitHub Pages build uses Ruby 3.3 and Jekyll.

```powershell
bundle install
bundle exec jekyll build --trace
bundle exec jekyll serve
```

If Ruby or Bundler are not installed locally, use the GitHub Actions workflow as the build reference.

## Adding Or Editing A Post

- Posts live in `_posts/YYYY-MM-DD-slug.md`.
- Keep permalinks stable by leaving existing filenames and dates alone.
- Use the fixed tag set: `reverse-engineering`, `game-hacking`, `windows-internals`, `compatibility`, `hardware-security`, `arcade`, `emulation`, `tooling`, `low-level-systems`, `masterpiece`.
- Prefer a clear `description` that tells a reader why the post is worth opening.
- Use `archival_note` for dated claims, tools, or links instead of rewriting history silently.
- Use `toc: true` for long or heavily sectioned posts.
- Put article assets under `assets/images/YYYYMMDD/` and link them from the post with absolute `/assets/images/...` paths.

## Frontmatter Shape

```yaml
---
layout: post
title: "Example Title"
date: 2026-06-06
description: "One sentence that frames the post for a reader."
tags: [reverse-engineering, tooling]
toc: true
hero_image: /assets/images/20260606/00.png
archival_note: "Originally written in 2026; specific tools and links may have changed."
---
```

Series posts can also set:

```yaml
series: "Masterpiece"
series_part: 1
```

## Cleanup Rules

- Keep the practitioner voice; polish clarity, not personality.
- Do not keep generated desktop artifacts such as `.DS_Store` or `Thumbs.db`.
- Research scripts kept with posts should be small, readable, and clearly tied to the article.
