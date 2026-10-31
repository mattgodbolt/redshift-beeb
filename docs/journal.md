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

## 2026-10-31: the first room on screen

- `tools/mkgfx.py` and `tools/mkrooms.py` turn the text art and rooms
  into data, with PNG previews in `build/preview` that render each room in
  both phases, bands and all.
- The room packs as tiles, runs, and runs copied from the row above.
  The first room fits in under 200 bytes.
- The first boot hung in `load_room`: `rd_byte` returned the flags of its
  pointer's `INC`, not of the byte, so the name loop never saw its 0.
  Then the status text was garbled: `print_char_a` leaves Y at &FF, and
  the string loop indexed with it.
- Bands and the phase shift work as planned. SHIFT recolours every band
  and redraws only the phase tiles (`draw_room_phase`).

## 2026-10-31: Ash moves

- `render.6502`: each changed thing's old and new rectangle grows to take
  in anything it touches, is composed in the buffer (tiles, then sprites
  masked in slot order), and is copied out. Walking and firing hold 25
  frames a second (50 frames in 100 VSyncs).
- `player.6502`: walking, a jump table, falling with gravity, crouching,
  bolts, hazards, and room exits. The phase shift is refused if it would
  put Ash inside something solid.
- Bugs met: two more of the same kind as `rd_byte`'s. A load after a
  routine set the flags its caller tested: `LDX sh_x` after `test_area`
  made every bolt hit at once. Branches out of range were fixed with `JNE`
  and an inverted branch.

## 2026-10-31: things

- `things.6502`: sentries (armoured, fire along their row), drones (bob
  and turn at walls), crawlers (turn at walls and at the floor's end),
  shards (home in), pickups, the grenade's arc and blast (which also
  clears breakable tiles), and enemy bolts. `tools/mkgfx.py` makes each
  phase enemy's ghost, and mirrored copies only of sprites flagged
  `mirror`.
- A trap avoided: after tiles are drawn over things (a blast, a phase
  shift), forgetting what's on screen would leave a trail where a moving
  thing was. They're marked changed instead (`objs_touch`), so both
  rectangles are redrawn.
- The low pages filled up. The interrupt's page-aligned tables now come
  first, and the compose buffer is 768 bytes.
- Memory is getting short below the screen: about 4K is left.
