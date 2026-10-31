# REDSHIFT for the BBC Micro

*Future home of* an original flip-screen run-and-gun game for the BBC
Micro (Model B and Master 128), in 6502 assembly.

> Kharon-4, 2189. The colony's deep mine broke into the Prism, an alien
> engine that splits reality in two. The Red Phase is overrun by the
> Prism's war machines; the Blue Phase by its crystal swarm. Trooper Ash
> Calder wears the last working phase harness. Fight down through five
> sectors and shut the Prism off.

### ▶ [Play it in your browser](https://bbc.xania.org/?disc=github:mattgodbolt/redshift-beeb/redshift.ssd&autoboot)

So far: the first room, with Ash walking, jumping and firing. Try to
get across the acid. Then press **SHIFT**.

| Key | Does |
|---|---|
| Z / X (or ← →) | left / right |
| : (or ↑) | jump |
| / (or ↓) | crouch |
| RETURN | fire |
| SHIFT | flip the phase |

## The idea

- **SHIFT flips the phase.** Every palette band on the screen swaps at
  once, from the Red Phase's warm reds and yellows to the Blue Phase's
  cold blues and cyans. Blocks and enemies that belong to the other phase
  become dotted outlines: you walk through them, and they can't hurt you.
- A blaster, and grenades that crack armour and breakable walls.
- MODE 1 at 256x192 with palette bands driven by interrupts, after
  [Chuckie Egg 2](https://github.com/mattgodbolt/chuckie-egg-2-beeb)'s, so
  each band of a room has its own four colours.
- A level editor in the browser, so anyone can make rooms (coming soon).

## Building it

[baron](https://github.com/waitingforvsync/baron) 0.6, Python 3 with
Pillow, and Node for the test harness (jsbeeb through
[jsbeeb-mcp](https://www.npmjs.com/package/jsbeeb-mcp)).

```sh
npm install
make            # build/redshift.ssd
make run        # boot it in jsbeeb, screenshot to shots/run.png
```

## Where things are

- `BRIEF.md`: where it started.
- `docs/journal.md`: what's been done, in order. `docs/decisions.md`:
  every design call, numbered.
- `gfx/tiles.txt`, `gfx/sprites.txt`: the art, as text.
- `rooms/rooms.txt`: the rooms, as text.
- `src/`: the game. `tools/`: the converters and the test harness.
