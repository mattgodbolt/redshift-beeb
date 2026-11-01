# REDSHIFT level editor

Make REDSHIFT's rooms in a browser, no programming needed:
https://mattgodbolt.github.io/redshift-beeb/editor/

To keep your rooms, press **Download rooms.txt**. To play them, put the file
in place of `rooms/rooms.txt` in your own copy of the repo and build it (the
top-level README says how).

To run it locally, serve the repo's root (`python3 -m http.server`) and open
http://localhost:8000/editor/. It reads `gfx/tiles.txt`, `gfx/sprites.txt`,
`rooms/rooms.txt` and `tools/mkrooms.py`, and keeps your work in the browser.

`node editor/check.mjs` checks it against the real files and
`tools/mkrooms.py`: `rooms.txt` must survive a load and a save byte for byte,
every room must draw exactly as `render()` does, in both phases and every
state its machinery has (on the beat, thrown), and the editor must find
problems in just the rooms that `mkrooms.py` refuses.
