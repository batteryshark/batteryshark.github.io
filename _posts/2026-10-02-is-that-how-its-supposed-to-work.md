---
layout: post
title: "Is That How It's Supposed to Work?"
date: 2026-10-02
description: "Some of what we call how a game works is behavior nobody intended, accepted as normal because nobody could tell the difference. Agents make it practical to go looking for it. A fun example: Parasol Stars, where one stale byte and an empty controller port decide whether the enemies can walk through walls."
tags: [reverse-engineering, game-hacking, emulation, low-level-systems, tooling]
toc: true
image: /assets/images/20261002/01-same-inputs.png
---

Most of what we call "how the game works" is just what shipped. Usually that's
what the developers meant. Sometimes it isn't, and from the outside nobody can
tell the difference.

That gap is what I find fascinating. It isn't really bug hunting, though
there's usually a bug underneath. It's unintended behavior that got accepted as
normal operation, because nobody noticed, or because they noticed and assumed
it was on purpose. Speedrunners have lived in this space for decades. To find
one of these you have to know a game well enough to ask a strange question: why
does this room only act like this with two players? Why is it harder with this
controller?

Before patches and over-the-air updates, the cartridge was the final word. If a
routine misbehaved under a condition nobody tested, that behavior WAS the game,
and players learned to live with it. Some of these were seen and kept. Street
Fighter II's cancels began as a side effect of making special-move inputs more
forgiving, and the team spotted it during development and left it in. Others
nobody caught at all. In Super Mario Bros., Lakitu is supposed to throw his
Spiny eggs with a bit of physics, aimed off Mario's speed and position and
bouncing off whatever they hit. A bug makes them drop straight down, and for
decades that was just Lakitu.

That second kind is the one I can't leave alone. Nobody would have known it
wasn't intended. With the source gone, the only record of intent is the code,
and sometimes the code disagrees with itself.

This is where agents earn their keep in reverse engineering. Finding these is
mostly patient work through ambiguity: read a routine, form a theory, run the
original twice with one condition changed, diff the state frame by frame, and
refuse to accept "it feels harder" as an answer. That loop is tedious enough
that people rarely run it on a hunch. An agent will run it all afternoon.

Here's a fun one from a side project. I noticed the symptom. An agent ran it
down.

<figure>
  <img src="{{ '/assets/images/20261002/01-same-inputs.png' | relative_url }}" alt="Two rows of screenshots from Parasol Stars round 1-5 at 10, 25 and 50 seconds. With a TurboTap the triangle enemies stay inside their brick maze; with one pad they leak out through the walls.">
  <figcaption>Same save state, same input (player 1 holds LEFT), one difference: what's plugged into the console.</figcaption>
</figure>

## A remake that was too faithful

Parasol Stars ("The Story of Bubble Bobble III") is Taito's 1991 PC Engine
follow-up to Rainbow Islands, and I've been rebuilding it in Godot. As far as I
know the original source is lost, which matters less than you'd think. The game
is small, it's all HuC6280 assembly, and the emulators are excellent. With
agents doing most of the work, the practical route is lifting: read a routine,
write the same logic in GDScript with the ROM addresses in the comments, and
prove it with a lock-step harness that runs the remake next to the original in
an emulator and compares game state every frame. Lifting deserves its own post.

The complaint that started this was mine. Round 1-5 is a zig-zag brick maze
with ten triangle enemies flying around inside it and four water dispensers on
the roof. The room is built for one move: let the triangles bunch up, then
flood the maze from above. In the remake the triangles kept leaking out and
chasing me in the open, and a flood never cleared the room. I didn't remember
it being anywhere near that hard.

So I played the original in an emulator. As far as I could tell, no triangle
got out the whole time I was on that screen, and one flood from the roof washed
every one of them out at once. (The data later showed four brief trips through
the maze's real openings. Hold that thought.)

The obvious theory was that the remake had the speeds wrong. It was the first
thing the loop killed: the agent measured player and triangles against the
original, and they matched to the sub-pixel, 1 pixel a frame, 2 when angry.

What differed was the hardware. The remake had been built against an emulator
harness with no multitap, inherited one-pad behavior from it, and the
two-player spec kept it. My emulator had the multitap switched on. Nobody had
checked one against the other. Neither was wrong, and it turns out the game
behaves differently on them.

## Five questions, one answer

Every home PC Engine and TurboGrafx-16 has one controller port. Behind it is a
4-bit register at `$1000`. Writing bit 0 (SEL) picks which half of the pad
answers, the four directions or the four buttons, and bit 1 (CLR) is a reset
line.

The TurboTap, NEC's multitap, plugs into that one port and holds five sockets.
A CLR pulse sends it back to socket 1, and every time SEL goes from 0 to 1 it
steps to the next socket. That's how one port reads five controllers. A pad
plugged straight into the console has nothing that counts sockets. It just
keeps answering.

<figure>
  <img src="{{ '/assets/images/20261002/02-five-questions.png' | relative_url }}" alt="Diagram: the game asks ports 1 to 5 for buttons. With one pad, every port answers with pad 1. With a TurboTap, port 1 is pad 1 and ports 2 to 5 are empty sockets.">
  <figcaption>Without a TurboTap nothing switches between controllers, so your one pad answers all five questions.</figcaption>
</figure>

Bank 0 `$E19B` runs every frame. It resets the tap, then for each of the five
ports it reads the directions, reads the buttons, packs them into one byte,
flips it (the pad sends 0 for pressed) and stores it, `$244D` for port 1
through `$2451` for port 5. It never asks whether a TurboTap is there.

<figure>
  <img src="{{ '/assets/images/20261002/03-reading-a-pad.png' | relative_url }}" alt="Annotated disassembly of the pad read routine at E19B, the eight bits of a controller byte (LEFT is $80, II is $02), and the five held-button bytes $244D to $2451 with port 2 at $244E marked.">
  <figcaption>LEFT is bit 7, so holding it makes the byte $80. Port 2's byte at $244E is where the trouble comes from.</figcaption>
</figure>

So the "mirroring" of player 1 onto player 2 isn't logic in the game at all.
The game always asks five times. Without a TurboTap, the electronics give the
same answer five times.

## Who owns $26

Three routines touch zero-page `$26` in a frame. (Zero page on the HuC6280
lives at `$2000`, so if you're setting a watchpoint, it's `$2026`.)

Player 1's turn writes port 1's held buttons into it. Player 2's turn writes
port 2's, every frame, whether or not anyone has joined, because it's checking
whether someone wants to. Then the enemies move, and the flyers' wall tests
(`$6645` moving right, `$66BC` moving left) read `$26` as a counter before they
ever write it.

<figure>
  <img src="{{ '/assets/images/20261002/04-one-frame.png' | relative_url }}" alt="Four steps in one frame: read the pads, player 1's turn writes port 1 into $26, player 2's turn writes port 2 into $26, the enemies move and the flyers' wall test reads $26 as a row counter.">
  <figcaption>Scratch that two routines borrow: the player code for "buttons held", the flyers' wall test for a counter.</figcaption>
</figure>

So the condition isn't really one pad versus a TurboTap. It's whatever port 2
reports: your own pad mirrored onto it, or an actual second player. The walls
only behave when port 2 reports nothing.

<figure>
  <img src="{{ '/assets/images/20261002/05-what-is-in-26.png' | relative_url }}" alt="The byte $26 shown as eight bits in three setups: TurboTap alone gives $00 and the walls hold; one pad with LEFT held gives $80 and triangles slip; TurboTap with player 2 holding RIGHT gives $20 and triangles slip.">
  <figcaption>A held direction is a big count (LEFT is 128), enough to cover every flyer's wall test that frame.</figcaption>
</figure>

## A counter that assumes zero

A triangle is 10 pixels tall, so when it moves, the wall test checks two rows
of the game's 8x8 collision grid in the column ahead: the head row, then the
row below.

The counter exists for one edge case. When a flyer's head is above the top of
the map, the rows above it don't exist, so the routine sets `$26` to the number
of missing rows and reads row 0 again instead. In every other case it never
sets `$26` at all. It assumes it's 0.

```
row = head_y / 8                 ; $26 is only set when the head is above the map
repeat (height + 7) / 8 times:   ; 2 rows for a triangle
    if map[column][row] is a wall:  return WALL
    if $26 > 0:  $26 = $26 - 1      ; meant for rows above the map: read row 0 again
    else:        row = row + 1
return NO WALL
```

Hand it a stale count and the test re-reads the head row instead of moving
down. The row below is never checked, so a wall that only touches the lower
half of the triangle doesn't exist as far as the triangle is concerned.

<figure>
  <img src="{{ '/assets/images/20261002/06-wall-test.png' | relative_url }}" alt="Two schematic grids. With $26 = $00 the test reads the head row (empty) then the row below (wall) and the triangle turns back. With $26 = $80 it reads the head row twice and the wall in the row below is never read.">
  <figcaption>Each routine is correct on its own. Together, your thumb on the d-pad becomes the wall test's loop counter.</figcaption>
</figure>

## Frame 33

This is the loop's "run it twice with one thing changed" step. Same save state,
same input, once with a TurboTap and once with one pad. The triangles move
identically until frame 33.

At frame 32, triangle 5 is flying right and down, and its right-wall test reads
column 44. Row 8, its head, is open. Row 9 holds a step of the maze. With the
TurboTap, the test reads both cells, finds the step, and the triangle turns
back. With one pad, it reads row 8 twice and flies into the step. Six frames
later it's inside the bricks.

<figure>
  <img src="{{ '/assets/images/20261002/07-the-moment.png' | relative_url }}" alt="Real frames from the original game at frame 32, annotated with the collision grid and the triangle's hitbox. With the TurboTap the test checks an empty cell then a wall; with one pad it checks the empty cell twice. At frame 38 the one-pad triangle is inside the wall.">
  <figcaption>Frame 32 is the same in both runs. The only difference that matters is the value sitting in $26.</figcaption>
</figure>

## How big it is

Measured on the original ROM in the emulator, from the round 1-5 save state:

| Check | TurboTap | One pad |
|---|---|---|
| Player 1 holds LEFT, 4000 frames | 4 of 10 drift out briefly; outside the maze 1.8% of the time | 9 of 10 get out; outside 75.5% of the time |
| Random input, 8 seeds | the same brief trips, 1.8% | 8 to 10 get out; outside 31-53% of the time |
| Player 1 idle, pad 2 holds LEFT, 3000 frames | 9 of 10 get out, frame for frame the same as one pad | |
| Random bot, 96 sessions each | 0 deaths in 480,000 frames | 741 deaths in 459,124 frames |

In the first three rows player 1 is parked and invincible, so only the
triangles act. The bot plays with 9 lives and a session ends at game over,
which is why the frame totals differ. The 1.8% is the baseline: the maze has
real openings, and triangles take brief trips through them even with no input.

The flood tells the same story. After twenty seconds of walking, one flood from
the roof caught all ten triangles in the original with the TurboTap. The
remake's one-pad model, which matches the original's enemy logic frame for
frame, caught two. The other eight were already outside.

And two players don't save you. In the third row, player 1 does nothing while
pad 2 holds LEFT, and the result is identical to one pad. In actual two-player
games (six saved states, including flyer rounds in other worlds), `$26` at the
start of the enemy task is always pad 2's byte.

<figure>
  <img src="{{ '/assets/images/20261002/08-port-two-decides.png' | relative_url }}" alt="Three frames at frame 1500: TurboTap with nobody on pad 2 keeps the triangles in the maze; TurboTap with pad 2 holding LEFT and one pad with player 1 holding LEFT both have triangles outside.">
  <figcaption>It's port 2 that decides, not player 1.</figcaption>
</figure>

In this room, the only setup where the walls hold is the one where port 2 is an
empty socket: a TurboTap, playing alone.

## How do you call it a bug with no source?

There's no design doc and no one to ask, so "unintended" has to be argued from
the ROM. It testifies against itself three times.

The wall test's counter has exactly one job, rows above the map, and every
other path through the routine assumes it's 0. The room is built to be solved
by flooding a maze the triangles stay inside. And on the title screen, bank 0
`$E204` checks whether a TurboTap is plugged in by comparing the new presses on
ports 1, 2 and 3. Press RUN on a single pad and it shows up on all three at
once, so the game sets its multitap flag `$2458` to 0 and turns off two-player
games.

The game knew what hardware it was on. The wall test never asked.

<figure>
  <img src="{{ '/assets/images/20261002/09-the-game-knows.png' | relative_url }}" alt="Annotated disassembly of the title-screen TurboTap check at E204, which sets the multitap flag $2458, and two one-line fixes: STZ $26 at the start of the wall test, or skip the port-2 copy when $2458 is 0.">
  <figcaption>The game's own detection relies on the same hardware behavior that causes the bug.</figcaption>
</figure>

The fix is a two-byte `STZ $26` in front of each wall test. My remake ships with
it on by default. A FLYER WALL BUG option in the pause menu switches between
FIXED and ORIGINAL, and ORIGINAL plays it as shipped, with `$26` holding your
buttons on one pad and player 2's in a two-player game. The regression
harnesses run ORIGINAL, so every baseline recorded from the ROM stays valid. A
controller-port setting couldn't have covered it: with a TurboTap the bug still
happens whenever player 2 holds a direction.

## How it shipped, and whether it's real

My guess, and it is only a guess: the developers mostly tested with a TurboTap
plugged in. The platform's controller notes say every game was expected to
work with the multitap, so it isn't a stretch that one sat on the test bench.
In that setup a one-player game leaves `$00` in `$26`, the counter does
nothing, the walls hold, and every test passes. You'd only see it by playing
with the one pad that came in the box and holding a direction for a while in a
room full of flyers. Even then it just looks like tough enemies.

I fell into the same setup without meaning to. My emulator had the multitap on,
so the original felt fair and the remake felt broken. I'd rebuilt their test
bench by accident.

As for whether it's real hardware behavior: every run here is the original ROM
in an emulator, not a console, and I don't want to oversell it. The TurboTap's
protocol is documented (CLR resets it, SEL steps it), a bare pad has nothing to
step, and I read the emulator's input code to confirm it models exactly that
rather than taking its word for it. The strongest evidence is the game's own
title-screen check, which only works BECAUSE a bare pad answers on every port.
If the hardware didn't mirror, `$E204` would never see RUN on ports 2 and 3.

(If you're looking closely at the TurboTap screenshots, player 2's side still
says GAME OVER / CREDIT 1. The save state was made with the game's flag set to
one pad, and the tap is switched on in the emulator after loading it. It doesn't matter here: the port-2 copy
never looks at that flag.)

I couldn't find this one documented anywhere, which proves nothing except that
it wasn't easy to find. I'd still like it confirmed on a console. If you have a
PC Engine or TurboGrafx-16, one pad and a copy of Parasol Stars: go to round
1-5, hold LEFT for twenty seconds, and watch the triangles. A few brief trips
through the maze's openings are normal. Walking through the bricks isn't.

## Stale scratch

Generalized, this is a bug class. Old consoles keep their temporary values in a
handful of fast, shared bytes, the 6502 family's zero page. Two routines can
each be correct on their own and still disagree about one of those bytes: here,
"buttons held" to the player code and "rows to repeat" to the wall test. The
disagreement only shows under a condition the developers rarely changed, and
then it ships as normal operation.

<figure>
  <img src="{{ '/assets/images/20261002/10-stale-scratch.png' | relative_url }}" alt="The stale-scratch pattern in four steps, and four ways to hunt for it: log the first access to each zero-page byte per routine, find the last writer, vary rarely changed conditions, and diff runs frame by frame.">
  <figcaption>The pattern, and how to hunt for it in other games.</figcaption>
</figure>

The loop from the top becomes a method:

- Log the first access to each zero-page byte inside each routine. A read
  before any write is a lead.
- For each lead, find the code that wrote that byte last, and what changes that
  value: input, hardware, game state.
- Vary the conditions the developers rarely did: controller setup, empty ports,
  region, timing.
- Run the same input twice with one condition changed and diff the game state
  frame by frame. The first frame that differs is where you look.

## What the agent got right, and what it got wrong

What made the agent useful was refusing to stop at the first plausible story,
then doing the parts I'd never have had the patience for: A/B
runs with one condition changed, hundreds of bot sessions and close to a
million frames, finding the exact frame the runs split, and tracing `$26` back
to the routine that wrote it.

It also got things wrong, and how it got them wrong is worth knowing. An early
summary said that with a TurboTap, zero of ten triangles ever leave the maze.
The data said four take brief trips, 1.8% of the time. A first draft of the
infographics claimed it didn't matter which button you held. It does: II alone
is a count of 2, which the first flyer's test uses up. The first came from
quoting a summary instead of the data, the second from generalizing past what
had been run. Both were caught by going back to the numbers. Every claim in a
caption needs a run behind it.

And the one-pad model that made the remake "too hard" was an agent's call in
the first place, kept from the harness without checking my setup. That's the
mistake that surfaced the bug. I'll take it.

Once the explanation held up, I had it package the explaining half as a skill:
take a behavior you understand and produce an evidence-backed set of pictures,
real frames from the original next to diagrams where every number was measured.
The hunting half is still a method rather than a tool. Turning the zero-page
read-before-write sweep into something an agent can run across a whole ROM is
what I want to build next.

## Accepted as normal operation

Both games are in the ROM. The one the developers meant, where the triangles
stay in their maze until you flood them out, and the one most people actually
played, where they slide through the walls whenever you hold a direction. The
only thing separating them is a condition nobody thought to change, and for
thirty-five years the second one has just been how round 1-5 works.

That's the part I find fascinating, and there's no reason it's unique to this
game. Plenty of old ROMs must carry behavior nobody intended and everybody
accepted. Finding it
used to take someone who knew the game cold and had a lot of evenings. Now it
takes an emulator you can script and something that doesn't get bored diffing
RAM. That second part is new.

Thoughts? I'm curious whether anyone remembers this room being brutal on a
console with one pad, and what other "that's just how it works" behavior is
sitting in games we all know.

---

*Sources: the Lakitu egg behavior is documented on
[The Cutting Room Floor](https://tcrf.net/Super_Mario_Bros.) (summarized by
[Nintendo Everything](https://nintendoeverything.com/how-lakitu-throws-spiny-eggs-in-super-mario-bros-is-due-to-a-glitch-not-the-intended-behavior/));
the Street Fighter II cancel story comes from its designers, via
[Game Developer](https://www.gamedeveloper.com/business/-i-street-fighter-ii-i-designer-opens-up-about-the-cancelling-bug-).
The TurboTap protocol and the multitap expectation are from pce-devel's
[PCE_Controller_Info](https://github.com/pce-devel/PCE_Controller_Info), and the
emulator's model of it from [Geargrafx](https://github.com/drhelius/Geargrafx)'s
input code. All the measurements were taken on the original ROM in an emulator
harness, except the flood comparison's one-pad number, which comes from the
remake's lock-step-matched model as noted.*
