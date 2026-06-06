---
layout: post
title: "Masterpiece - Putting together an App Format (Part Four)"
date: 2021-10-25
description: "Packaging the filesystem and runtime assumptions into an app format that can be moved around sanely."
tags: [masterpiece, compatibility, game-hacking, low-level-systems]
toc: true
hero_image: /assets/images/20211025/v4p3.png
archival_note: "Originally published in 2021 as part of the Masterpiece series; metadata and package names are preserved from the original design."
series: "Masterpiece"
series_part: 4
---

![vxlogo](/assets/images/20211025/vxicon.png)

## Background

Now that we have a composite filesystem library and shims that allow us to establish our own operating context, we need something to tie everything into an easily deployable package. This concept has suffered the most iterations over the years, but we need a few things:

- Some minimal metadata to identify the app.
- Our 'content' including read-only files and our smoothie map.
- A list of any executable entry-points we want to expose to whatever loads the app.
- A list of any plugins or configuration options that need to be enabled to make it all work.

## Enter .vxapp

Simplicity is key here, and .vxapp takes pages from various app formats including Mac's .app, and various console package formats.

A typical app layout may look like the following:
```
App Name.vxapp /
    content /
        some_image.vhdx
        smoothie.map
        plugin_options.ini
     vxapp.config
     vxapp.info (e.g. name, rating, etc.)
     metadata( icon? )
```

When an app is loaded, we look at the vxapp.config JSON format which uses entries like the following:
```
[
    {
        "args": "base\\Wolf3d.exe -conf base\\wolf3d.conf -fullscreen -exit",
        "cwd": "",
        "envar": [],
        "executable": "C:\\app\\base\\dosbox.exe",
        "map": "smoothie.map",
        "name": "Play Game",
        "preload": [
            "pdxproc.dlldynamic",
            "pdxfs.dlldynamic"
        ]
    }
]
```

Each "entrypoint" has a few fields:
- A (virtual) path to the target executable.
- An (optional) set of args.
- An (optional) alternate working directory to start the app from.
- A specified map as an app may choose to list many different maps to run different versions of the app.
- A name for a loader to reference.
- Any environment variables that need to be set.
- Any preloaded pdx plugins we need to use.

One lesson learned over the many iterations is to keep metadata generic, we aren't trying to recreate steam or another online curating service, we want something generic that can be reused. As a result, nothing in vxapp.info is ever used by a loader.


Now that we have a format, we have to build a loader to tie all this together -  more to come!
