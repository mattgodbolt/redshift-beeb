# REDSHIFT level editor

Make REDSHIFT's rooms in a browser, no programming needed:
https://mattgodbolt.github.io/redshift-beeb/editor/

To send in your rooms, press **Download rooms.txt**. Then either commit it
as `rooms/rooms.txt` in a pull request, or send the file to Matt.

To run it locally, serve the repo's root (`python3 -m http.server`) and open
http://localhost:8000/editor/. It reads `gfx/tiles.txt`, `gfx/sprites.txt`,
`rooms/rooms.txt` and `tools/mkrooms.py`, and keeps your work in the browser.

`node editor/check.mjs` checks it against the real files and
`tools/mkrooms.py`: `rooms.txt` must survive a load and a save byte for byte,
every room must draw exactly as `render()` does, and the editor must find
problems in just the rooms that `mkrooms.py` refuses.
