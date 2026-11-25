# batteryshark.github.io

Source of [batteryshark.github.io](https://batteryshark.github.io): write-ups on reverse engineering, game hacking
and low-level systems. It is a Jekyll site, built and published to GitHub Pages by `.github/workflows/jekyll.yml`.

## What lives here

- `_posts/` holds the posts.
- `assets/images/` holds post images and the small research snippets some posts link to.
- `topics.md`, `series.md` and `about.md` are the navigation pages.
- `MAINTAINING.md` covers front matter, tags and how to add a post.

## Build locally

Needs Ruby 3.3 (the version the workflow uses) and Bundler.

```sh
bundle install
bundle exec jekyll serve
```

The site is then at `http://127.0.0.1:4000`. `bundle exec jekyll build` writes it to `_site/` without serving.
