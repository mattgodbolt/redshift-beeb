#!/usr/bin/env node
// Checks the level editor (editor/index.html) against the real files and tools/mkrooms.py:
//
//   node editor/check.mjs [rooms.txt]
//
// - rooms.txt survives a load and a save byte for byte, and rooms written afresh read back the same;
// - every room draws, in both phases and every state its machinery has (on the beat, the switch thrown,
//   both: decision 46), pixel for pixel as mkrooms.py's render() draws it;
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
    print(json.dumps({s.name: [g.hollow(s.pixels), g.ghost_sprite(s.pixels, 0)] for s in g.read_sprites(ghosts=False)}))
elif mode == 'types':
    print(json.dumps([m.THING_TYPES, m.THING_BOX, list(m.SWITCH_THINGS), [g.MAX_PARTS, g.PART_W, g.PART_CELLS]]))
elif mode == 'render':
    # Each room as drawn, and in each state of its machinery that changes its map.
    tiles = g.read_tiles()
    out = []
    for r in g.read_rooms(sys.argv[3]):
        drawn = g.machine_map(r, tiles)
        states = [s for s in g.STATES if s == (0, 0) or g.machine_map(r, tiles, *s) != drawn]
        out.append([[f'{b}{t}'] + [base64.b64encode(m.render(r, tiles, p, scale=1, state=(b, t)).tobytes()).decode()
                                   for p in (0, 1)] for b, t in states])
    print(json.dumps(out))
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
  r.bands.map(b => [b.line, b.logical, b.r, b.b]), r.beat && [r.beat[0], r.beat[r.beat.length - 1]], r.map,
  r.things.map(t => [t.type, t.x, t.y, t.args]),
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
  const STATE_NAMES = {'00': '', '10': ', on the beat', '01': ', the switch thrown', '11': ', on the beat and the switch thrown'};
  doc.rooms.forEach((r, k) => {
    // (The states the editor's map changes in, as mkrooms.py's does: machineMap against machine_map.)
    const drawn = JSON.stringify(RS.machineMap(r, tileMap));
    const mine = RS.STATES.filter(([b, t]) => (!b && !t) || JSON.stringify(RS.machineMap(r, tileMap, [b, t])) !== drawn)
      .map(([b, t]) => `${b}${t}`);
    check(JSON.stringify(mine) === JSON.stringify(want[k].map(s => s[0])),
      `${label}: ${r.id}'s machinery has the states render() has: ${mine.join(' ')}`);
    for (const [state, ...phases] of want[k]) {
      [0, 1].forEach(phase => {
        const buf = RS.renderRoom(r, tileMap, phase, new Uint8ClampedArray(RS.WIDTH * RS.LINES * 4), [+state[0], +state[1]]);
        const ref = Buffer.from(phases[phase], 'base64');
        let bad = 0, first = -1;
        for (let i = 0, j = 0; i < ref.length; i += 3, j += 4) {
          if (ref[i] !== buf[j] || ref[i + 1] !== buf[j + 1] || ref[i + 2] !== buf[j + 2]) {
            bad++;
            if (first < 0) first = i / 3;
          }
        }
        check(ref.length === RS.WIDTH * RS.LINES * 3 && !bad,
          `${label}: ${r.id} in the ${phase ? 'Blue' : 'Red'} Phase${STATE_NAMES[state]} draws as render() draws it`,
          `${bad} pixels differ, the first at ${first % RS.WIDTH}, ${Math.floor(first / RS.WIDTH)}`);
      });
    }
  });
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
  const [list, boxes, switches, parts] = JSON.parse(types.out);
  check(JSON.stringify(list) === JSON.stringify(RS.THING_TYPES), `THING_TYPES matches mkrooms.py's: ${list.join(' ')}`);
  check(JSON.stringify(boxes) === JSON.stringify(RS.THING_BOX), "THING_BOX matches mkrooms.py's");
  check(JSON.stringify(switches) === JSON.stringify(RS.SWITCH_THINGS), `SWITCH_THINGS matches mkrooms.py's: ${switches.join(' ')}`);
  check(JSON.stringify(parts) === JSON.stringify([RS.MAX_PARTS, RS.PART_W, RS.PART_CELLS]),
    `MAX_PARTS, PART_W and PART_CELLS match gfxlib's: ${parts.join(' ')}`);
}

const ghosts = py('ghosts');
if (ghosts.error) skip('ghosts', ghosts.error);
else {
  const want = JSON.parse(ghosts.out);
  const bad = sprites.filter(s => JSON.stringify(s.hollow) !== JSON.stringify(want[s.name][0])).map(s => s.name);
  check(!bad.length, `every sprite's outline is gfxlib's hollow() (${sprites.length} sprites)`, `differ: ${bad.join(' ')}`);
  const badGhost = sprites.filter(s => JSON.stringify(s.ghost) !== JSON.stringify(want[s.name][1])).map(s => s.name);
  check(!badGhost.length, `every sprite's ghost is gfxlib's ghost_sprite() (${sprites.length} sprites)`, `differ: ${badGhost.join(' ')}`);
}

// --- Made-up rooms, for what the real ones don't have yet -----------------------------------------

// Every tile, split between alpha (Sector 2), gamma (Sector 3), delta (Sector 4) and epsilon (Sector
// 5): each is drawn, and each is one sector's own, so each sector's looks stay within what the game
// can number (decision 43). The splits are where the looks they'd own (a tile's own, its variants and
// alts) come out about even, in quarters, as there are four sectors' kits to share out. (A tile drawn
// as another owns none.)
const keys = tiles.map(t => t.key).join('');
const owned = tiles.map((t, i) => (i === 0 || t.shared || t.like != null ? 0
  : 1 + t.variants.length + Object.values(t.alts).reduce((n, list) => n + list.length, 0)));
const allOwned = owned.reduce((a, b) => a + b, 0);
const PARTS = 4;
const cut = part => {
  let i = 0;
  for (let sum = 0; i < tiles.length && PARTS * (sum + owned[i]) <= part * allOwned; i++) sum += owned[i];
  return i;
};
const cuts = [0, cut(1), cut(2), cut(3), keys.length];
const keysOf = n => (n === 3 ? '' : ' ') + keys.slice(cuts[(n - 3) / 2], cuts[(n - 3) / 2 + 1]);
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
  'band 175 3 red', 'map', ...map(5), 'thing shard 1 1', 'thing exit 29 19 0 extra', '',
  'room delta', 'name DELTA', 'sector 4', 'start 2 18', 'map', ...map(7), '',
  'room epsilon', 'name EPSILON', 'sector 5', 'start 2 18', 'map', ...map(9), 'thing hinge 4 4', '', '# the end', '',
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
  'two hinges': one({tail: ['thing hinge 4 4', 'thing hinge 8 4']}),
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
  const big = `${read('gfx/tiles.txt')}\ntile é big\n${art}\n` + `alt é base\n${art}\n`.repeat(RS.MAX_LOOKS - 1);
  compareVerdict(one({}) + one({head: ['sector 2'], map: blankMap.map((l, k) => (k ? l : 'é'))}).replace('solo', 'duo'),
    "a sector's own looks past what fits", big);
}

// Machinery (decision 46): each of these breaks one of its rules, but for the first few, which keep
// them. The ram (") and its slot (,) move on the beat, the turntable's deck (7) goes on it, and the
// gate (`) opens when a switch is thrown.
{
  const at = rows => blankMap.map((l, k) => rows[k] ?? l);
  const floor = '_'.repeat(RS.MAP_W);
  const art = Array(8).fill('.1.1.1.1').join('\n');
  const realTiles = read('gfx/tiles.txt');
  compareVerdict(one({head: ['beat 20 10'], map: at({8: '  """', 9: '  ,,,', 10: '  ,,,', 21: floor})}),
    'a ram on a beat');
  compareVerdict(one({head: ['beat 20'], map: at({17: '  7777', 18: floor}),
    tail: ['thing lever 10 16 2']}), 'a deck on a beat, and a lever that stops it');
  compareVerdict(one({map: at({15: '    `', 16: '    `', 17: '    `', 18: floor}), tail: ['thing plate 8 17']}),
    'a gate, and a plate that opens it');
  const machineBroken = {
    'a beat line with no frames': one({head: ['beat']}),
    'a beat of 0 frames': one({head: ['beat 0']}),
    'a beat of 256 frames the other way': one({head: ['beat 10 256']}),
    'a beat with three numbers': one({head: ['beat 1 2 3']}),
    'a ram with no beat': one({map: at({8: '  """', 9: '  ,,,', 21: floor})}),
    'a gate with nothing to throw it': one({map: at({17: '    `', 18: floor})}),
    'a gate with only a cage': one({map: at({17: '    `', 18: floor}), tail: ['thing exit 10 15']}),
    // (Each deck cell is a part, with the air under it, which loses its ceiling.)
    'nine parts': one({head: ['beat 9'], map: at({10: '7 7 7 7 7 7 7 7 7', 21: floor})}),
    'the beat and the switch changing one cell': one({head: ['beat 9'], map: at({17: '`t7', 18: floor}),
      tail: ['thing lever 10 16']}),
  };
  for (const [what, text] of Object.entries(machineBroken)) compareVerdict(text, what);
  // And what the art can't say: a tile that becomes one that isn't there, machinery that breaks, a tile
  // that says both, and a breakable tile whose look a gate changes.
  const plain = one({});
  compareVerdict(plain, "a tile that becomes one that isn't there", `${realTiles}\ntile é odd beat=ñ\n${art}\n`);
  compareVerdict(plain, 'machinery that a grenade breaks', `${realTiles}\ntile é odd solid breakable beat=space\n${art}\n`);
  compareVerdict(plain, 'a tile on the beat and thrown by a switch', `${realTiles}\ntile é odd beat=space switch=space\n${art}\n`);
  compareVerdict(plain, 'a tile on the beat twice over', `${realTiles}\ntile é odd beat=space beat=,\n${art}\n`);
  compareVerdict(one({map: at({17: '`é', 18: floor}), tail: ['thing lever 10 16']}),
    "a breakable tile's look changed by a gate", `${realTiles}\ntile é crumbly solid breakable\n${art}\nvariant é left\n${art.replace(/1/g, '2')}\n`);
  // A tile drawn as another (as=, decision 49): a truck that goes on the beat and where it comes, and what
  // the art can't say of one.
  compareVerdict(one({head: ['beat 20 30'], map: at({16: '  ÇÇÇççç', 17: '  ĈĈĈĉĉĉ', 18: floor})}), 'a truck that drives itself');
  compareVerdict(plain, 'a tile drawn as one with other flags', `${realTiles}\ntile é odd as=C\n`);
  compareVerdict(plain, "a tile drawn as one that isn't there", `${realTiles}\ntile é odd solid as=ñ\n`);
  compareVerdict(plain, 'a tile drawn as one drawn as another', `${realTiles}\ntile é odd solid as=Ç\n`);
  compareVerdict(plain, 'a variant of a tile drawn as another', `${realTiles}\ntile é odd solid as=C\nvariant é left\n${art}\n`);
  // A tile that's another thing in each phase (a "blue" block, the Hinge's: decision 58), and one the
  // game's code turns into another (then=), and what the art can't say of either.
  const blueArt = art.replace(/1/g, '2');
  compareVerdict(one({map: at({17: 'é', 18: floor})}), 'a tile with a Blue Phase picture',
    `${realTiles}\ntile é odd solid then=ê\n${art}\nblue é\n${blueArt}\ntile ê odder solid\n${art}\nblue ê\n${art}\n`);
  compareVerdict(plain, 'a Blue Phase picture for a tile only in the Red', `${realTiles}\ntile é odd solid red\n${art}\nblue é\n${blueArt}\n`);
  compareVerdict(plain, 'two Blue Phase pictures for a tile', `${realTiles}\ntile é odd\n${art}\nblue é\n${art}\nblue é\n${art}\n`);
  compareVerdict(plain, 'a Blue Phase picture and a variant', `${realTiles}\ntile é odd\n${art}\nblue é\n${art}\nvariant é left\n${art}\n`);
  compareVerdict(plain, 'a Blue Phase picture for no tile', `${realTiles}\nblue é\n${art}\n`);
  compareVerdict(plain, "then= a tile that isn't there", `${realTiles}\ntile é odd then=ê\n${art}\n`);
  compareVerdict(plain, 'then= a tile drawn as another', `${realTiles}\ntile é odd solid then=Ç\n${art}\n`);
  compareVerdict(plain, 'then= twice', `${realTiles}\ntile é odd then=ê then=ê\n${art}\ntile ê odder\n${art}\n`);
}
function compareVerdictOk(text) {
  return RS.validate(RS.parseRooms(text), tiles).filter(p => p.level === 'error').length === 0;
}

rmSync(tmp, {recursive: true, force: true});
console.log(failed ? `\n${failed} failed` : `\nall passed${skipped ? ` (${skipped} skipped)` : ''}`);
process.exit(failed ? 1 : 0);
