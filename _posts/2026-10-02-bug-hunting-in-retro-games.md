---
layout: post
title: "Bug Hunting in Retro Games"
date: 2026-10-02
description: "The bugs that went undetected, or that everyone accepted as intended, are the interesting ones, and retro games have a lot of them. An emulator with good instrumentation lets an agent test many configurations and compare the results, which makes it practical to search for these bugs. The example: a Parasol Stars bug where the second controller port controls whether enemies can fly through walls."
tags: [reverse-engineering, game-hacking, emulation, low-level-systems, tooling]
toc: true
image: /assets/images/20261002/banner.jpg
---

<figure>
  <img src="/assets/images/20261002/banner.jpg" alt="Title art in the style of the Parasol Stars title screen: the words Bug Hunting in rainbow bubble letters, a ribbon that says In Retro Games, the parasol in an oval window over the sea, and a triangle enemy slipping out through the oval's wall.">
  <figcaption>Title art made from the remake's REMASTER title screen.</figcaption>
</figure>

Bugs fascinate me, especially the ones that nobody detected, or that everyone
took to be intended. Some of them stay in shipped software for years, and
people learn them as normal behavior. Finding one of those decades later has
always been one of my favorite things.

Retro games are a good place to look for these bugs. At that time, it was easy
to make a bug like this by accident. Most developers wrote in assembly, and they had few of
the tools that we use now to find bugs, such as static analysis and test
automation. There are also thousands of these games, and emulators let us run
and inspect them.

A shipped cartridge did not get online updates, but it was not always the last
version either. Some games got cartridge revisions that fixed bugs, and
sometimes a revision broke other things or changed a feature. Releases for
different regions were often built from different snapshots of the code. I
think we have only started to understand the differences between all these
versions.

Some of what shipped stayed hidden for a long time. Every cartridge of
GoldenEye 007 (Nintendo 64, 1997) contains a ZX Spectrum emulator with ten of
Rare's Spectrum games. Rare made it as an experiment and disabled it, but did
not remove it, and players found it in 2012, 15 years after release. The game
also still contains a character select screen for the earlier Bond actors,
which you can only reach with a cheat device.

Developers also put in button codes and debug features that they never
disclosed, or that they forgot about. Homefront: The Revolution (2016) contains
a full port of TimeSplitters 2 that a code unlocks. In 2021, the programmer who
added it said that the code was lost with his notebook. Four days later, a
player who had kept the code from an old message posted it, while a modder was
already reverse-engineering the game's menus to find it. In Alien Resurrection
(PlayStation, 2000), a programmer added a code that lets you swap in another
disc without a reset. It was a test, and he did not tell the other developers
or Sony. He revealed it in 2023, 23 years later.

This is the part that gets me most excited. Every game that shipped is a
snapshot of code that somebody wrote under a deadline, and most of that code
has probably never been read by anyone outside the team that wrote it. Even
with sites like The Cutting Room Floor documenting so much, there are
probably debug menus, cheats, unused features and bugs in thousands of games
that nobody has found yet. Add every revision and every regional release, and
the pile only gets bigger. We have barely scratched the surface.

Some well-known behaviors started as bugs. In Super Mario Bros., Lakitu was supposed to
throw Spiny eggs with some physics: the throw depended on Mario's speed and
position, and the eggs bounced off walls. A bug makes the eggs drop straight
down. For decades, players knew that as normal Lakitu behavior. In Street
Fighter II, you can cancel a normal attack into a special move. This came from
code that made special-move inputs easier. Capcom saw it during development and
kept it.

<figure>
  <img src="/assets/images/20261002/lakitu-eggs.png" alt="Schematic: on the left, Lakitu's egg follows an arc ahead of Mario and bounces off a block, as the throw code intends. On the right, the egg drops straight down under Lakitu, as in the shipped game.">
  <figcaption>The Lakitu bug, drawn from the description on The Cutting Room Floor.</figcaption>
</figure>

Bugs that nobody noticed are hard to find, because no document shows what the
developers intended. The only evidence is in the code, where two parts of the
code disagree. Often the bug occurs in one configuration only: one controller
instead of two, a multitap connected or not, a different region, different
timing. To find one, you must know the game well enough to see that something
is different. Then you must test each configuration and compare the results. A
person can do this for one or two theories, but it is slow work.

An emulator with good instrumentation makes this easier. You can save a state,
play the same input in different configurations, record the RAM in every frame,
and compare the runs. An agent can do this for many configurations and many
save states, and it does not get tired of comparing memory dumps. With an
agent, you can search for these bugs before you have a theory.

<figure>
  <img src="/assets/images/20261002/ab-runs.png" alt="Diagram: one save state runs twice, once with a TurboTap and once with one pad, with the same input. The triangles' state is the same in frames 30 to 32 and different from frame 33. The trace back finds $26: $00 in run A and $80 in run B.">
  <figcaption>The method, applied to the Parasol Stars bug that the rest of this post explains.</figcaption>
</figure>

The example below is from a remake project of mine. I saw a difference in
difficulty, and an agent found the cause.

<figure>
  <img src="/assets/images/20261002/01-same-inputs.png" alt="Two rows of screenshots from Parasol Stars round 1-5 at 10, 25 and 50 seconds. With a TurboTap the triangle enemies stay inside their brick maze; with one pad they leak out through the walls.">
  <figcaption>Same save state, same input (player 1 holds LEFT). The only difference is the controller configuration.</figcaption>
</figure>

## The project

I am remaking Parasol Stars (Taito, PC Engine, 1991) in Godot, and the remake
must behave like the original. Agents read the original HuC6280 code and write
the same logic in GDScript. A lock-step harness then runs the remake and the
original ROM side by side in an emulator and compares the game state in every
frame.

<figure>
  <img src="/assets/images/20261002/remake-round-1-5.jpg" alt="Round 1-5 of the remake in two graphics modes: CLASSIC with the original pixels, and REMASTER with new art. The maze and the ten triangles are in the same places.">
  <figcaption>Round 1-5 in the remake. The graphics mode changes the art. The game logic is the original's.</figcaption>
</figure>

Round 1-5 is a brick maze with ten triangle enemies that fly inside it. There
are four water dispensers on the roof. The room is designed for one method:
wait until the triangles are together, then flood the maze. In the remake, the
triangles went out through the walls and chased me, and a flood never cleared
the room. I did not remember the original being this hard.

I played the original in an emulator. The triangles stayed in the maze, except
for some short trips through the maze's openings. One flood from the roof
removed all of them.

The first theory was that the remake had the wrong enemy speeds. The agent
measured the player and the triangles in both versions. The speeds were the
same to the sub-pixel: 1 pixel per frame, and 2 when the triangles are angry.

The difference was the controller configuration. The remake was built against
an emulator harness with no multitap, so it used the behavior of one pad
connected directly to the console. My emulator had the multitap enabled.
Nobody had compared the two configurations, and the game behaves differently
in each one.

## The hardware

Each home PC Engine and TurboGrafx-16 has one controller port. The game reads
it through a 4-bit register at `$1000`. Bit 0 (SEL) selects which half of the
pad answers: the four directions or the four buttons. Bit 1 (CLR) is a reset
line.

The TurboTap (NEC's multitap) connects to that port and has five sockets. A CLR
pulse resets it to socket 1. Each change of SEL from 0 to 1 moves it to the
next socket. This is how one port reads five controllers. A pad that is
connected directly to the console has no sockets to step through. It answers
every read.

<figure>
  <img src="/assets/images/20261002/02-five-questions.png" alt="Diagram: the game asks ports 1 to 5 for buttons. With one pad, every port answers with pad 1. With a TurboTap, port 1 is pad 1 and ports 2 to 5 are empty sockets.">
  <figcaption>Without a TurboTap, the one pad answers all five reads.</figcaption>
</figure>

Bank 0 `$E19B` reads the controllers in every frame. It resets the tap. Then,
for each of the five ports, it reads the directions and the buttons, combines
them into one byte, inverts the byte (the pad sends 0 for pressed), and stores
it. Port 1 goes to `$244D` and port 5 goes to `$2451`. The routine does not
check if a TurboTap is present.

<figure>
  <img src="/assets/images/20261002/03-reading-a-pad.png" alt="Annotated disassembly of the pad read routine at E19B, the eight bits of a controller byte (LEFT is $80, II is $02), and the five held-button bytes $244D to $2451 with port 2 at $244E marked.">
  <figcaption>Holding LEFT sets bit 7, so the byte is $80. Port 2's byte is at $244E.</figcaption>
</figure>

So with one pad, ports 2 to 5 hold player 1's buttons.

## How $26 is used

Three routines use the zero-page byte `$26` in each frame. (The HuC6280 zero
page is at `$2000`, so for a watchpoint the address is `$2026`.)

1. Player 1's routine writes port 1's held buttons to `$26`.
2. Player 2's routine writes port 2's held buttons to `$26`. This routine runs
   in every frame, even when there is no player 2, because it checks if a
   second player wants to join.
3. The enemy routines run. The wall tests of the flying enemies (`$6645` for
   movement to the right, `$66BC` for movement to the left) read `$26` as a
   counter. They read it before they write it.

<figure>
  <img src="/assets/images/20261002/04-one-frame.png" alt="Four steps in one frame: read the pads, player 1's turn writes port 1 into $26, player 2's turn writes port 2 into $26, the enemies move and the flyers' wall test reads $26 as a row counter.">
  <figcaption>The player code uses $26 for held buttons, and the wall test uses it as a counter.</figcaption>
</figure>

When the enemy routines run, `$26` holds port 2's buttons. With one pad and no
TurboTap, port 2 reports your own buttons. In a two-player game, it reports
player 2's buttons. The walls work correctly only when port 2 reports no
buttons (for example, a TurboTap with one player).

<figure>
  <img src="/assets/images/20261002/05-what-is-in-26.png" alt="The byte $26 shown as eight bits in three setups: TurboTap alone gives $00 and the walls hold; one pad with LEFT held gives $80 and triangles slip; TurboTap with player 2 holding RIGHT gives $20 and triangles slip.">
  <figcaption>A held direction gives a large count (LEFT is 128). That is enough for all the wall tests in the frame.</figcaption>
</figure>

## The wall test

A triangle is 10 pixels high. When it moves, the wall test checks two rows of
the 8x8 collision grid in the column in front of it: the row of its head, and
the row below.

The counter is for one special case. When the head of a flying enemy is above
the top of the map, the rows above the map do not exist. The routine sets
`$26` to the number of missing rows and reads row 0 again for each of them. In
all other cases, the routine does not set `$26`. It expects `$26` to be 0.

```
row = head_y / 8                 ; $26 is only set when the head is above the map
repeat (height + 7) / 8 times:   ; 2 rows for a triangle
    if map[column][row] is a wall:  return WALL
    if $26 > 0:  $26 = $26 - 1      ; for rows above the map: read row 0 again
    else:        row = row + 1
return NO WALL
```

If `$26` is not 0, the test reads the head row again instead of the next row.
It does not check the row below, so it does not detect a wall that touches
only the lower half of the triangle.

<figure>
  <img src="/assets/images/20261002/06-wall-test.png" alt="Two schematic grids. With $26 = $00 the test reads the head row (empty) then the row below (wall) and the triangle turns back. With $26 = $80 it reads the head row twice and the wall in the row below is never read.">
  <figcaption>With $26 = $80, the test reads the head row two times and does not read the row below.</figcaption>
</figure>

## The first frame that differs

The agent ran the original two times from the same save state with the same
input: one time with a TurboTap and one time with one pad. Player 1 holds
LEFT. The triangles move the same way in both runs until frame 33.

At frame 32, triangle 5 flies right and down. Its wall test reads column 44.
Row 8 (the head) is empty, and row 9 has a step of the maze. With the
TurboTap, the test reads both cells, finds the step, and the triangle turns
back. With one pad, the test reads row 8 two times, and the triangle flies
into the step. Six frames later, it is inside the bricks.

<figure>
  <img src="/assets/images/20261002/07-the-moment.png" alt="Real frames from the original game at frame 32, annotated with the collision grid and the triangle's hitbox. With the TurboTap the test checks an empty cell then a wall; with one pad it checks the empty cell twice. At frame 38 the one-pad triangle is inside the wall.">
  <figcaption>Frame 32 is the same in both runs. The value in $26 is the only difference that matters.</figcaption>
</figure>

## Measurements

All measurements are on the original ROM in the emulator, from the round 1-5
save state:

| Test | TurboTap | One pad |
|---|---|---|
| Player 1 holds LEFT, 4000 frames | 4 of 10 leave for short times; outside the maze 1.8% of the time | 9 of 10 get out; outside the maze 75.5% of the time |
| Random input, 8 seeds | the same short trips, 1.8% | 8 to 10 get out; outside the maze 31-53% of the time |
| Player 1 does nothing, pad 2 holds LEFT, 3000 frames | 9 of 10 get out, the same frame for frame as one pad | |
| Random bot, 96 sessions each | 0 deaths in 480,000 frames | 741 deaths in 459,124 frames |

In the first three rows, the harness holds player 1 in one place and makes him
invulnerable, so only the triangles act. The input still goes to the pad, so
`$26` still gets it. The bot plays with 9 lives, and a session ends at game
over. This is why the frame totals are different. The 1.8% is the baseline:
the maze has openings, and the triangles go through them for short times even
when `$26` is 0.

I also tested a flood after 20 seconds of walking. In the original with the
TurboTap, the flood caught all ten triangles. The remake's one-pad model,
which matches the original's enemy logic frame for frame, caught two. The
other eight were already outside the maze.

A second player does not prevent the bug. In the third row, player 1 does not
press anything and pad 2 holds LEFT. The result is the same as with one pad.
In real two-player games (six saved states, including rounds with flying
enemies in other worlds), `$26` at the start of the enemy routines always
contains pad 2's byte.

<figure>
  <img src="/assets/images/20261002/08-port-two-decides.png" alt="Three frames at frame 1500: TurboTap with nobody on pad 2 keeps the triangles in the maze; TurboTap with pad 2 holding LEFT and one pad with player 1 holding LEFT both have triangles outside.">
  <figcaption>Port 2 decides the result, not player 1.</figcaption>
</figure>

Round 1-5 is not the only round where this happens. The section "The rest of
the game" below covers the other rounds.

## Why I call it a bug

Three things in the ROM show that the developers did not intend this behavior:

- The counter in the wall test has one purpose: rows above the map. All other
  paths through the routine expect it to be 0.
- The room is designed to be cleared with a flood. That works only if the
  triangles stay in the maze.
- On the title screen, bank 0 `$E204` checks for a TurboTap. It compares the
  new button presses on ports 1, 2 and 3. If you press RUN on a single pad, the
  press shows on all three ports, so the game sets its multitap flag `$2458` to
  0 and disables two-player games. The game knows that there is no TurboTap,
  but the wall test does not use that information.

<figure>
  <img src="/assets/images/20261002/09-the-game-knows.png" alt="Annotated disassembly of the title-screen TurboTap check at E204, which sets the multitap flag $2458, and two one-line fixes: STZ $26 at the start of the wall test, or skip the port-2 copy when $2458 is 0.">
  <figcaption>The title screen check uses the same hardware behavior that causes the bug.</figcaption>
</figure>

The fix is a two-byte `STZ $26` at the start of each wall test. My remake has
a FLYER WALL BUG option in the pause menu. FIXED is the default. ORIGINAL keeps
the shipped behavior: `$26` contains your buttons with one pad, and player 2's
buttons in a two-player game. The regression tests use ORIGINAL, so they still
match the ROM. An option for the controller type would not fix the bug,
because with a TurboTap it still occurs when player 2 holds a direction.

<figure>
  <img src="/assets/images/20261002/remake-pause-menu.png" alt="The remake's pause menu, GAME tab, with FLYER WALL BUG set to FIXED and the hint: flying enemies stop at walls, as intended.">
  <figcaption>The option in the remake's pause menu.</figcaption>
</figure>

## How it probably shipped

This part is a guess. I think the developers tested mostly with a TurboTap
connected. The pce-devel controller notes say that all games were expected to
work with the multitap. With a TurboTap and one player, `$26` is `$00` when the
enemy routines run, the counter does nothing, and the walls work. To see the
bug, you must play with only the pad that came with the console and hold a
direction in a room with flying enemies. Even then, it looks like the enemies
are just difficult.

My emulator had the same configuration as that guessed test setup. That is why
the original looked correct to me and the remake looked wrong.

## Is it the emulator?

All the tests ran on the original ROM in an emulator, not on a console. These
are the reasons that I think a console behaves the same way:

- The TurboTap protocol is documented: CLR resets it and SEL steps it. I read
  the emulator's input code, and it does what the documentation says.
- The game's title screen check works only because a single pad answers on all
  ports. If the console did not do this, `$E204` would not see RUN on ports 2
  and 3.

The TurboTap screenshots show GAME OVER / CREDIT 1 for player 2. The save
state has the multitap flag `$2458` at 0 (one pad), and the harness enables the
tap after it loads the state. This does not change the result, because the
copy from port 2 does not check that flag.

I did not find this bug described anywhere else. I would like someone to test
it on a console. If you have a PC Engine or TurboGrafx-16, one pad and
Parasol Stars, go to round 1-5, hold LEFT for 20 seconds, and watch the
triangles. You will see some short trips through the maze's openings even with
a TurboTap. With the bug, triangles fly into the bricks.

## The rest of the game

Round 1-5 is only where I noticed the bug. The same wall test runs for flying
enemies in many rounds, so the next question was where else it changes the
game.

The project has a save state for each round of the original, 78 in all. An
agent ran each one twice with the same input, once with a TurboTap and once
with one pad, and logged every read of `$26` and `$27`. With the TurboTap, every
read of the value that player 2's copy left there was 0. With one pad, the wall
test read the held buttons in 36 of the 78 rounds.

A stale read does not always change what you see. So one group of agents
measured each of the 36 rounds: the same save state and input with a TurboTap
and with one pad, for 3,000 to 9,000 frames, with A/B screenshots and a count of
the frames where a flyer's hitbox centre is inside a wall. A second group re-ran
every measurement with its own scripts and tried to refute each verdict. The
verifiers reproduced the measurements, corrected a few descriptions, and changed
some verdicts: two rounds went up from subtle to visible, and one went down.

<figure>
  <img src="/assets/images/20261002/rounds-map.png" alt="A grid of all rounds, worlds 1 to 10 and rounds 1 to 8. 17 rounds are marked visible, 12 subtle, 6 with no change, and 42 not affected. Round 9-8 is marked as the same result as round 10-1.">
  <figcaption>Every round of the original, after the second check.</figcaption>
</figure>

After that check:

- In 17 rounds the difference is visible. Flyers clip into walls or fly
  through them, or reach places that they never reach with a TurboTap. In some
  rounds this only happens now and then.
- In 12 rounds the enemies' paths change, but nothing looks wrong.
- In 6 rounds the game plays the same.

<figure>
  <img src="/assets/images/20261002/round-10-1-ab.png" alt="Round 10-1 at frame 242, TurboTap on the left and one pad on the right. With one pad, a purple blob is above the top wall, over the score display.">
  <figcaption>Round 10-1. With one pad (right), a blob leaves its pocket and gets out above the map. With the TurboTap it stays in the pocket.</figcaption>
</figure>

<figure>
  <img src="/assets/images/20261002/round-7-3-ab.png" alt="Round 7-3 at frame 2384, TurboTap on the left and one pad on the right. With one pad, the sky cow is inside a magenta block, marked with a red box.">
  <figcaption>Round 7-3. With one pad (right), the sky cow goes through a block and leaves its pocket.</figcaption>
</figure>

The search found two more things.

The bug is not only about controllers. Even with a TurboTap, a flyer's wall
test can start with a value that other code left in `$26`. When a flyer's head
is above the top of the map, the wall test sets `$26` to the number of rows
above the map, and part of that count can stay there after the test ends. The
routine that moves the flyers (bank 6 `$6CB6`) also leaves values in `$26`.
Nothing clears the byte between two flyers' wall tests.

I compared the original with a version that clears `$26` at the start of each
wall test, both with a TurboTap and no input, for 9,000 frames. In five rounds, flyers end up inside
walls only in the original: 9-2 (397 frames against 0), 8-6 (149 against 0),
2-2 (109 against 0), 2-4 (38 against 0) and 6-6 (26 against 0). A second agent
checked each case: every time, the flyer had just skipped a wall cell because
of the stale value. These are the green dots on the map.

Player 2's join check reads `$27`. On a normal console with one pad, nothing
happens, because the game turns off joining when it does not find a TurboTap on
the title screen. But if a TurboTap was there on the title screen and stops
answering later (unplugged during play, or an emulator's multitap switched
off), the RUN press that unpauses the game also joins player 2. The credit
goes, Bobby comes in, and pad 1 then moves both characters. I only tested this
in the emulator.

In two-player games, the flyers' wall test is the only code outside the player
routines that reads player 2's buttons.

This is the part that I could not have done by hand in any reasonable time: 78
rounds, two setups and three inputs, thousands of frames each, and then a
second pass to check every result. The agents took a little over an hour for
all of it.

## The bug class

This bug is an example of a general class. Old consoles keep temporary values
in a small set of fast, shared bytes (the zero page on the 6502 family). One
routine leaves a value in a shared byte. A later routine reads that byte before
it writes it. Here, the player code uses `$26` for "buttons held" and the wall
test uses it for "rows to repeat". The problem shows only in a configuration
that, I think, the developers rarely tested.

<figure>
  <img src="/assets/images/20261002/10-stale-scratch.png" alt="The stale-scratch pattern in four steps, and four ways to hunt for it: log the first access to each zero-page byte per routine, find the last writer, vary rarely changed conditions, and diff runs frame by frame.">
  <figcaption>The bug class, and a method to find it in other games.</figcaption>
</figure>

The method to find this class of bug:

1. Log the first access to each zero-page byte in each routine. A read before
   any write is a candidate.
2. For each candidate, find the code that wrote the byte last. Then find what
   changes the value: input, hardware or game state.
3. Change the configurations that the developers rarely changed: controller
   setup, empty ports, region, timing.
4. Run the same input two times with one change, and compare the game state
   frame by frame. Examine the first frame that is different.

## What the agent did, and its mistakes

I could have done all of this by hand. It would have been grueling, and it
would have taken a lot of time that I do not have, even for one game, let alone
a whole shelf of them. The agent did that work. It measured the speeds to
remove the first theory. It ran A/B tests with one change at a time. It ran 192
bot sessions (939,124 frames). It found the first frame where the two runs are
different, and it traced `$26` back to the routine that wrote it. Being able to
hand that work off and see what it uncovers is very cool.

It also made mistakes:

- An early summary said that with a TurboTap, none of the ten triangles leave
  the maze. The data shows four triangles that leave for short times, 1.8% of
  the time.
- A draft of the infographics said that the button you hold does not matter.
  That was wrong: button II alone gives a count of 2, and the wall test of the
  first flying enemy uses it up. The draft generalized from tests that did not
  include that case.
- The one-pad behavior in the remake was the agent's decision. It kept the
  behavior of the test harness and did not compare it with my emulator
  configuration. That made the remake harder than I expected.
- The first sweep script missed some memory accesses, so one routine looked
  like it read the stale buttons when it did not. A verifying agent found the
  problem, and the corrected sweep found the same 36 rounds.

We found each mistake when we checked the claim against the logged data.

After that, I had the agent turn the explanation work into a skill. It takes a
bug that you understand and makes a set of pictures from the evidence: real
frames from the original, and diagrams where each number comes from a
measurement.

Then an agent built the search part as a tool. It traces every memory access
in the emulator, finds the reads in each routine that come before a write,
ranks them, and tests the best candidates with A/B runs that change one
condition. As a test, it had to find the `$26` bug with no hint. It ranked the
two wall-test reads first and second out of 2,474 candidates, in about 13
seconds. Run over every round, it also found the leftover count described
above.

The tool still makes mistakes. In round 1-5 it marked the player's state byte
as a confirmed problem, but that byte only changed because the escaped
triangles hit the player. A person still has to read what it finds.

## Outside games

My day job is finding issues in software, mostly not in games, and this is
what excites me about it. I see the same kind of bug in large code bases: a
value that one part of the code leaves behind and another part trusts, in a
configuration that nobody tests. Those code bases are big, strange and full of
odd edge cases, and nobody can keep all of their variations in their head.
Agents are getting better at taking one systemic cause like this and checking
every place where it shows up. Each time that gets better, we find more
unintended behavior that has been sitting there for years, and that is
exciting.

If you remember this room being very hard on a console with one pad, or if you
know of other bugs like this, I would like to hear about it.

---

*Sources: the Lakitu egg behavior is documented on
[The Cutting Room Floor](https://tcrf.net/Super_Mario_Bros.) (summarized by
[Nintendo Everything](https://nintendoeverything.com/how-lakitu-throws-spiny-eggs-in-super-mario-bros-is-due-to-a-glitch-not-the-intended-behavior/)).
The Street Fighter II cancel story comes from its designers, in
[Game Developer](https://www.gamedeveloper.com/business/-i-street-fighter-ii-i-designer-opens-up-about-the-cancelling-bug-).
The GoldenEye details are from
[Wikipedia](https://en.wikipedia.org/wiki/GoldenEye_007_(1997_video_game)) and
[Nintendo Life](https://www.nintendolife.com/news/2012/03/wait_theres_a_spectrum_emulator_in_goldeneye).
The TimeSplitters 2 story is from
[Kotaku](https://kotaku.com/someone-recovered-the-code-to-unlock-a-full-version-of-1846655103) and
[Tech Times](https://www.techtimes.com/articles/258927/20210409/timespliiters-2-easter-egg-code-finally-cracked-homefront-revolution.htm),
and the Alien Resurrection code from
[Time Extension](https://www.timeextension.com/news/2023/12/23-years-later-ps1-alien-resurrections-naughty-piracy-cheat-code-is-revealed).
The TurboTap protocol and the multitap expectation are from pce-devel's
[PCE_Controller_Info](https://github.com/pce-devel/PCE_Controller_Info). The
emulator's model of the TurboTap is in the input code of
[Geargrafx](https://github.com/drhelius/Geargrafx). All measurements are from
the original ROM in an emulator harness, except the one-pad flood result,
which comes from the remake's model as noted above.*
