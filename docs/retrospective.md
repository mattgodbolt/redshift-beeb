# Retrospective

REDSHIFT was built between 31 October and 5 November 2026. Matt asked for
a game in the style of Exolon, picked one of three pitches, and handed over
more of the design as it went, until the last sectors were the game's own
to make. This looks back at what worked, what didn't, and what we'd do again.
The day-by-day story is in `journal.md` and every design call is in
`decisions.md`.

## What it came to

Forty-five rooms in five sectors, the boss (THE HINGE) and two endings. Two
phases, the Red and the Blue, are swapped with the palette in a frame. A
teletext title page has its own theme, and each sector has music in both
phases. It runs on a Model B with 16K of sideways RAM, or on a Master, and
loads one sector at a time from the disc. A level editor reads the same files
as the build, and an end-to-end test plays the whole game from the title page
to the ending and on into a new game.

## What worked

**The signature came first and stayed cheap.** The phase shift is a change of
palette, plus a redraw of only the tiles that belong to a phase. The interrupt
handler's timing came from chuckie-egg-2-beeb, where it had already been
measured, so the bands worked on the first boot. Everything later stood on
that one trick: the ghosts, the Blue's music a semitone up, the Hinge's
two-picture tiles, and the band that pulses blue to point at the shift.

**Everything is text.** Art, rooms, tile rules and music are all plain text
files, read by small Python tools and by the editor. That meant:
- an agent could design a sector in the same files a person would edit;
- a diff showed what a room's change was;
- the editor's check could hold its drawing to the build's, pixel for pixel.

Writing the scores as grids, a token a semiquaver, let a tool check every
bar's length before a note was played.

**Newcomers found what reading never would.** For each sector, a fresh agent
played from screenshots, with no map and no source. That did more for the
game than anything else. Nearly all of what they found wasn't a bug. It was
something that read as something it wasn't:
- a helmet that read as a beak, and a sergeant as a duck;
- cracks that read as exit chevrons, and ghosts that read as gems;
- a plate that read as trim, and a crack that read as a shield that grows
  back.

The rule that each colour has one job (decision 20) came out of one such
comparison, and it held to the end.

**Proving rooms with a simulation.** A small Python model of Ash's jump and
fall, run over a room's map from every x, found traps before the emulator
did. It also proved that a room needed what it was meant to need, in each
phase and in each state of its machinery. The habit grew a list of lessons
(the "prove a room" entries in `CLAUDE.md`), each from a jump that went
somewhere unexpected.

**The playthrough as the test.** `make playthrough` began as a run through
Sector 1 and ended as the whole game. It plays every route on both machines,
through each sector's load from the disc. It broke often, and nearly every
break was real: a rule had changed what a room allowed, such as the shift
margin, a gun's gap, or a Sliver's aim.

**Fairness rules, made once and kept:**
- a safe spell after a respawn;
- a death leaves two cells and a grenade;
- Slivers hang still out of phase;
- a shift is refused into the new phase's hazards, or next to its enemies;
- after a respawn, Ash ignores the direction keys until they're let go.

Each came from a death a player hadn't earned. Each is a numbered decision,
so later rooms could be checked against it rather than re-argued.

## What didn't

**6502 flags, again and again.** The same mistake came up repeatedly: a load
after a call, setting the flags the caller then tested. It first hung the
first boot, then made every bolt hit at once, and kept coming back. Writing
it at the top of the traps list helped. Wrapping such calls by habit would
have helped more.

**Memory decisions came in steps.** First the art went to sideways RAM. Then
the bank filled, so rooms were loaded a sector at a time. Then each sector
got its own looks. Each step was right when it was taken, but each one meant
re-plumbing. Designing the sector load from the start would have saved two
rounds. The DFS's traps took the longest of any problem: it trusts its
catalogue while the drive spins, and it wants its workspace back as it left
it. Compressing the rooms with LZ was tried and saved nothing. The existing
run-and-copy packing was already better, and the sprites were always most
of the bank.

**Rules added late broke routes.** The shift margin (decision 51) was right,
but it came after three sectors' routes had been scripted. Some of those
routes had shifted next to enemies that the new rule now counted as too
close. Some rooms had to be reworked because of it. Fairness rules want
settling before rooms are built against them.

**The boss took three passes.** The first Hinge could be beaten but taught
nothing: every wrong hit looked like hitting a wall. The second made the
armour answer back, with a ring, a flicker of the right look, and damage
that stays. The third pointed the Red at the Blue. A boss is mostly
feedback, and that should have been designed first, not its attacks.

**Parallel agents and merges.** Sectors, passes and polish were often built
in parallel worktrees. That was fast, but the merges cost. One merge left
conflict markers in the README, and they were pushed before a later pass
caught them. Binary stills conflicted whenever two branches retook them.
Scripted routes name things by their place in a room's list, so adding a
thing anywhere but the end renumbered every route after it.

**Reports need checking.** A playtester put one death down to the steam in
the Blue. It was a Sliver. Matt ran out of shifts on THE CATWALKS, where two
are enough. Reproducing each report in the harness before changing a room
kept rooms from being "fixed" for the wrong reason.

**Friction outside the game.** Long autonomous stretches kept stopping for
permission prompts on ordinary commands, and twice for spending limits.
Agents' work in flight was saved as work-in-progress commits each time, and
nothing was lost. Keeping commands short and file-based, and using message
files for commits, cut the prompts down.

## What's left open

- A Gadfly at head height can still touch a player who shifts right beside
  it, for part of its bob.
- THE DARK FRINGE's last pair of Slivers can be walked past.
- Stepping off the Hinge's pillar to the right in the Blue drops Ash into
  the pit.
- A shift during the plate's flicker can show the wrong plate for a frame.
- Decisions 50 to 63 were made while Matt was away, and are provisional
  until Matt has looked at them. The biggest is that ghosts are drawn
  entirely in the body colour, which changed every sector's look.

## What we'd do again

- Pick the signature mechanic first, and make it cheap.
- Keep every asset in text, with one reader shared by the tools and the editor.
- Have a newcomer play each new piece cold, from screenshots, and fix what
  they misread before what they couldn't do.
- Prove rooms with a model of the player's movement.
- Keep one end-to-end test that plays the whole game, and run it on every
  change.
- Number every design call, so a later change can name what it overrides.

## Thanks

To Matt, for the brief, the push towards Chuckie Egg 2's look, the reports
from playing it, and handing the game over. To chuckie-egg-2-beeb, for the
interrupt timing. To baron, the assembler. To jsbeeb, which ran every frame
of every test.
