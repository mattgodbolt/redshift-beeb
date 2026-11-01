#!/usr/bin/env node
// Checks the level editor (editor/index.html) against the real files and tools/mkrooms.py:
//
//   node editor/check.mjs [rooms.txt]
//
// - rooms.txt survives a load and a save byte for byte, and rooms written afresh read back the same;
// - every room draws, in both phases, pixel for pixel as mkrooms.py's render() draws it;
// - the editor finds problems in just the rooms that mkrooms.py (or gfxlib's reader) refuses;
// - it counts the looks shared and each sector's own as gfxlib's Looks does (decision 43);
// - the editor's copy of THING_TYPES matches mkrooms.py's.
//
// It runs the page's core script (<script id="core">) as it is. The drawing and the mkrooms.py
// checks need python3 with Pillow, and are skipped without it.
import {mkdtempSync, readFileSync, rmSync, writeFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import vm from 'node:vm';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const html = readFileSync(path.join(here, 'index.html'), 'utf8');
const ctx = vm.createContext({});
vm.runInContext(html.match(/<script id="core">([\s\S]*?)<\/script>/)[1], ctx, {filename: 'index.html'});
const RS = ctx.RS;

let failed = 0, skipped = 0;
function check(ok, what, detail = '') {
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${what}${!ok && detail ? '\n       ' + detail : ''}`);
  if (!ok) failed++;
}

const read = f => readFileSync(path.join(root, f), 'utf8');
const tiles = RS.parseTiles(read('gfx/tiles.txt'));
const tileMap = new Map(tiles.map(t => [t.key, t]));
const sprites = RS.parseSprites(read('gfx/sprites.txt'));
check(sprites.length > 0, `gfx/sprites.txt reads: ${sprites.length} sprites`);
const tmp = mkdtempSync(path.join(tmpdir(), 'redshift-editor-'));

// mkrooms.py, driven from outside: it reads only rooms/rooms.txt, so read_rooms is pointed elsewhere.
const PY = `
import json, sys, base64
sys.path.insert(0, sys.argv[1])
import gfxlib as g, mkrooms as m
mode = sys.argv[2]
if mode == 'ghosts':
    print(json.dumps({s.name: g.hollow(s.pixels) for s in g.read_sprites(ghosts=False)}))
elif mode == 'types':
    print(json.dumps([m.THING_TYPES, m.THING_BOX]))
elif mode == 'render':
    tiles = g.read_tiles()
    print(json.dumps([[base64.b64encode(m.render(r, tiles, p, scale=1).tobytes()).decode() for p in (0, 1)]
                      for r in g.read_rooms(sys.argv[3])]))
elif mode == 'looks':
    lks = g.Looks(g.read_tiles(), g.read_rooms(sys.argv[3]))
    print(json.dumps([len(lks.shared), {s: len(own) for s, own in lks.own.items()}]))
elif mode == 'build':
    real = g.read_rooms
    g.read_rooms = lambda p=sys.argv[3]: real(p)
    if len(sys.argv) > 5:
        real_tiles = g.read_tiles
        g.read_tiles = lambda p=sys.argv[5]: real_tiles(p)
    sys.argv = ['mkrooms.py', sys.argv[4]]
    try:
        m.main()
        print('ok')
    except BaseException as e:
        print(type(e).__name__, e)
`;
function py(...args) {
  const r = spawnSync('python3', ['-c', PY, path.join(root, 'tools'), ...args], {encoding: 'utf8', maxBuffer: 1 << 28});
  if (r.error || r.status !== 0) return {error: r.error ? r.error.message : r.stderr.trim().split('\n').pop()};
  return {out: r.stdout.trim()};
}
function skip(what, why) {
  console.log(`skip ${what} (${why})`);
  skipped++;
}

// What a room means, as against how it's written.
const meaning = doc => JSON.stringify(doc.rooms.map(r => [
  r.id, r.name.trim() || r.id.toUpperCase(), r.sector, r.exits, r.start, r.colours.map(c => [c.r, c.b]),
  r.bands.map(b => [b.line, b.logical, b.r, b.b]), r.map, r.things.map(t => [t.type, t.x, t.y, t.args]),
]));
function firstDiff(a, b) {
  const x = a.split('\n'), y = b.split('\n');
  for (let i = 0; i < Math.max(x.length, y.length); i++) {
    if (x[i] !== y[i]) return `line ${i + 1}: ${JSON.stringify(x[i])} became ${JSON.stringify(y[i])}`;
  }
  return '';
}

function roundTrip(text, label, expectFresh) {
  const doc = RS.parseRooms(text, label);
  const saved = RS.serializeRooms(doc);
  check(saved === text, `${label}: load then save gives it back byte for byte`, firstDiff(text, saved));
  const viaJson = RS.serializeRooms(JSON.parse(JSON.stringify(doc)));
  check(viaJson === text, `${label}: ...and after the JSON trip that undo and the browser's storage take`, firstDiff(text, viaJson));
  const fresh = RS.serializeRooms(doc, {canonical: true});
  check(meaning(RS.parseRooms(fresh)) === meaning(doc), `${label}: every room written afresh reads back the same`);
  if (expectFresh) check(fresh === text, `${label}: ...and gives it back byte for byte too`, firstDiff(text, fresh));
  return doc;
}

function compareDrawing(file, doc, label) {
  const res = py('render', file);
  if (res.error) return skip(`${label}: drawing against render()`, res.error);
  const want = JSON.parse(res.out);
  check(want.length === doc.rooms.length, `${label}: mkrooms.py reads ${want.length} rooms, the editor ${doc.rooms.length}`);
  doc.rooms.forEach((r, k) => [0, 1].forEach(phase => {
    const buf = RS.renderRoom(r, tileMap, phase, new Uint8ClampedArray(RS.WIDTH * RS.LINES * 4));
    const ref = Buffer.from(want[k][phase], 'base64');
    let bad = 0, first = -1;
    for (let i = 0, j = 0; i < ref.length; i += 3, j += 4) {
      if (ref[i] !== buf[j] || ref[i + 1] !== buf[j + 1] || ref[i + 2] !== buf[j + 2]) {
        bad++;
        if (first < 0) first = i / 3;
      }
    }
    check(ref.length === RS.WIDTH * RS.LINES * 3 && !bad,
      `${label}: ${r.id} in the ${phase ? 'Blue' : 'Red'} Phase draws as render() draws it`,
      `${bad} pixels differ, the first at ${first % RS.WIDTH}, ${Math.floor(first / RS.WIDTH)}`);
  }));
}

// The editor's errors against mkrooms.py's verdict, which is the one that counts: with tiles.txt, or
// the tiles given (their text).
function compareVerdict(text, label, tilesText = null) {
  const file = path.join(tmp, 'rooms.txt');
  writeFileSync(file, text);
  const tilesFile = path.join(tmp, 'tiles.txt');
  if (tilesText) writeFileSync(tilesFile, tilesText);
  const res = py('build', file, path.join(tmp, 'rooms.6502'), ...(tilesText ? [tilesFile] : []));
  if (res.error) return skip(`${label}: against mkrooms.py`, res.error);
  let mine;
  try {
    mine = RS.validate(RS.parseRooms(text), tilesText ? RS.parseTiles(tilesText) : tiles)
      .filter(p => p.level === 'error').map(p => p.msg);
  } catch (e) {
    mine = [e.message];
  }
  const theirs = res.out === 'ok' ? 'takes it' : `refuses it (${res.out})`;
  check(!mine.length === (res.out === 'ok'), `${label}: mkrooms.py ${theirs}; the editor ${mine.length ? 'says ' + mine[0] : 'finds no errors'}`);
}

// The looks shared and each sector's own, as the editor counts them (lookCounts) and gfxlib's Looks.
function compareLooks(file, doc, label) {
  const res = py('looks', file);
  if (res.error) return skip(`${label}: looks against gfxlib`, res.error);
  const want = JSON.stringify(JSON.parse(res.out)), mine = RS.lookCounts(doc, tiles);
  const got = JSON.stringify([mine.shared, Object.fromEntries([...mine.own].sort((a, b) => a[0] - b[0]))]);
  check(got === want, `${label}: the looks shared, and each sector's own, as gfxlib's Looks has them: ${got}`,
    `gfxlib says ${want}`);
}

// --- The real rooms -------------------------------------------------------------------------------

const roomsFile = path.resolve(process.argv[2] || path.join(root, 'rooms/rooms.txt'));
const label = path.relative(root, roomsFile);
const real = read(path.relative(root, roomsFile));
const doc = roundTrip(real, label, true);
for (const p of RS.validate(doc, tiles)) console.log(`     ${p.level}: ${doc.rooms[p.room] ? doc.rooms[p.room].id + ': ' : ''}${p.msg}`);
compareVerdict(real, label);
compareDrawing(roomsFile, doc, label);
compareLooks(roomsFile, doc, label);

const types = py('types');
if (types.error) skip('THING_TYPES', types.error);
else {
  const [list, boxes] = JSON.parse(types.out);
  check(JSON.stringify(list) === JSON.stringify(RS.THING_TYPES), `THING_TYPES matches mkrooms.py's: ${list.join(' ')}`);
  check(JSON.stringify(boxes) === JSON.stringify(RS.THING_BOX), "THING_BOX matches mkrooms.py's");
}

const ghosts = py('ghosts');
if (ghosts.error) skip('ghosts', ghosts.error);
else {
  const want = JSON.parse(ghosts.out);
  const bad = sprites.filter(s => JSON.stringify(s.hollow) !== JSON.stringify(want[s.name])).map(s => s.name);
  check(!bad.length, `every sprite's ghost is gfxlib's hollow() (${sprites.length} sprites)`, `differ: ${bad.join(' ')}`);
}

// --- Made-up rooms, for what the real ones don't have yet -----------------------------------------

// Every tile, split between alpha (Sector 2) and gamma (Sector 3): each is drawn, and each is one
// sector's own, so the two sectors' looks stay within what the game can number (decision 43).
const keys = tiles.map(t => t.key).join('');
const half = Math.ceil(keys.length / 2);
const keysOf = n => (n === 3 ? keys.slice(0, half) : ' ' + keys.slice(half));
const row = (k, n) => {
  const ks = keysOf(n);
  return Array.from({length: RS.MAP_W}, (_, i) => ks[(i * n + k * 7) % ks.length]).join('');
};
const map = n => Array.from({length: RS.MAP_H}, (_, k) => (k % 3 ? row(k, n) : row(k, n).replace(/ +$/, '')));
const blankMap = Array(RS.MAP_H).fill('');
const rich = [
  '# A header.', '', 'room alpha   # the first', 'name ALPHA ROOM', 'sector 2', 'exits left=- right=beta up=- down=gamma', 'start 3 10',
  'colours red yellow/white white', '# the sky', 'band 60 2 cyan', 'band 20 1 magenta/red   # out of order',
  'band 100 3 green', 'map', ...map(3), 'thing sentry 4 5 1', '# a pickup', 'thing cell 10 12',
  '# the cage, down to gamma in the next sector', 'thing exit 20 19', '',
  '# beta: no colours line, odd spacing, and blank map lines', 'room beta', 'name   BETA', 'exits  left=alpha',
  'map', ...blankMap.map((l, k) => (k === 21 ? '______' : l)), '',
  'room gamma', 'name GAMMA', 'sector 3 # deeper', 'exits up=gamma', 'start 20 18', 'colours blue green magenta', 'band 2 1 white', 'band 4 1 black',
  'band 175 3 red', 'map', ...map(5), 'thing shard 1 1', 'thing exit 29 19 0 extra', '', '# the end', '',
].join('\n');
const richDoc = roundTrip(rich, 'made-up rooms', false);
roundTrip(rich.replace(/\n/g, '\r\n'), 'made-up rooms with CRLF', false);
compareVerdict(rich, 'made-up rooms');
const richFile = path.join(tmp, 'rich.txt');
writeFileSync(richFile, rich);
compareDrawing(richFile, richDoc, 'made-up rooms');
compareLooks(richFile, richDoc, 'made-up rooms');

// An edit rewrites only the room it touches, and keeps that room's comments.
{
  const d = RS.parseRooms(rich), before = RS.serializeRooms(d).split('\n');
  d.rooms[0].map[4] = 'R' + d.rooms[0].map[4].slice(1);
  const after = RS.serializeRooms(d).split('\n');
  const diff = after.map((l, i) => (l !== before[i] ? i : -1)).filter(i => i >= 0);
  check(after.length === before.length && diff.length === 1 && after[diff[0]].startsWith('R'),
    'painting one tile changes one line of rooms.txt', `lines ${diff.map(i => i + 1).join(', ')} changed`);
  d.rooms[1].map[0] = '#' + d.rooms[1].map[0].slice(1);
  const text = RS.serializeRooms(d), again = RS.parseRooms(text);
  check(meaning(again) === meaning(d), 'an odd-looking room, once edited, reads back as edited');
  check(text.includes('# beta: no colours line') && text.includes('# the sky') && text.includes('# out of order'),
    'comments survive edits');
  check(text.split('\n').slice(0, 2).join('\n') === '# A header.\n', 'the header stays');
}

// The first room deleted: the next one doesn't bring a second blank line under the header.
{
  const d = RS.parseRooms(rich);
  d.rooms.splice(0, 1);
  const text = RS.serializeRooms(d);
  check(text.startsWith('# A header.\n\n# beta'), 'deleting the first room leaves the header tidy', JSON.stringify(text.slice(0, 40)));
}

// A new room, with a start, is one mkrooms.py takes.
{
  const d = RS.parseRooms(real);
  const r = RS.newRoom('fresh');
  r.start = [1, 1];
  d.rooms.unshift(r);
  const text = RS.serializeRooms(d);
  check(meaning(RS.parseRooms(text)) === meaning(d), 'a new room reads back the same');
  compareVerdict(text, 'a new room first');
}

// Each of these breaks one of mkrooms.py's rules (or gfxlib's reader), and both should say so.
const one = lines => ['room solo', 'name SOLO', 'start 1 1', ...lines.head || [], 'map', ...(lines.map || blankMap), ...lines.tail || []].join('\n') + '\n';
const broken = {
  'bands too close': one({head: ['band 40 1 red', 'band 41 2 red']}),
  'a band on line 1': one({head: ['band 1 1 red']}),
  'a band on line 176': one({head: ['band 176 1 red']}),
  'nine bands': one({head: Array.from({length: 9}, (_, k) => `band ${10 + 10 * k} 1 red`)}),
  'an exit to nowhere': one({head: ['exits left=nowhere']}),
  'a blank exit': one({head: ['exits left']}),
  'an unknown thing': one({tail: ['thing dragon 1 1']}),
  "a thing's arg that isn't a number": one({tail: ['thing sentry 1 1 x']}),
  'a key that isn\'t a tile': one({map: blankMap.map((l, k) => (k ? l : 'Q'))}),
  'two rooms with one id': one({}) + one({}),
  'no start in the first room': one({}).replace('start 1 1\n', ''),
  'an unknown colour': one({head: ['colours red pink white']}),
  'band logical 4': one({head: ['band 40 4 red']}),
  'a map line 33 wide': one({map: blankMap.map((l, k) => (k ? l : '#'.repeat(33)))}),
  'a short map': one({map: blankMap.slice(2)}),
  'an unknown line': one({head: ['colour red red red']}),
  'sector 6': one({head: ['sector 6']}),
  'sector 0, inherited': one({head: ['sector 0']}) + one({}).replace('solo', 'duo'),
  'a sector line with no number': one({head: ['sector']}),
  'seven things': one({tail: Array(7).fill('thing cell 1 1')}),
  'a drone on row 0, bobbing off the top': one({tail: ['thing drone 4 0']}),
  'a sentry at x 31, off the right': one({tail: ['thing sentry 31 4']}),
  'a cage on row 20, off the bottom': one({tail: ['thing exit 4 20']}),
  'a thing at x -1': one({tail: ['thing cell -1 4']}),
  // (Rooms load a sector at a time, so only a cage's down exit leaves one, to the next.)
  'an exit to another sector': one({head: ['exits right=duo']}) + one({head: ['sector 2']}).replace('solo', 'duo'),
  'down to the next sector with no cage': one({head: ['exits down=duo']}) + one({head: ['sector 2']}).replace('solo', 'duo'),
  'a cage down two sectors': one({head: ['exits down=duo'], tail: ['thing exit 4 4']}) + one({head: ['sector 3']}).replace('solo', 'duo'),
  'a cage back to the sector before': one({head: ['sector 2', 'exits down=duo'], tail: ['thing exit 4 4']})
    + one({head: ['sector 1']}).replace('solo', 'duo'),
};
check(compareVerdictOk(one({})), 'a plain room is fine by the editor');
compareVerdict(one({tail: ['thing drone 4 1', 'thing crawler 30 20', 'thing exit 30 19', 'thing cell 31 21', 'thing sentry 0 0', 'thing shard 5 5 1']}),
  'six things, each just fitting');
compareVerdict(one({head: ['exits down=duo'], tail: ['thing exit 4 4']}) + one({head: ['sector 2']}).replace('solo', 'duo'),
  'a cage down to the next sector');
for (const [what, text] of Object.entries(broken)) compareVerdict(text, what);
// A tile with as many looks as a sector can have, used only in Sector 2: too many for it, with the
// shared ones (decision 43).
{
  const art = Array(8).fill('.1.1.1.1').join('\n');
  const big = `${read('gfx/tiles.txt')}\ntile 7 big\n${art}\n` + `alt 7 base\n${art}\n`.repeat(RS.MAX_LOOKS - 1);
  compareVerdict(one({}) + one({head: ['sector 2'], map: blankMap.map((l, k) => (k ? l : '7'))}).replace('solo', 'duo'),
    "a sector's own looks past what fits", big);
}
function compareVerdictOk(text) {
  return RS.validate(RS.parseRooms(text), tiles).filter(p => p.level === 'error').length === 0;
}

rmSync(tmp, {recursive: true, force: true});
console.log(failed ? `\n${failed} failed` : `\nall passed${skipped ? ` (${skipped} skipped)` : ''}`);
process.exit(failed ? 1 : 0);
