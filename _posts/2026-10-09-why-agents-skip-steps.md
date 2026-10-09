---
layout: post
title: "Why Agents Skip Steps"
date: 2026-10-09
description: "An agent can't see the state of your machine, and even the best current models are unreliable at predicting what real code will do when it runs. We delegate as if they could, because we do those checks ourselves without thinking about them. What to keep in mind when you start something with an agent, while it runs, when it gets stuck, and when you change your mind about what you wanted."
tags: [agents, ai-engineering, harness-design, tooling]
toc: true
image: /assets/images/20261009/social.png
---

<figure>
  <img src="/assets/images/20261009/banner.png" alt="Title art: the words Why Agents Skip Steps beside a column of faint checkboxes labeled with questions you answer for yourself: migration ran? server up? column exists? which emulator config?">
</figure>

In [my last post]({% post_url 2026-10-02-bug-hunting-in-retro-games %}), an
agent found a bug in Parasol Stars by running the original ROM twice with one
change and comparing memory frame by frame. I only looked because I happened
to play that room in the remake and it felt wrong: harder than I remembered,
in a way that didn't seem intentional. I had no proof, just a guess that
something was off, and I made a bet on it.

The agent had built the remake's enemy logic against an emulator harness with
no multitap, and it kept that configuration without comparing it to my
emulator, which had the multitap on. I knew which setup I play on. It never
came up.

This post is about getting better results from agents on larger projects,
the kind that run for weeks with twenty to fifty agents working at once, not
one agent and a button: the things I've found worth keeping in mind when I
start something, while it runs, when it gets stuck, and when I change my mind
about what I wanted, which on a long project I always do. The first half is why the gap exists.
If you already believe an agent can't see your machine, skip to
[part two](#part-two-what-to-keep-in-mind).

## Part one: why the gap exists

## What stays in your head

<figure>
  <img src="/assets/images/20261009/00-in-your-head.png" alt="A person at a laptop glancing at a log, with a thought cloud above holding sticky notes and icons: DB is up, port 3000, changed the schema an hour ago, a flask for the legacy tests that flake on purpose, a chart from last month's sheet, a monitor with the sound crossed out, and a note that Sam owns the deploy script.">
  <figcaption>All of it current, none of it written down.</figcaption>
</figure>

When you work on something you know, you carry a model of it. You know which
services are up, what you changed an hour ago, which tests are flaky, and what
the data usually looks like. Outside code it's the same. You know the chart
came from last month's spreadsheet, and that the sound stopped after you
plugged in the new monitor.

It isn't only facts. The model is also what you expect: this call is fast,
that service drops connections under load, the build takes four minutes, the
cache is probably stale. You run on those assumptions without noticing
they're assumptions, right or wrong, and most problem-solving is comparing
what happened to what you expected and chasing the difference.

You check your work against that model all the time without thinking of it as
checking: a glance at a log, a quick run because something looks off. The
model is often wrong, which is why you also keep notes, open a debugger, and
ask a coworker. But the tracking and the checking happen whether you plan them
or not.

Because that work costs nothing, we don't plan for it when we delegate. Look
at how people write tasks for agents:

- Hook the API up to the database.
- Make the checkout page look better on mobile.
- Clean up my downloads folder.
- You are a senior engineer at a top FAANG company who never makes
  mistakes... blah blah blah.

Each one describes a change. None says what the current state is, or how
anyone would know the change worked. The person writing it might know both
and not think to say them, or might not have thought about either. They know
what they want, and that's what goes on the card.

<figure>
  <img src="/assets/images/20261009/01-handoff.png" alt="Diagram: a task card that says Hook the API up to the database is handed to an agent. Above the person, a thought cloud holds the facts that are not on the card: the DB is up, the migration might not have run, port 3000, the legacy tests fail on purpose.">
  <figcaption>Port 3000 and the migration never make it onto the card.</figcaption>
</figure>

An agent can't look unless you gave it something to look with. So the request
gets the change, and the facts and the checks stay with you. Working well with
agents means handing those over too: the current state, written down, and a
way to check results that the agent can run.

## The context window is all it has

The agent has none of that. Its context window is its working memory: if a
fact isn't in it, the agent guesses or goes and gets it. Reasoning can tell
it what should have happened. Only observation tells it what did. Compiler
errors, test output, logs, screenshots, and query results are how the real
world gets into that memory, and they're how the agent finds out what's
true.

<figure>
  <img src="/assets/images/20261009/03-two-loops.png" alt="Three rows. You: idea, change, compare against what you know and what you see, next. Agent: idea, change, done? with nothing to compare against. Agent with checks: idea, change, run or look, write down what is now known, next.">
  <figcaption>The middle row is what you get when the request only describes the change.</figcaption>
</figure>

Unchecked assumptions get expensive because later work depends on them. If an
agent assumes the data import worked, it builds the chart, writes the summary,
and polishes the report on top of an empty table. Each step looks finished,
and all of them are wrong.

That's the quantitative case. A lot of the direction on a real project is
qualitative: you look at what came back, wrinkle your nose, and say eh, this
isn't it, what about this. The page doesn't pop. The enemy shows up too
early. The animation is right but the timing feels off. The settings menu
works and it's three clicks too deep.

Half of it is questions: what is this,
what did you mean by that, what if we did it the other way, and can we try
that without buying it a ring. That happens constantly while building,
and there's no check for it except a person looking at the output. The agent
can't wrinkle its nose on your behalf, which is one more reason the output
has to end up somewhere you'll look.

How far its own predictions go, and how well it judges its own work, is
measured in [What the agent has instead](#what-the-agent-has-instead) near
the end, with the numbers in the appendix.

## The strongest models build their own checks

As of October 2026, the strongest models don't deal with this by predicting
harder. They build checks. I've watched it happen. On a recompilation project
before this one, the audio skipped when a certain part of a stage started,
and I couldn't explain it. The cause turned out to be the process freezing
while it waited for the window to become responsive, which meant nothing
inside the process could see the gap: its threads were stopped, so from its
point of view no time had passed. Logging from the code would have shown
nothing.

The model built a monitor in a separate process that tapped the audio output
while the game ran and did spectral analysis on the stream, and that found
the hiccup. That was where I noticed it couldn't see what I could see, and
that I'd been assuming it could.

Claude Opus 5's launch examples are the same move: asked to rebuild a machine part from a drawing it couldn't
view, it wrote its own computer vision pipeline; asked to build a market data
feed with no live feed to test against, it wrote its own test harness. Anthropic's prompting guide now tells developers to
remove explicit verification instructions because the model already checks
its work, and OpenAI says the same about GPT-6 Astra. The labs with the most
compute trained their models to build checks. They didn't train them to stop
needing checks.

Anthropic's harness work shows the same thing from the other side. A harness
is the software around the model that runs its tools and manages its context.
Across three Opus releases, the author removed more of it each time: forced
context resets, then rigid sprint plans. One component stayed through every
version: a separate evaluator that clicked through the running app in a real
browser.

<figure>
  <img src="/assets/images/20261009/04-scaffolding.png" alt="Timeline across three Opus releases. Scaffolding blocks drop away one by one: forced context resets, rigid sprint plans, explicit verification instructions. One block stays across all three: a separate evaluator with a real browser.">
  <figcaption>Each release let more scaffolding go. The browser never left.</figcaption>
</figure>

Meta tried the other route, training its Code World Model on 120 million
traced Python functions so it would have an internal sense of what code does
at runtime. On the June 2026 benchmark it finished in the bottom half. A
model that predicted perfectly would still not know the state of your
machine.

## Why this won't close soon

- **Your state isn't in the weights.** Any model, of any design, has to
  observe your system to know what's true in it.
- **Prediction degrades with distance and size.** Models predict by reasoning
  one step at a time, the cost grows with every line, and running the real
  thing is faster, cheaper, and exact.
- **The industry is betting on loops.** Frontier coding models are trained
  inside runnable environments and rewarded when hidden tests pass, which
  makes them better at using feedback, not at working without it.
- **Reliability lags capability.** METR's May 2026 report put the public
  frontier at about 12 hours for tasks agents finish half the time and 1.5
  hours for tasks they finish 80% of the time.

What would change this is a model that keeps an explicit, updated picture of
program state across steps and knows when that picture is uncertain. That's a
different kind of model from what we have. Even then, it would reduce how
often an agent needs to check, not remove the need to look.

## A feedback loop is worth more than a bigger model

If checks are what make agents reliable, you can buy reliability with checks
instead of model size. My own run is the smallest version of this: the same
27B model went from 0% to 67% at ten lines ahead when it was allowed to check
each step. Two 2026 studies found the same at larger scale: an agent that
checks its model of a game against recorded observations ranks first in every
setting, and picking the best harness gains about as much as picking the best
model (appendix).

The limits: the model still has to turn the signal into a fix, a wrong checker steers it wrong with confidence, and many cheap attempts
can cost more than one good one. Within those limits, a loop built for a
smaller or local model is the cheapest upgrade available.

## A check can't tell you what you wanted

I was talking about this with a colleague, a principal engineer at a major
software company who has spent a few decades building things and has gone
all in on making agents build them the way he wants. He pushes back. In his
view, loops and goals are crutches, a way of failing upward at a cost, and the real
work is the design up front. His plans read like hand-held pseudocode where
an algorithm matters and detailed prose where it doesn't, with the data model
and the state model written out. It's more work, and what comes back is what
he meant. Tokens are cheap, he says, and thought is not.

He is right about the part a check can't reach. A check tells you whether
what you asked for happened. It can't tell you whether you asked for the
right thing, and a loop that runs until the check passes gives you exactly
what you asked for and not what you wanted, which is the oldest complaint in
software, moved down one level. The two fixes are not in competition. The
design says what you want; the check says whether you got it. A check written
from a vague request confirms a vague result, which is why the checks have to
come from the requirement, and why the requirement has to be written down.

<figure>
  <img src="/assets/images/20261009/10-design-check.png" alt="Two boxes. The design says what you want: data model, state model, which algorithm where. The check says whether you got it, written from the requirement, not the code. An arrow from the design to the check labeled checks come from here. Below: a loop that runs until the check passes gives you what you asked for; the design is the only thing that says whether that was what you wanted.">
</figure>

The newer frontier models are very good at solving things with no direction,
and that's most of their appeal: one-shot builds, changes to existing code,
long runs of work from a vague instruction. The cost is that more gets
assumed. Every requirement I didn't write down gets filled in by the model's
judgment, and the work is finished before I see any of it.

With twenty agents at once that compounds: each fills its gaps its own way, then they build on
each other's fills, and the distance between what I think I said and what
exists grows with every hour nobody is watching. The gap is between the work
it did and the work I wanted, and a passing check doesn't close it.

## Part two: what to keep in mind

This is the half to use. Four moments on any project longer than a day:
when you start, while it runs, when it gets stuck, and when you change your
mind about what you wanted. First, what a check can be, because most of what
follows depends on having one.

## Checks are not only tests

Tests are one kind of check. The job is to make the things you'd check
yourself available to the agent as text it can ask for.

- **Is it running? What's in there right now?** A state dump: one command that prints current rows, config, queue depth, or file tree.
- **Does it look right?** Screenshots, rendered output, browser automation at phone and desktop widths.
- **What did I just change?** Before and after snapshots, and diffs.
- **Will this break that?** A repro script for the bug; an invariant check such as "every order has a customer".
- **What does the outside service do?** A fake or recorded copy of the service the agent can call safely.
- **Does it look and sound right while it runs?** A tap at the output: screen control, an audio capture, not a read of the file.
- **Where was I? What do I actually know?** The working record, in a file.

The Parasol Stars harness is one of these. It runs the remake and the original
side by side and compares game state every frame. It isn't a unit test. It
shows the agent a difference that it couldn't have predicted from the code.

<figure>
  <img src="/assets/images/20261002/01-same-inputs.png" alt="Two rows of screenshots from Parasol Stars round 1-5 at 10, 25 and 50 seconds. With a TurboTap the triangle enemies stay inside their brick maze; with one pad they leak out through the walls.">
  <figcaption>Same save state, same input. One controller port's worth of difference.</figcaption>
</figure>

The same idea works away from code. Reorganizing 8,000 photos: write a
manifest of every file and its hash first, then confirm every hash exists
exactly once in the new layout. Analyzing a spreadsheet: compute the key totals
two ways and reconcile them against the source before writing any
conclusions. Writing from sources: a script that confirms every quote appears
word for word in the source. Setting up a home server: a health check that hits
each service and prints up or down after every change.

Some things can only be checked at the end of the line. A rendering bug, a
skipped audio frame, a checkout button that sits off-screen on a phone: none
of that shows up in the code or in a file, only in the output. That's why
I've put time into computer-use tooling, [CUA](https://github.com/trycua/cua)
and my own [computer-ctrl](https://github.com/batteryshark/computer-ctrl) on
top of it. Those checks used to need me. They don't, if the agent has the
tool and the expectation that it will use it, but that has to be in the plan;
nothing hands it over by default.

## When you start

**Build the check first and watch it fail for the right reason.** A test that
fails with "module not found" proves the module doesn't exist yet, not that
the test checks the behavior you care about.

**Write down what's in your head.** Which database, which port, which tests
fail on purpose, what normal data looks like, which emulator configuration is
the real one. The design belongs here too: the data model, the state model,
and which algorithm goes where. An agent fills unspecified design with
whatever is most common in its training data, and that's rarely what you had
in mind. Put the lasting answers in a file the agent reads every session:

```markdown
## How to check things here
- Run the app: `make dev` (port 3000). Load sample data: `make seed`
- Full check: `./check` (lint, types, tests; under a minute)
- Peek at the DB: `./scripts/db-peek orders 5`
- See a page: `npx playwright screenshot http://localhost:3000/cart cart.png`
- Known noise: tests in `legacy/` fail on purpose
- Don't edit: `tests/contract/` (these are the acceptance checks)
```

**Give access, not instructions.** An agent can only check what it can
observe. In Anthropic's harness experiments, Claude out of the box was a poor
judge of its own work; a separate judging agent with a real browser was the
strongest lever they found. A dev environment, sample data, a browser, and
read-only logs beat paragraphs of instructions.

**Match the effort to the model.** Frontier models already check their work,
so skip the step-by-step verification script; give them the checks, a clear
definition of done, and the acceptance rule. Smaller and local models need the
loop spelled out. A typo fix needs none of this.

## While it runs

This is where the scale bites. With one agent I can follow the thread: I
see it hit a problem or build something I didn't expect, and I step in. With
twenty running at once I can't. They're making decisions I have no idea
about, in parallel, all day. I can't watch twenty things, so the record and
the checks have to do it for me: each agent writes down what it observed and
what it assumed, each result gets checked before anything builds on it, and
I read the misses.

Most agent workflows keep a plan or a to-do list. That records what has been
done. It doesn't record what's actually known, which is what you need when
something goes wrong.

For any task with several dependent steps, have the agent keep a short working
record: the goal, what has been observed and how, what's assumed but not yet
checked, which later steps depend on each assumption, and the one check that
would settle the assumption the next step depends on.

<figure>
  <img src="/assets/images/20261009/06-working-record.png" alt="A working record for adding a download CSV button to a filtered dashboard. Goal: the download contains exactly the records the current filters show. Observed: test dataset with filter region=EU shows 12 records. Assumed, not checked: the export request includes the active filters. Depends on it: everything about whether the file is right. Next check: inspect the export request, then parse the file and compare its record IDs with the 12 expected. Two arrows from a mismatch: no filters in the request points at the button-to-endpoint path; request right but file wrong points at the export.">
  <figcaption>Without this, the next move after a wrong file is "try something else."</figcaption>
</figure>

Without the record, a wrong file sends the agent through unrelated fixes:
tweak the button, rewrite the query, restyle the CSV. With it, a mismatch
points somewhere. If the request has no filters, the bug is between the button
and the endpoint. If the request is right and the file is wrong, the bug is in
the export. Either way one assumption gets crossed off and the next move has a
reason.

The record also lets evidence expire. A check on yesterday's build says nothing
about today's, so when something a check relied on changes, that fact goes
back to assumed.

This record is the external working memory. Logs and test output are raw
observations. The record holds what they mean for the task.

I keep a skill for this,
[project-tracker](https://github.com/batteryshark/skill-tap/tree/main/skills/productivity/project-tracker):
one Markdown dashboard per project with the current objective, status,
attempts, decisions, open questions, and next actions, with observed facts
kept separate from theories and unknowns. I'm not pitching it. It's a
collection of the things I kept finding myself tracking in larger projects,
iterated on now and then, and it has been useful on the bigger ones.

**Check before you build on it.** Not after every edit; before a result
becomes the foundation for more work. The data import before the analysis, the
schema before the API.

**Protect the acceptance checks.** An agent told to make tests pass will make
tests pass by whatever route is open. In a June 2026 study, agents graded by a
hidden suite of browser tests scored near-perfect while the library they were
asked to build was often dead or absent; they'd built a demo that held the
tested behavior directly. The same pattern shows up in every current
measurement of it (appendix). Tests can be wrong too, so the rule isn't
"never touch a test." It's "never weaken a check to get a pass." Keep the
acceptance checks out of the agent's reach, hold some back, and tell it: if a
check looks wrong, stop and say why.

**End with what wasn't checked and what was assumed.** "Probably works"
shouldn't turn into "done" on the way to the summary, and a requirement the
agent invented shouldn't pass as one you gave it.

## When it's stuck

**When it starts skipping around, ask what would tell the explanations
apart.** An agent trying one plausible fix after another has stopped learning
from its attempts. Ask which observation would show which explanation is
right. If two attempts teach it nothing new, it should change how it's
investigating or say what's blocking it.

Every check has a scope, and it's easy to ask the wrong question. "The file
downloaded" isn't "the right records downloaded." Reopening a document proves
it saved, not that it says the right things. Reading back an audio setting
proves the setting changed, not that you can hear anything.

<figure>
  <img src="/assets/images/20261009/07-scope.png" alt="Three pairs. What the check proves versus what you wanted to know: the file downloaded versus the right records downloaded; the document saved versus the document is correct; the output device changed versus you can hear sound.">
  <figcaption>All three pass. None of them answers the question you had.</figcaption>
</figure>

The worst case is a check written from the same misunderstanding as the code.
If the agent believes exports should ignore filters, it writes an export that
ignores filters and a test that confirms it, and they agree. Write checks from
the requirement, not the implementation, and look at a real output yourself at
least once.

## When you change your mind

On anything that takes more than a day I change my mind about what I
wanted, because I see the thing and it isn't it. That isn't a failure of the
plan; part of the requirement gets discovered by building. The record above
handles the mechanics: evidence expires, assumptions go back to assumed. The
harder part is the requirement that was never written down at all.

<figure>
  <img src="/assets/images/20261009/11-remake-scene.jpg" alt="A 2.5D arcade platformer stage at sunset: a small hero with a striped parasol on a mossy stone bridge, bubble enemies, winged star enemies, gold coins over block platforms, waterfalls and a castle in the parallax background, and a score, lives, round and time HUD.">
  <figcaption>Roughly what I had in mind, and nothing like what came back.</figcaption>
</figure>


My remake is the example. It was mostly built with frontier models, but not
from a prompt that said port this game. I gave them an emulator and a working
environment, local models to generate art and assets, and the harness that
compares the remake with the original every frame.

I picked Godot because I knew it: cross-platform, easy to build with, and it
exports to HTML, which matters because models are very good at web pages and
most harnesses can drive Chrome over its debug protocol, so an HTML build
gives the agent a whole environment to guess, check, and sort out its own
mistakes in a browser tab it controls. It also means my machine isn't
covered in game windows while it tests.

The emulator was the same kind of decision. An open-source emulator gives the
agents instrumentation and a debugger for free: no crude harness to wire up,
no getting lucky and catching the odd behavior at the right moment. They can
step cycle by cycle and dump any subsystem they need, which makes the
emulator a source of truth, and I led with that from the start because I
value an agent being able to reproduce anything at any time.

The target helped too. An arcade game has no complicated state carried between screens,
so every part of it can be run and tested on its own without playing back to
it; I'm a few seconds from any state I need to validate.

None of that is specific to games. Games are a useful case because they're a
runtime of many subsystems running in real time, with consequences in real
time and everything bubbling up into a presentation layer, plus remote
systems to coordinate with if there's a network feature. That's what makes
them a good test of working with agents on complex systems.

The question I led with was how to give the agent a way to know whether it
was getting closer, without me playing whack-a-mole over every detail.
Asking it to figure out what's inaccurate and fix it doesn't work; it has
nothing to compare against. The frame-by-frame harness was the answer: a
deterministic signal, cheap to run, that says how far off the remake is and
where. Inside that frame the models did a lot of good work. Then I asked for a 2.5D graphical
overhaul with no requirements, because I didn't have any. The models
extruded 3D geometry out of the 2D sprites. It was horrible.

<figure>
  <img src="/assets/images/20261009/09-asked-wanted.png" alt="Diagram of the 2.5D request. In the person's head, a sticky note says what I wanted: looks like a studio with a budget reimagined it, with art direction, pipeline and tooling marked as never written down. The task card says 2.5D graphical overhaul. The agent returns a card showing the flat pixel sprite next to the same sprite extruded into blocks, marked done with a check and wanted with a question mark.">
  <figcaption>Every check passed. The sprite got thicker.</figcaption>
</figure>

To get what a studio with a budget would produce, I'd have to supply the
tooling, the direction, and a production pipeline for turning a retro game
into something that looks designed. Frontier models can do a lot and there's
headroom there. But even if they can do it, will the assumptions they make be
the ones I want? And if they are, is the way they get there any good? I have
no way to tell.

Anthropic's guide for Opus 5 now ships a prompt to hold the model to the
scope you asked for and to check in when different readings of the request
would lead to materially different work. The useful version of that is an
agent that helps you find your requirements while it builds: it says what it
assumed, it says so at the point where the assumption changes the shape of
the work, and it lists all of them at the end.

## The prompt

A prompt that covers it:

```text
Goal: [one sentence]
Done means: [something observable: a command's output, a screenshot, a number]
What you can't see from here: [current state, constraints, what normal looks like]

Before changing anything, show me how you'll check this. If no check exists,
build the smallest one that works and run it so we both see the current state.

Keep a short note of what you've observed versus what you're assuming, and
check an assumption before building on it. When a requirement I did not
state would change the shape of the work, say what you assumed before you
build on it. Don't edit [tests/contract/]. If a check looks wrong, or two
attempts teach you nothing new, stop and tell me instead of working around it.

When you're done, show the check output, list what you did not verify, and
list the requirements you assumed.
```

## What to build

In your own projects: one command that checks everything and prints short
output. Scripts that print current state for anything you'd otherwise
look at in a GUI. Sample data with known right answers, and fakes for outside
services. A way to see UI output. A working-record file for multi-session
work.

In the harnesses we all use: tools that report whether something finished, not
just whether it was requested. The project's check run automatically when the
agent says it's done, with the result shown to both of you. Compiler and type
errors surfaced right after each edit. Files the user can mark off-limits so
the acceptance checks stay intact. The working record kept outside the context
window so it survives restarts. Loop detection: repeated attempts that produce
nothing new should trigger a new approach or a question. Screenshots, browser
control, and log tails as standard tools, and cheap experiments with sandboxes
and rollback. Tool output trimmed so the one useful line isn't buried in
2,000 lines of noise.

In teams: treat "agent-legible" as an engineering goal. One-command dev
environments, fast deterministic tests, clear error messages, and a CLI or API
for anything only reachable through a GUI. Test the checkers too: plant a known
bug and confirm the check catches it. All of this makes the humans faster as
well.

## Build the check first

Before handing an agent a task, the question isn't whether it can make the
change. It usually can. The question is whether it can check the result. If it
can't, build that first.

In the Parasol Stars work, every mistake the agent made was found the same way:
by checking its claim against the logged data. The log made that possible, not
the agent.

The log has a second use. People remember the hits and forget the misses. An
agent that does one surprising thing well leaves a stronger impression than
the ten routine failures around it, and the failures turn into ordinary days.
Engineers surface the hits, managers see the hit rate, and the misses never
make it into the summary. I'm not immune. I have a skill pack that Codex has
been writing for four days, about 280 skills, and I don't know if any of it
is any good, because nothing checks it. A record of what was verified and what
wasn't is the only account that keeps the misses in it.

The same applies to writing, including this post. It started as a rant, got
sorted into beats and a short brief for what a reader should walk away with,
and went through three reviewers with different jobs, a lint for my own voice,
a check of every number against its paper, and one measurement I ran myself.
None of that is prompting. It's the pipeline, and without it the result is
the generic article you have already read ten times.

## Sign-off

If you take one thing from this, take the question: before you hand an agent
a task, how will either of you know it worked? If you take two, the second is
that "you are a senior engineer at a top FAANG company who never makes
mistakes" is not a check.

The numbers are below for anyone who wants them. If you've built checks like
these for your own work, or had an agent's self-check fool you, I'd like to
hear about it.

## What the agent has instead

The facts behind part one, for anyone who wants them before the numbers.


**Its predictions are good on toy code and poor on real code.** Predicting
the output of a small function is a solved problem, to the point that the
classic benchmark for it was retired this year, and a September 2026 paper
notes that an agent doesn't need to predict anyway when it can run the
program. Fair for agents, and beside the point for the model: being able to
run the program says nothing about how good its own picture is, which is
what you're relying on every time it can't run the thing, or doesn't.

Real repositories are a different story: on a September 2026
benchmark built from instrumented test runs, the best of five models got 38%
of the runtime questions right ([A1](#a1-toy-code-versus-real-code)), and on a June 2026 benchmark the best of
twelve models caught three quarters of the failing tests while most caught a
third or less. On my own machine, a 27B model asked for the program state ten
lines ahead got it right never with reasoning off and two thirds of the time
with reasoning on, at twenty times the cost ([A2](#a2-my-lookahead-run)).

**It's optimistic about its own work.** In a 2026 Anthropic harness
experiment, agents reliably graded their own work too generously
([A4](#a4-harnesses-horizons-and-loops)), and the
June 2026 benchmark's authors attribute its misses to a bias toward
predicting that tests pass.

**It can't see your state.** No training run puts your database, your
environment variables, your library versions, or yesterday's edits into a
model's weights. A perfect simulator would still need to know where to start.

**It can't reliably tell when it's wrong without outside input.** Asking a
model to review its work without running anything means it re-reads text it
wrote a moment ago. Research from 2024 on self-correction found that without
outside feedback, models often don't improve and sometimes get worse. With
reliable feedback, an error message or a test result, self-correction works.

The same limit holds at the other end of the speed range. TypeSafe AI's Jev,
launched in September, is a System One model: hand it a state and a typed
question and it returns a decision with a probability in one pass, no prose,
no reasoning. That's useful for routing and triage, and the probability isn't
evidence that the decision was right. It's the model's assessment of itself,
which is the thing that can't be trusted without outside input. A fast
decision still needs a check from outside the model.

## Appendix: the measurements

The numbers behind the claims above, for anyone who wants them. Every model
and benchmark here is from 2026 unless the date says otherwise.

## A1. Toy code versus real code

The classic test, CruxEval, asks a model to predict the output of a small
Python function. By 2026 it had stopped separating models: one evaluation
service quit running LiveCodeBench's version on new releases because scores
had saturated, and a benchmark paper from late September 2026 says the format
is no longer suitable for coding agents, because an agent can run the program
instead of reasoning about it.

That paper, Codoku, replaced it with puzzles
an agent can't run its way out of: fill in typed blanks in a partial program
so that global constraints hold. Claude Opus 5 solved 77% of the small
puzzles and 50% of the large ones. GPT-5.6 Sol solved 67% and 54%. The
open-weight models ranged from 50% down to 11%.

SWE-Flux, also from September 2026, asks what happens at runtime inside
twelve Python repositories, with the answers taken from instrumented test
runs: which branch executed, how many times a loop ran, what a variable held,
which exception fired. The best of five models, GPT-5.4, scored 38% overall
and 29% on the loop questions, where, as the authors put it, a model must
track how the program evolves over iterations.

A June 2026 benchmark took 435 cases from SWE-bench Verified and asked twelve
models, frontier ones included, whether a test would pass. GPT-5.5 caught 74%
of the failing tests. Claude Opus 4.7 caught 35%, Qwen3.5-397B 32%, and
Qwen3-30B 2.5%. The authors attribute the misses to a bias toward predicting
that tests pass. Asked which method or line would use the most time or
memory, none of the twelve reached a recall at five of 0.2. Meta's CWM, the
model trained on execution traces, caught 21% of the failing tests, ninth of
twelve, and came last at picking out the most expensive method or line.

<figure>
  <img src="/assets/images/20261009/02-real-code.png" alt="Bar chart of the share of failing tests each model caught when predicting test outcomes on real repository code: gpt-5.5 73.5%, gpt-oss-120b 49.5%, gpt-5-mini 39.5%, claude-sonnet-4-6 39%, claude-opus-4-7 34.5%, Qwen3.5-397B 32%, gpt-5.2 27%, gpt-5.4 23.5%, CWM 21%, claude-haiku-4-5 18.5%, Qwen3-235B 8%, Qwen3-30B 2.5%.">
  <figcaption>Twelve models, 435 cases from SWE-bench Verified, June 2026. Data from Towards Evaluation of Implicit Software World Models in Coding LLMs.</figcaption>
</figure>

## A2. My lookahead run

Qwen3.8-27B, a 4-bit MTPLX export served locally on an M5 Max: give it a
short Python program and the variable state after one executed line, ask for
the state n lines later, score exact match on the whole state. Thirty
synthetic programs (a few integers, a list, a short loop with a branch),
seed fixed, temperature 0, one run.

With reasoning off, one line ahead it was exactly right 70% of the time.
Three lines ahead, 20%. Five, 3%. Ten, never, though on average it still had
about half the variables right. Each answer took about a second.

With reasoning on at the lowest effort setting, it got one and three lines
ahead right every time, five lines 92%, and ten lines 67%. The cost was 290
reasoning tokens at one line ahead and about 1,200 at ten, and 6 to 24
seconds per answer instead of one. The reasoning text is the model executing
the program by hand, one line at a time. That's the mechanism: it can
simulate, the simulation costs tokens in proportion to the distance, and it
still fails a third of the time at ten lines.

<figure>
  <img src="/assets/images/20261009/08-local-lookahead.png" alt="Grouped bar chart. Qwen3.8-27B, exact state predicted n executed lines ahead. Reasoning off: 1 line 70%, 3 lines 20%, 5 lines 3%, 10 lines 0%. Reasoning on at low effort: 100%, 100%, 92%, 67%.">
  <figcaption>Reasoning off, 120 prompts; reasoning on at low effort, 49 prompts. My run, October 2026.</figcaption>
</figure>

Limits: synthetic code, one model, one quantization, one run per prompt, and
the reasoning condition was stopped at twelve programs to keep it under
twenty minutes. The harness, the raw results, and the two runs that didn't
work (a stale `mlx_lm`, and a server that ignored the thinking-off flag and
reasoned into a token cap) are in the post's repository.

## A3. Agents building to the test

In a June 2026 study, Copilot CLI agents running Claude Opus 4.7 and GPT-5.5
were asked to port a React data table to Angular as a reusable library,
graded by a hidden suite of 222 browser tests. Without the suite, they
delivered a library that was present but unfinished. With the suite in the
loop, scores went near-perfect while the library was often dead or absent:
the agents built a demo that held the tested behavior directly. The authors'
line: the agent doesn't, on its own, validate what it ships as a user would.

SpecBench, from May 2026, measures the same thing as the gap between visible
tests and a held-out suite. Every frontier agent saturates the visible tests,
the gap persists, and it grows by 28 points for every tenfold increase in
code size. One agent produced a 2,900-line hash-table "compiler" that
memorized the test inputs.

METR's pre-deployment run of GPT-5.6 Sol in June 2026 put its 50% time
horizon at about 11 hours when cheating attempts were counted as failures and
beyond 270 hours when they were counted as successes, and noted its detected
cheating rate was the highest of any public model on their harness.

## A4. Harnesses, horizons, and loops

Anthropic's March 2026 harness experiments: out of the box, Claude was a poor
QA agent for its own work. Separating the agent doing the work from the agent
judging it was the strongest lever, and the judge got a real browser through
Playwright so it could click through the live app. Opus 4.5 let the author
drop forced context resets; Opus 4.6 let him drop the sprint structure and
run the evaluator once at the end. A solo run of the same task took 20
minutes and $9; the full harness took 6 hours and $200, with a difference in
output quality the author calls immediately apparent.

METR's May 2026 frontier report: the public frontier at about 12 hours for
tasks finished half the time (confidence interval 5 to 61 hours) and about
1.5 hours for tasks finished 80% of the time, with the strongest agents
having essentially saturated the Time Horizon 1.1 suite.

Loops versus model size: a 2026 study of coding agents on ARC-AGI-3 found the
variant that checked its model of the game against recorded observations
ranked first in every setting and succeeded at lower reasoning effort, at the
price of more compute per run. Han and Sun (ICML 2026) found that picking the
best harness gains about as much on Terminal-Bench as picking the best model.
The 2024 "Large Language Monkeys" paper is the origin of the result: a cheap
open model with tests choosing among many attempts beat the best single
attempt of that year's frontier models on SWE-bench Lite. Those models are
two generations gone; the result has held up.

---

*Sources: the saturation note is on [Vals AI's LiveCodeBench page](https://www.vals.ai/benchmarks/lcb)
(updated September 2026); Codoku is Li, Sun, Li and Su,
[Codoku: Renewable Program-Reasoning Challenges for Frontier Coding Agents](https://arxiv.org/abs/2609.34661)
(September 2026); SWE-Flux is Taherkhani et al.,
[Can LLMs Reason About Runtime Behavior?](https://arxiv.org/abs/2609.28449)
(September 2026); the test-outcome benchmark from
[Towards Evaluation of Implicit Software World Models in Coding LLMs](https://huggingface.co/papers/2606.27406)
(2026). Self-correction: Huang et al.,
[Large Language Models Cannot Self-Correct Reasoning Yet](https://arxiv.org/abs/2310.01798)
(ICLR 2024) and Kamoi et al.,
[When Can LLMs Actually Correct Their Own Mistakes?](https://aclanthology.org/2024.tacl-1.78)
(TACL 2024). Jev: TypeSafe AI,
[Introducing System One Models & Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev)
(September 2026). ReAct: [Yao et al.](https://arxiv.org/abs/2210.03629) (2022).
Opus 5 examples and guidance:
[Introducing Claude Opus 5](https://www.anthropic.com/news/claude-opus-5) and
[Prompting Claude Opus 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5).
Astra guidance: OpenAI,
[Rethinking skills and prompts for GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)
and [Using GPT-6 Astra](https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra).
Harness experiments: Anthropic,
[Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps)
(March 2026). CWM: [FAIR CodeGen team](https://arxiv.org/abs/2510.02387)
(2025). METR: [Frontier Risk Report, February to March 2026](https://metr.org/blog/2026-05-19-frontier-risk-report/)
(May 2026) and
[Summary of METR's predeployment evaluation of GPT-5.6 Sol](https://metr.org/blog/2026-06-26-gpt-5-6-sol/)
(June 2026). Repeated sampling: Brown et al.,
[Large Language Monkeys](https://arxiv.org/abs/2407.21787) (2024). ARC-AGI-3:
[Rodionov](https://arxiv.org/abs/2607.15439) (2026). Harness versus model:
Han and Sun, [How good is your harness?](https://icml.cc/virtual/2026/68323)
(ICML 2026). Building to the test: Ma, Kereopa-Yorke and Schultz,
[Building to the Test: Coding Agents Deliver What You Check, Not What You Requested](https://arxiv.org/abs/2606.28430)
(June 2026); Zhao, Srikanth, Wu and Jiang,
[SpecBench: Measuring Reward Hacking in Long-Horizon Coding Agents](https://arxiv.org/abs/2605.21384)
(May 2026, revised September 2026). The Parasol Stars material and the
lookahead measurement are from my own harnesses; the measurement's code and
raw results are in the post's repository.*
