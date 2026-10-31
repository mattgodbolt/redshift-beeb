# Journal

What was done, in order, with what worked and what didn't.

## 2026-10-31: the start

- Matt asked for a game in the style of Exolon. It's an original game in
  that genre rather than a port, so it has its own name, story, art, map
  and rules. From three pitches Matt picked REDSHIFT, whose signature is
  a phase shift done with the palette (`BRIEF.md`).
- Matt pointed at Chuckie Egg 2's look, MODE 1 with palette bands from
  interrupts, over Scorched Earth's MODE 2. The interrupt handler follows
  CE2's `irq.6502` up to each write, so its measured timing carries over.
  CE2's fixed band splits become a list of per-line changes of one
  logical colour each.
- The art and the rooms are text files (`gfx/`, `rooms/`), read by the
  Python tools and, later, by the level editor.
