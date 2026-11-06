#!/usr/bin/env node
// A playthrough of every sector, from the first room to each sector's cage,
// each next sector's load from the disc, THE HINGE beaten in Sector 5 and the
// ending seen through to a new game, on the default build: the end-to-end
// test that the game can be finished without losing a life, and with --shots,
// the README's screenshots.
//
//   node tools/playthrough.mjs               play it, and fail if a room isn't reached,
//                                            a life is lost, a sergeant lives, a switch
//                                            isn't thrown, or the Hinge isn't beaten
//   node tools/playthrough.mjs --shots DIR   also save a screenshot at each moment the
//                                            route marks, as DIR/<name>.png
//
// The route is a player's, read off the screen: it waits for enemies to turn
// or move off, and for machinery to move, as a player would, and reads where
// things are and how the machinery stands from memory only to time that.
import { execFileSync } from "child_process";
import { mkdirSync } from "fs";
import { startBeeb } from "./beeb.mjs";

const args = process.argv.slice(2);
const si = args.indexOf("--shots");
const OUT = si >= 0 ? args[si + 1] : null;
const KEYS = { L: "Z", R: "X", J: "COLON_STAR", D: "SLASH", F: "RETURN", G: "SPACE", S: "SHIFT" };

const beeb = await startBeeb({ disc: "build/redshift.ssd", symbols: "build/redshift.json" });
if (OUT) mkdirSync(OUT, { recursive: true });
// The game's narrowed screen in jsbeeb's screenshot, at a BBC pixel to two of
// the PNG's; and the title page's, which is wider.
const CROP = { game: [368, 264, 1024, 768], title: [304, 152, 1216, 944] };
const mark = async (name, crop = "game") => {
    if (!OUT) return;
    const f = `${OUT}/${name}.png`;
    await beeb.shot(f);
    const [x, y, w, h] = CROP[crop];
    execFileSync("python3", ["-c", `
from PIL import Image
im = Image.open("${f}").convert("RGB").crop((${x}, ${y}, ${x + w}, ${y + h}))
im.resize((${w / 2}, ${h / 2}), Image.NEAREST).quantize(colors=16).save("${f}", optimize=True)
`]);
};

// --- The player's hands ---------------------------------------------------

const g = {
    async gf(n = 1) { if (n > 0) await beeb.frames(2 * n); },
    async st() {
        const one = async (s) => (await beeb.read(s, 1))[0];
        return { x: await one("obj_x"), y: await one("obj_y"), room: await one("room"), lives: await one("lives"),
            cells: await one("cells"), dead: await one("pl_dead"), air: await one("pl_air"), phase: await one("phase") };
    },
    async down(k) { await beeb.keyDown(KEYS[k] ?? k); },
    async up(k) { await beeb.keyUp(KEYS[k] ?? k); },
    async tap(k, n = 3) { await g.down(k); await g.gf(n); await g.up(k); },
    async land(limit = 100) {
        for (let i = 0; i < limit; i++) { const s = await g.st(); if (s.air === 0 || s.dead) return s; await g.gf(1); }
        return g.st();
    },
    async walkTo(tx, limit = 200) {
        let s = await g.st();
        const dir = tx > s.x ? "R" : "L";
        await g.down(dir);
        for (let i = 0; i < limit; i++) {
            s = await g.st();
            if ((dir === "R" && s.x >= tx) || (dir === "L" && s.x <= tx) || s.dead) break;
            await beeb.frames(1);
        }
        await g.up(dir);
        await g.gf(1);
        return g.land();
    },
    async walkUntilRoom(dir, room, limit = 400) {
        await g.down(dir);
        for (let i = 0; i < limit; i++) { const s = await g.st(); if (s.room === room || s.dead) break; await g.gf(1); }
        await g.up(dir);
    },
    async jump(dir = null, n = 24) {
        if (dir) await g.down(dir);
        await g.tap("J", 2);
        await g.gf(Math.max(0, n - 2));
        if (dir) await g.up(dir);
        return g.land();
    },
};
const thing = async (i) => {
    const x = (await beeb.read("obj_x", 12))[i], f = (await beeb.read("obj_face", 12))[i];
    return { x, f, alive: (await beeb.read("obj_spr", 12))[i] !== 255 };
};
// The enemies' bolts in flight (EB0 on).
const bolts = async () => (await beeb.read("obj_spr", 12)).slice(10).filter((s) => s !== 255).length;
// A sergeant (thing i) that should be dead.
const dead = async (i, where) => { if ((await thing(i)).alive) throw new Error(`${where}'s sergeant lived`); };
// The cage: its ride, then the next sector's rooms from the disc (src/sector.6502).
const rideCage = async (sector) => {
    const ride = await beeb.runUntil("sector_load", 15);
    if (ride.stopped_reason !== "breakpoint") throw new Error("the cage didn't load the next sector");
    const load = await beeb.runUntil("sector_load.done", 30);
    if (load.stopped_reason !== "breakpoint") throw new Error(`Sector ${sector}'s load didn't finish`);
    console.log(`${`Sector ${sector} loaded`.padEnd(16)} in ${(load.cycles_run / 2e6).toFixed(2)}s`);
};
let lives0 = null;
const expectRoom = async (n, name) => {
    const s = await g.st();
    console.log(`${name.padEnd(16)} room ${s.room}  lives ${s.lives}  cells ${s.cells}`);
    if (s.room !== n) throw new Error(`expected room ${n} (${name}), in room ${s.room}`);
    if (lives0 !== null && s.lives < lives0) throw new Error(`a life was lost before ${name}`);
    lives0 = s.lives;
};
// Fire (crouched, or not) until thing i is gone; false if it isn't.
const fireUntilDead = async (i, limit = 150, crouch = false) => {
    if (crouch) await g.down("D");
    await g.down("F");
    for (let k = 0; k < limit; k++) { await g.gf(1); if (!(await thing(i)).alive) break; }
    await g.up("F");
    if (crouch) await g.up("D");
    return !(await thing(i)).alive;
};
const cross = async (dir, room) => { await g.walkUntilRoom(dir, room); await g.gf(3); };
// Into a room, and on once it's drawn and its things are out.
const settle = async () => { await until(async () => (await beeb.peek("blackout")) === 0, 100); await g.gf(2); };
const until = async (test, limit = 400) => { for (let i = 0; i < limit; i++) { if (await test()) return; await g.gf(1); } };
// The machinery just turning: 0 back as drawn, 1 the other way (src/machines.6502).
const beatTurns = async (on) => {
    await until(async () => (await beeb.peek("beat_on")) !== on, 300);
    await until(async () => (await beeb.peek("beat_on")) === on, 300);
};
// The room's switch, which should have been thrown.
const thrown = async (where) => { if (!(await beeb.peek("sw_thrown"))) throw new Error(`${where}'s switch wasn't thrown`); };
const shift = async () => { await g.tap("S", 2); await g.gf(2); };
// The frame rate across the machinery's next warning and turn, while Ash
// waits: in game frames and VSyncs, which wrap at 256.
const frameRate = async (what) => {
    const b0 = await beeb.peek("beat_on"), f0 = await beeb.peek("frame"), v0 = await beeb.peek("vsyncs");
    await until(async () => (await beeb.peek("beat_on")) !== b0, 150);
    await g.gf(5);
    const frames = ((await beeb.peek("frame")) - f0) & 255, vsyncs = ((await beeb.peek("vsyncs")) - v0) & 255;
    console.log(`${"(frame rate)".padEnd(16)} ${frames} game frames in ${vsyncs} VSyncs, ${what}`);
    if (frames * 2 < vsyncs - 2) throw new Error(`frames dropped, ${what}: ${frames} in ${vsyncs} VSyncs`);
};

// --- The title page, then the route ---------------------------------------

await beeb.runUntil("rsload.space");        // (RSLOAD waiting for SPACE)
await g.gf(10);
await mark("title", "title");
await g.down("G"); await g.gf(3); await g.up("G");
await beeb.runUntil("game_start", 30);
await g.gf(40);
await mark("card");
await g.gf(70);
await g.land();

try {
    // 1 LANDING ZONE
    await expectRoom(0, "LANDING ZONE");
    await g.gf(10); await mark("landing");
    if (!(await fireUntilDead(5))) throw new Error("the pad's Trundler lived");
    await g.walkTo(30); await g.jump("R", 20);
    await g.walkTo(58); await g.jump("R", 14);
    await g.walkTo(76); await g.jump("R", 14);
    await g.down("R"); await until(async () => { const s = await g.st(); return s.air === 0 && s.y === 104; }, 40); await g.up("R"); await g.land();
    await g.walkUntilRoom("R", 1, 80); await g.land();
    await g.gf(3);
    // 2 PUMP HOUSE: the shift
    await expectRoom(1, "PUMP HOUSE");
    await g.jump("R", 12);
    await g.walkTo(28); await g.jump("R", 16);
    await g.walkTo(64, 60);
    await mark("pump_red");
    if (!(await fireUntilDead(4, 200))) throw new Error("the Pump House's Gadfly lived");
    await g.tap("S", 2); await g.gf(2);
    await g.gf(20); await mark("pump_blue");
    // (Up the crate on the chain, from where it stops Ash, and then the ledge.)
    await g.walkTo(102, 80); await g.jump("R", 16);
    await g.walkTo(110); await g.jump("R", 16);
    await cross("R", 2);
    // 3 VAT ROW (in the Blue)
    await expectRoom(2, "VAT ROW");
    await g.gf(4); await mark("vatrow");
    await g.down("F"); await g.walkTo(28); await g.jump("R", 16); await g.walkTo(56); await g.jump("R", 18); await g.walkTo(108); await g.up("F");
    await cross("R", 3);
    await g.gf(30);
    // 4 THE PICKLE JAR
    await expectRoom(3, "THE PICKLE JAR");
    await g.tap("S", 2); await g.gf(2);
    await g.walkTo(90); await g.jump("L", 14);
    await fireUntilDead(4, 200);
    await mark("jar");
    await g.walkTo(67); await g.jump("L", 20);
    await g.walkTo(42); await g.jump("L", 14);
    // (Watch the Trundler below, and drop when it's well off to the right.)
    await until(async () => { const c = await thing(5); return !c.alive || c.x > 70; }, 400);
    await g.walkTo(10);
    await g.down("R"); await g.gf(1); await g.up("R");
    await fireUntilDead(5, 150, true);
    await cross("R", 4);
    // 5 SETTLING TANKS
    await expectRoom(4, "SETTLING TANKS");
    await g.walkTo(6); await g.jump("R", 8);
    await g.jump("R", 10);
    await g.walkTo(60, 60);
    await g.jump("R", 24);
    await g.walkTo(100, 60);
    await mark("tanks");
    await g.tap("G", 2); await g.gf(20);
    await fireUntilDead(5, 200);
    await g.jump("R", 10);
    await cross("R", 5);
    // 6 FOREMAN'S HUT
    await expectRoom(5, "FOREMAN'S HUT");
    // (A charge lobbed from the crate, where the sergeant's fire passes under.)
    await g.walkTo(26); await g.jump("R", 8); await g.walkTo(36);
    await g.down("R"); await g.gf(1); await g.up("R");
    await mark("hut");
    await g.tap("G", 2); await g.gf(40);
    if ((await thing(4)).alive) throw new Error("the Foreman's Hut's sergeant lived");
    await cross("R", 6);
    // 7 THE CATWALKS
    await expectRoom(6, "THE CATWALKS");
    await g.walkTo(26);
    await g.tap("S", 2); await g.gf(2);
    await mark("catwalks");
    await g.down("F"); await g.walkTo(48); await g.up("F");
    await g.tap("J", 2); await g.gf(8); await g.tap("S", 1); await g.land();
    await g.walkTo(56); await g.jump("R", 26);
    await g.walkTo(90); await g.jump("R", 10);
    await g.walkTo(94); await g.jump("L", 12);
    await g.walkTo(88); await g.jump("R", 16);
    await cross("R", 7);
    await g.gf(30);
    // 8 SLURRY RUN
    await expectRoom(7, "SLURRY RUN");
    await g.walkTo(90);
    await g.tap("S", 2); await g.gf(2);
    await g.down("L"); await g.gf(1); await g.up("L");
    await g.down("F");
    await until(async () => !(await thing(6)).alive && !(await thing(7)).alive, 40);
    await g.walkTo(52); await g.up("F");
    await mark("slurry");
    await until(async () => { const t = await thing(4); return t.f === 2 && t.x < 22; }, 200);
    await g.tap("S", 2); await g.gf(2);
    await fireUntilDead(4, 200, true);
    await cross("L", 8);
    await g.gf(30);
    // 9 SKIP SHAFT, and the cage
    await expectRoom(8, "SKIP SHAFT");
    await mark("skip");
    // (Down the ledges onto the crate, where the sergeant's fire passes
    // under. Then, once a shot has struck the crate, down to the floor to
    // roll a charge into it, crouched under the next.)
    await g.walkTo(24); await g.walkTo(34);
    await until(async () => (await bolts()) > 0, 80);
    await until(async () => (await bolts()) === 0, 40);
    await g.walkTo(44);
    await g.down("D"); await g.gf(2); await g.tap("G", 2); await g.gf(30); await g.up("D");
    await dead(4, "the Skip Shaft");
    await g.down("R");
    await rideCage(2);
    await g.up("R");
    await g.gf(20); await mark("sector2");
    await until(async () => (await beeb.peek("room_sector")) === 2 && (await beeb.peek("blackout")) === 0, 200);
    await g.land();

    // --- Sector 2: the Marshalling Yard ------------------------------------

    // 1 ENGINE SHED: Trundlers in numbers, one on the floor behind the
    // buffers, one on the engine; crystal before the engine and a Sliver for
    // a Blue that isn't a way round them.
    await expectRoom(0, "ENGINE SHED");
    if ((await beeb.peek("room_sector")) !== 2) throw new Error("the Engine Shed isn't in Sector 2");
    await g.gf(10); await mark("engine");
    await g.walkTo(18);
    // (Over the buffers once the first has rolled off, and shoot it crouched.)
    await until(async () => { const a = await thing(4); return a.x > 48 && a.f === 0; }, 200);
    await g.jump("R", 20);
    if (!(await fireUntilDead(4, 100, true))) throw new Error("the Engine Shed's floor Trundler lived");
    // (Up onto the engine when the other is at its far end, by the cab, which
    // turns it now it's solid.)
    await g.walkTo(52);
    await until(async () => { const t = await thing(5); return t.x >= 80 && t.f === 0; }, 300);
    await g.jump("R", 14);
    if (!(await fireUntilDead(5, 100, true))) throw new Error("the engine's Trundler lived");
    await g.walkTo(80); await g.jump("R", 14);
    await cross("R", 1); await settle();
    // 2 SIGNAL BOX: a sergeant up in the box, lobbed from the truck on its
    // plinth, where the sergeant's fire passes over; then into the box and
    // over its lever frame.
    await expectRoom(1, "SIGNAL BOX");
    if (!(await fireUntilDead(4, 150))) throw new Error("the Signal Box's Trundler lived");
    await g.walkTo(8); await g.jump("R", 10);
    await g.walkTo(44); await g.jump("R", 12);
    await g.walkTo(56);
    await g.down("R"); await g.gf(1); await g.up("R");
    await mark("signal");
    await g.tap("G", 2); await g.gf(40);
    await dead(5, "the Signal Box");
    await g.jump("R", 12);
    await g.walkTo(94); await g.jump("R", 16);
    await g.walkTo(118, 300);
    await cross("R", 2); await settle();
    // 3 TURNTABLE: straight over the deck from the way in, in its first
    // window (it turns away on the beat, with a warning first), then the
    // Slivers beyond the barricade in the Blue, and down through the welded
    // hatch.
    await expectRoom(2, "TURNTABLE");
    await g.walkTo(84);
    await g.tap("S", 2); await g.gf(2);
    await g.gf(4); await mark("turntable");
    await g.down("F");
    await until(async () => !(await thing(4)).alive && !(await thing(5)).alive, 150);
    await g.up("F");
    if ((await thing(4)).alive || (await thing(5)).alive) throw new Error("the turntable's Slivers lived");
    await g.walkUntilRoom("R", 3, 200); await settle();
    await g.gf(30);
    // 4 WEIGHBRIDGE: over the crystals onto the weigh plate, which opens the
    // gate to the truck, up the truck to the siding, back to the Red where the
    // crystal grows, and a charge lobbed at the jammed carts.
    await expectRoom(3, "WEIGHBRIDGE");
    await g.walkTo(108); await g.jump("L", 16);
    await thrown("the Weighbridge");
    await g.jump("L", 12); await g.jump("L", 22);
    // (The siding's Trundler is a ghost in the Blue: back to the Red with it
    // off at the far end, more than a tile away (decision 51), and shoot it.)
    await until(async () => { const t = await thing(4); return t.x < 50 && t.f === 2; }, 300);
    await g.tap("S", 2); await g.gf(2);
    if (!(await fireUntilDead(4, 150, true))) throw new Error("the Weighbridge's first Trundler lived");
    await g.walkTo(60);
    await g.down("L"); await g.gf(1); await g.up("L");
    await mark("weighbridge");
    // (A charge lobbed at the carts, under the siding's raised roof, and fire
    // on through the gap at the Trundler that was behind them.)
    await g.tap("G", 2); await g.gf(30);
    if (!(await fireUntilDead(5, 150, true))) throw new Error("the Trundler behind the carts lived");
    await cross("L", 4); await settle();
    // 5 SIDING FOUR: up the buffers, and onto the truck that drives itself
    // while it's near; where it overlaps itself while it runs over to the far
    // side; off it there, to shoot the Trundler on the next truck, where
    // crystal grows in the Blue; then the Gadfly under the barricade, and
    // through it in the Blue, where Slivers wake.
    await expectRoom(4, "SIDING FOUR");
    await g.walkTo(118);
    await g.jump("L", 7);
    await g.walkTo(108);
    await until(async () => (await beeb.peek("beat_on")) === 0 && (await beeb.peek("beat_t")) > 40, 300);
    await g.jump("L", 11);
    await g.walkTo(72);
    await until(async () => (await beeb.peek("beat_on")) === 1, 300);
    await g.gf(2);
    await g.walkTo(48);
    await mark("siding");
    if (!(await fireUntilDead(4, 150))) throw new Error("Siding Four's Trundler lived");
    await g.jump("L", 8);
    await g.walkTo(20);
    await g.down("L"); await g.gf(1); await g.up("L");
    if (!(await fireUntilDead(5, 150))) throw new Error("Siding Four's Gadfly lived");
    await g.tap("S", 2); await g.gf(2);
    await g.down("F");
    await until(async () => !(await thing(6)).alive && !(await thing(7)).alive, 150);
    await g.up("F");
    if ((await thing(6)).alive || (await thing(7)).alive) throw new Error("Siding Four's Slivers lived");
    await g.walkUntilRoom("L", 5, 200); await settle();
    // 6 CRANE GANTRY: back to the Red through the crystal, under the load
    // while it's up (it drops on the beat), onto the truck, and a charge
    // lobbed at the sergeant on the crane's other load; then over that load.
    await g.land();
    await expectRoom(5, "CRANE GANTRY");
    await g.tap("S", 2); await g.gf(2);
    await g.walkTo(30);
    await beatTurns(0);
    await g.walkTo(54);
    await g.jump("R", 10);
    await g.walkTo(66);
    await mark("crane");
    await g.tap("G", 2); await g.gf(40);
    await dead(4, "the Crane Gantry");
    await g.walkTo(70); await g.jump("R", 12);
    await cross("R", 6); await settle();
    // 7 BUFFER STOPS: the barricade and the Slivers in the Blue, the plates
    // in the Red; then, once the truck has run into the buffers, up it and
    // over them, and down.
    await expectRoom(6, "BUFFER STOPS");
    await g.walkTo(18);
    await g.tap("S", 2); await g.gf(2);
    await g.down("F");
    await until(async () => !(await thing(4)).alive && !(await thing(5)).alive, 150);
    await g.up("F");
    await g.walkTo(56);
    await g.tap("S", 2); await g.gf(2);
    if (!(await fireUntilDead(6, 200, true))) throw new Error("the Buffer Stops' Trundler lived");
    await g.walkTo(82);
    await beatTurns(1);
    await g.walkTo(92); await g.jump("R", 10);
    await mark("buffers");
    await g.walkUntilRoom("R", 7, 200); await settle();
    // 8 DEAD MAN'S HANDLE: the handle shot from the ledge, which stops the
    // press over the way down; down onto the truck between two sergeants, a
    // charge lobbed at each, and down past the press.
    await g.land();
    await expectRoom(7, "DEAD MAN'S HANDLE");
    await g.walkTo(68);
    await g.down("L"); await g.gf(1); await g.up("L");
    await g.down("F"); await until(async () => (await beeb.peek("sw_thrown")) !== 0, 40); await g.up("F");
    await thrown("the Dead Man's Handle");
    await g.walkTo(60); await g.land();
    await mark("handle");
    await g.walkTo(66);
    await g.down("R"); await g.gf(1); await g.up("R");
    await g.tap("G", 2); await g.gf(40);
    await dead(5, "the Dead Man's Handle's right");
    await g.walkTo(70);
    await g.down("L"); await g.gf(1); await g.up("L");
    await g.tap("G", 2); await g.gf(40);
    await dead(4, "the Dead Man's Handle's left");
    await g.walkUntilRoom("L", 8, 300); await settle();
    // 9 CRUSHER'S MOUTH: into the Blue on the ledge, where Slivers wake; from
    // the beam's end, clear of the jaw, along it while the jaw's open, the
    // Blue's span, a shift on the girder between, the Red's plates, down onto
    // the truck; then through the press, which opens while the jaw shuts, to
    // the cage.
    await g.land();
    await expectRoom(8, "CRUSHER'S MOUTH");
    await mark("crusher");
    await g.tap("S", 2); await g.gf(2);
    await g.down("R"); await g.gf(1); await g.up("R");
    await g.down("F");
    await until(async () => !(await thing(5)).alive && !(await thing(6)).alive, 250);
    await g.up("F");
    if ((await thing(5)).alive || (await thing(6)).alive) throw new Error("the Crusher's Mouth's Slivers lived");
    await g.walkTo(20);
    await beatTurns(0);
    await g.walkTo(56);
    await mark("jaw");
    await g.tap("S", 1);
    await g.walkTo(88); await g.land();
    // (The frame rate across the machinery's warning and its next turn, when
    // the jaw and the press both flicker and move: in game frames and VSyncs,
    // which wrap at 256.)
    const b0 = await beeb.peek("beat_on"), f0 = await beeb.peek("frame"), v0 = await beeb.peek("vsyncs");
    await until(async () => (await beeb.peek("beat_on")) !== b0, 100);
    await g.gf(5);
    const frames = ((await beeb.peek("frame")) - f0) & 255, vsyncs = ((await beeb.peek("vsyncs")) - v0) & 255;
    console.log(`${"(frame rate)".padEnd(16)} ${frames} game frames in ${vsyncs} VSyncs, the jaw and the press moving`);
    if (frames * 2 < vsyncs - 2) throw new Error(`the Crusher's Mouth dropped frames: ${frames} in ${vsyncs} VSyncs`);
    await beatTurns(1);
    await g.down("R");
    await rideCage(3);
    await g.up("R");
    await g.gf(20); await mark("sector3");
    await until(async () => (await beeb.peek("room_sector")) === 3 && (await beeb.peek("blackout")) === 0, 200);
    await g.land();

    // --- Sector 3: the Sump ------------------------------------------------

    // Things by their place in the room's list, from TH0 (4).
    const alive = async (...ids) => (await Promise.all(ids.map(thing))).filter((t) => t.alive).length;
    const fireAt = async (what, ...ids) => {
        await g.down("F");
        await until(async () => (await alive(...ids)) === 0, 300);
        await g.up("F");
        if (await alive(...ids)) throw new Error(`${what} lived`);
    };
    const face = async (dir) => { await g.down(dir); await g.gf(1); await g.up(dir); };
    const beat = async () => beeb.peek("beat_on");

    // 1 OUTFALL, the lesson: the sump boils in the Red and its bed is dry in
    // the Blue. Into the Blue on the bank, where two Slivers wake and come
    // across the sump; down into the bed, up onto the far landing, where
    // crystal holds the way out; back to the Red there, out of the reach of
    // the Trundler on the step above, and shoot it.
    await expectRoom(0, "OUTFALL");
    if ((await beeb.peek("room_sector")) !== 3) throw new Error("the Outfall isn't in Sector 3");
    await g.gf(10); await mark("outfall_red");
    await shift();
    await fireAt("the Outfall's Slivers", 4, 5);
    await g.walkTo(40);
    await mark("outfall_blue");
    await g.walkTo(84);
    await g.jump("R", 20);
    await g.walkTo(94);
    await shift();
    await face("R");
    if (!(await fireUntilDead(6, 150))) throw new Error("the Outfall's Trundler lived");
    await g.jump("R", 26);
    await cross("R", 1); await settle();
    // 2 THE CISTERN: a swarm in the tank. Into the Blue on the walkway, where
    // the Slivers rise out of the empty tank; over the kerb and down through
    // the tank's floor, the Red's plates. Back to the Red in the cellar with
    // the Gadfly off, shoot it, through the crystal's ghost for the cell, and
    // out through the Blue's wall at the cellar's end and down.
    await expectRoom(1, "THE CISTERN");
    await g.walkTo(12);
    await shift();
    await fireAt("the Cistern's Slivers", 4, 5, 6);
    await mark("cistern");
    await g.walkTo(36);
    await g.jump("R", 14);
    await g.land();
    await until(async () => Math.abs((await thing(7)).x - (await g.st()).x) > 24, 300);
    {
        const t = await thing(7), s = await g.st();
        await shift();
        await face(t.x < s.x ? "L" : "R");
    }
    if (!(await fireUntilDead(7, 150))) throw new Error("the Cistern's Gadfly lived");
    await g.walkTo(18);
    if ((await thing(8)).alive) throw new Error("the Cistern's cell wasn't taken");
    await g.walkUntilRoom("R", 2, 300); await settle(); await g.land();
    // 3 BOILER WALK: boiler to boiler over the boiling gaps. Over onto the
    // middle one, up onto its steam dome, out of the sergeant's fire, and a
    // charge lobbed at it; over to the welded door, and into the Blue there.
    await expectRoom(2, "BOILER WALK");
    await g.walkTo(104);
    await g.jump("L", 20);
    await g.walkTo(80);
    await g.jump("L", 8);
    await mark("boiler");
    await g.tap("G", 2); await g.gf(40);
    await dead(4, "the Boiler Walk");
    await g.walkTo(56);
    await g.jump("L", 24);
    await g.walkTo(20);
    await shift();
    await cross("L", 3); await settle(); await g.land();
    // 4 STEAM TRAP, the Blue's road: Blue blocks bar the corridor, and the
    // bed's swarm comes up through the Red's plates at the way in. Down into
    // the dry bed for the cell, up through the plates into the last pocket,
    // back to the Red there, and past the last vent as it stops into the
    // shaft. (The Red's road, from pocket to pocket as each vent stops, costs
    // the same shift and pays no cell.)
    await expectRoom(3, "STEAM TRAP");
    await face("L");
    await fireAt("the Steam Trap's Slivers", 4, 5, 6);
    await g.walkTo(88);
    await g.land();
    await g.walkTo(42);
    if ((await thing(7)).alive) throw new Error("the Steam Trap's cell wasn't taken");
    await g.jump("L", 6);
    await g.jump("L", 12);
    await until(async () => (await beat()) === 0, 200);
    await shift();
    await mark("steam");
    await frameRate("the vents steaming");
    await until(async () => (await beat()) === 1, 200);
    await until(async () => (await beat()) === 0, 200);
    await g.walkUntilRoom("L", 4, 200); await settle(); await g.land();
    // 5 DROWNED OFFICE: in facing the room; shoot the Trundler on the shelf,
    // up onto the filing cabinet, out of the sergeant's fire, and a charge
    // lobbed at it; along to the Red's wall at the shelf's end, into the Blue
    // there, and over the span to the door.
    await expectRoom(4, "DROWNED OFFICE");
    if ((await thing(0)).f !== 0) throw new Error("Ash came into the Drowned Office facing its wall");
    if (!(await fireUntilDead(4, 150))) throw new Error("the Drowned Office's Trundler lived");
    await g.walkTo(10);
    await g.jump("R", 10);
    await g.walkTo(30);
    await g.jump("R", 6);
    await g.walkTo(36);
    await mark("office");
    await g.tap("G", 2); await g.gf(40);
    await dead(5, "the Drowned Office");
    await g.jump("R", 10);
    await g.walkTo(46);
    await g.jump("R", 14);
    await g.walkTo(90);
    await shift();
    await cross("R", 5); await settle();
    // 6 SLUICE GATE: in the Blue, down into the dry bed; the gate's handle
    // shot, which lifts the gate and drains the sump in both phases; on to the
    // Blue's blocks over the culvert, back to the Red in the drained bed, the
    // Trundler beyond, over the kerb and down.
    await expectRoom(5, "SLUICE GATE");
    await g.walkTo(40);
    {
        // (The frame rate across the throw: the gate and the sump's water
        // redrawn at once.)
        const f0 = await beeb.peek("frame"), v0 = await beeb.peek("vsyncs");
        await g.down("F"); await until(async () => (await beeb.peek("sw_thrown")) !== 0, 40); await g.gf(6); await g.up("F");
        const frames = ((await beeb.peek("frame")) - f0) & 255, vsyncs = ((await beeb.peek("vsyncs")) - v0) & 255;
        console.log(`${"(frame rate)".padEnd(16)} ${frames} game frames in ${vsyncs} VSyncs, the sump draining`);
        if (frames * 2 < vsyncs - 2) throw new Error(`the Sluice Gate dropped frames: ${frames} in ${vsyncs} VSyncs`);
    }
    await thrown("the Sluice Gate");
    await mark("sluice");
    await g.walkTo(76);
    await shift();
    if (!(await fireUntilDead(5, 150))) throw new Error("the Sluice Gate's Trundler lived");
    await g.jump("R", 10);
    await g.walkUntilRoom("R", 6, 200); await settle(); await g.land();
    // 7 THE U-BEND: down onto the ledge in the right leg, and into the Blue;
    // down the leg and along the dry bend for a cell, where the Slivers come
    // down the other leg; up it to the ledge at the waterline, and back to the
    // Red there for the welded plate up to the way out.
    await expectRoom(6, "THE U-BEND");
    await shift();
    await g.walkTo(96);
    await g.walkTo(64);
    await fireAt("the U-Bend's Slivers", 4, 5, 6);
    if ((await thing(7)).alive) throw new Error("the U-Bend's cell wasn't taken");
    await mark("ubend");
    await g.walkTo(30);
    await g.jump("L", 6);
    await g.walkTo(18);
    await g.jump("L", 12);
    await shift();
    await g.walkTo(12);
    await g.jump("R", 8);
    await g.walkTo(18);
    await g.jump("L", 12);
    await cross("L", 7); await settle();
    // 8 OVERFLOW: the sump floods the walkway on the beat, in the Red, and
    // baffles of the Blue's hang over it. Down onto the first depth post, and
    // post to post over the walkway with the flood up, as they're spaced to
    // be hopped; into the Blue on the last, and down into the dry basin and
    // up the Blue's steps over it to the way out.
    await expectRoom(7, "OVERFLOW");
    await g.walkTo(104); await g.land();
    await frameRate("the sump flooding the walkway");
    await until(async () => (await beat()) === 1, 300);
    await g.walkTo(99);
    await g.jump("L", 22);
    await mark("overflow");
    await g.walkTo(75);
    await g.jump("L", 30);
    await shift();
    await g.jump("L", 6);
    await g.walkTo(43);
    await g.jump("L", 16);
    await g.walkTo(28);
    await g.jump("L", 18);
    await g.jump("L", 18);
    await cross("L", 8); await settle();
    // 9 THE PLUGHOLE: across the dry basin in the Blue and down the plughole
    // while the plug's drawn up, onto the crate under it; back to the Red
    // there, out of the Drill Sergeant's fire, a charge lobbed at it, and
    // through the Blue's blocks to THE CAGE.
    await expectRoom(8, "THE PLUGHOLE");
    await g.walkTo(108);
    await mark("plughole_bank");
    await frameRate("the plug dropping into the plughole");
    await beatTurns(0);
    await g.down("L");
    for (let i = 0; i < 80; i++) { const s = await g.st(); if (s.y > 64 || s.dead) break; await g.gf(1); }
    await g.up("L");
    if ((await g.land()).y !== 128) throw new Error("Ash missed the Plughole's crate");
    await shift();
    await mark("plughole");
    await g.tap("G", 2); await g.gf(40);
    await dead(4, "the Plughole");
    await g.walkTo(30);
    await g.down("L");
    await rideCage(4);
    await g.up("L");
    await g.gf(20); await mark("sector4");
    await until(async () => (await beeb.peek("room_sector")) === 4 && (await beeb.peek("blackout")) === 0, 200);
    await g.land();

    // --- Sector 4: the Spar Seams ------------------------------------------

    // Fire at a pack, turning to whichever is nearest, as a player does.
    const fight = async (what, ...ids) => {
        await g.down("F");
        for (let i = 0; i < 400; i++) {
            const ts = (await Promise.all(ids.map(thing))).filter((t) => t.alive);
            if (!ts.length) break;
            const s = await g.st();
            const near = ts.reduce((a, b) => (Math.abs(a.x - s.x) <= Math.abs(b.x - s.x) ? a : b));
            const want = near.x < s.x ? 2 : 0;
            if ((await thing(0)).f !== want) { await g.up("F"); await face(want ? "L" : "R"); await g.down("F"); }
            await g.gf(1);
        }
        await g.up("F");
        if (await alive(...ids)) throw new Error(`${what} lived`);
    };

    // 1 THE MOTHER LODE, the lesson: the Blue's crystal grows and draws back
    // here. A welded door at the tunnel's end stops the Red; into the Blue
    // there, where two Slivers wake and come over the pit; over the span
    // while its middle is out, taking the cell on it; back to the Red on the
    // landing, where crystal holds the way out, for the Trundler on the step.
    await expectRoom(0, "THE MOTHER LODE");
    if ((await beeb.peek("room_sector")) !== 4) throw new Error("the Mother Lode isn't in Sector 4");
    await g.walkTo(14);
    await g.gf(4); await mark("mother_red");
    await shift();
    await face("R");
    await fight("the Mother Lode's Slivers", 4, 5);
    await g.walkTo(28);
    await mark("mother_blue");
    await frameRate("the span drawing back and growing");
    await beatTurns(0);
    await g.walkTo(78);
    if (await alive(7)) throw new Error("the Mother Lode's cell wasn't taken");
    await shift();
    await face("R");
    if (!(await fireUntilDead(6, 200))) throw new Error("the Mother Lode's Trundler lived");
    await g.walkTo(88);
    await g.jump("R", 10);
    await cross("R", 1); await settle();
    // 2 SPAR FACE: the face holds back a Gadfly. A pack of charges on the way
    // in; the Gadfly shot through the gap under the face, where it can't
    // come; a charge brings the face down whole; over the Blue's crystal on
    // the floor beyond, which keeps the Blue out; into the Blue at the acid,
    // over its span, and down the shaft.
    await expectRoom(1, "SPAR FACE");
    await g.walkTo(20);
    await face("R");
    await mark("face");
    if (!(await fireUntilDead(5, 300))) throw new Error("the Spar Face's Gadfly lived");
    await g.tap("G", 2); await g.gf(30);
    await g.walkTo(66);
    await shift();
    await g.walkUntilRoom("R", 2, 150); await settle(); await g.land();
    // 3 THE ASSAY ROOM: the furnace is the only footing over the acid, and
    // it fires on the beat in the Red; in the Blue it's cold. Onto it in the
    // Blue, for the cell; back to the Red there as it cools, out of the
    // sergeant's fire, which it stops, and a charge lobbed at it; down onto
    // the far landing over the Blue's crystal before it fires, and out.
    await expectRoom(2, "THE ASSAY ROOM");
    await g.walkTo(76);
    await g.jump("L", 24);
    if (await alive(5)) throw new Error("the Assay Room's cell wasn't taken");
    await frameRate("the furnace firing");
    await beatTurns(0);
    await shift();
    await face("L");
    await mark("assay");
    await g.tap("G", 2); await g.gf(6);
    await g.jump("L", 24);
    await g.gf(30);
    await dead(4, "the Assay Room");
    await g.walkUntilRoom("L", 3, 300); await settle();
    // 4 SORTING TABLE, the Red's road: two rhythms on the picking belt, the
    // hoppers' ore in the Red and the Blue's crystal pushing up through the
    // belt, out of step. The Trundler on the belt, shot from the floor; onto
    // the belt clear of the near hopper; past it while it stops, into the
    // pocket between the hoppers while the far one pours; past that one as it
    // stops; off the belt through the Blue's blocks, onto the welded hatch,
    // into the Blue, down. (The Blue's road times the crystal, and climbs to
    // a cell on a span.)
    await expectRoom(3, "SORTING TABLE");
    await face("L");
    if (!(await fireUntilDead(4, 200))) throw new Error("the Sorting Table's Trundler lived");
    await g.walkTo(110);
    await g.jump("L", 10);
    await frameRate("the hoppers pouring and the crystal pushing up");
    await beatTurns(1);
    await g.walkTo(60);
    await mark("sorting");
    await beatTurns(0);
    await g.walkTo(14);
    await g.land();
    await g.walkTo(2);
    await shift();
    await g.walkUntilRoom("L", 4, 100); await settle(); await g.land();
    // 5 THE CHANDELIER: the Company's winch lowers it on the beat, and draws
    // it up again. In the Blue, over the span onto its boss; ride it down,
    // onto the cell that hangs where the boss comes to; off it onto the rock
    // at the low corridor's mouth, back to the Red there, and over the
    // welded plates.
    await expectRoom(4, "THE CHANDELIER");
    await until(async () => (await beat()) === 0, 300);
    await g.walkTo(56);
    await mark("chandelier_up");
    await frameRate("the chandelier lowered on its chains");
    await until(async () => (await beat()) === 1, 300);
    await g.gf(4); await g.land();
    if ((await g.st()).y !== 64) throw new Error("Ash didn't ride the Chandelier down");
    if (await alive(4)) throw new Error("the Chandelier's cell wasn't taken");
    await mark("chandelier");
    await g.walkTo(74);
    await shift();
    await cross("R", 5); await settle();
    // 6 SPLIT SEAM, the upper road (the sergeant's): along the way in to the
    // crate, up onto it for its charges, one lobbed at the sergeant against
    // the stub of spar; over the hole down to the seam (the lower road, the
    // swarm's, is down it), through the Blue's wall, onto the stub, into the
    // Blue, and over the span.
    await expectRoom(5, "SPLIT SEAM");
    await g.walkTo(12);
    await g.down("R"); await g.tap("J", 2); await g.gf(6); await g.up("R"); await g.land();
    await face("R");
    await mark("split");
    await g.tap("G", 2); await g.gf(40);
    await dead(4, "the Split Seam");
    await g.walkTo(20);
    await g.jump("R", 20);
    await g.walkTo(56);
    await g.jump("R", 8);
    await shift();
    await cross("R", 6); await settle();
    // 7 ECHO GALLERY: two walkways, one over the other, each the other's
    // echo: where the lower is the Blue's crystal, the upper is the Red's
    // plates, and the other way round. In the Blue, down onto the crystal,
    // up onto the next, down and up again; the Blue's crystal holds the door,
    // so back to the Red there, and out.
    await expectRoom(6, "ECHO GALLERY");
    await g.walkTo(24);
    await g.land();
    await g.jump("R", 22);
    await mark("echo");
    await g.walkTo(64);
    await g.land();
    await g.walkTo(72);
    await g.jump("R", 22);
    await g.walkTo(112);
    await shift();
    await cross("R", 7); await settle();
    // 8 LAST PAYDIRT: the bridge comes and goes too fast to cross, and the
    // Company's lever, high on the far wall, stops it: shot from the welded
    // ledge over the way in, at its height, and from nowhere on the floor,
    // where the Slivers are fought. Up onto the ledge for its charges and its
    // cell; the lever; down; into the Blue, the Slivers over the bridge; over
    // it onto the crystal grown over the shaft; into the Red, and down.
    await expectRoom(7, "LAST PAYDIRT");
    await g.walkTo(3, 20);
    await g.jump("R", 16);
    if (await alive(8)) throw new Error("the Last Paydirt's cell wasn't taken");
    await face("R");
    await g.down("F"); await until(async () => (await beeb.peek("sw_thrown")) !== 0, 60); await g.up("F");
    await thrown("the Last Paydirt");
    await mark("paydirt");
    await g.walkTo(0, 30);
    await g.land();
    await shift();
    await face("R");
    await fight("the Last Paydirt's Slivers", 6, 7);
    await g.walkTo(112);
    await shift();
    await g.walkUntilRoom("R", 8, 300); await settle(); await g.land();
    // 9 BORE NINE: sergeants dug in round the drill. On the first crate, a
    // charge at the near one; over the Blue's crystal on the floor onto the
    // second crate, a charge at the far one; to the floor before the welded
    // door, into the Blue, the swarm that comes out of the shaft; and the
    // cage, the drill shaft.
    await expectRoom(8, "BORE NINE");
    await face("L");
    await mark("bore");
    await g.tap("G", 2); await g.gf(40);
    await dead(5, "Bore Nine's near");
    await g.walkTo(68);
    await g.jump("L", 8);
    await face("L");
    await g.tap("G", 2); await g.gf(40);
    await dead(4, "Bore Nine's far");
    await g.walkTo(36);
    await g.land();
    await face("L");
    await shift();
    await fight("Bore Nine's swarm", 7, 8, 9);
    await g.down("L");
    await rideCage(5);
    await g.up("L");
    await g.gf(20); await mark("sector5");
    await until(async () => (await beeb.peek("room_sector")) === 5 && (await beeb.peek("blackout")) === 0, 200);
    await g.land();

    // --- Sector 5: Inside the Prism ----------------------------------------

    // A shift that has to happen: the playthrough fails if it's refused.
    const shiftTo = async (ph, where) => {
        await shift();
        if ((await g.st()).phase !== ph) throw new Error(`the shift in ${where} was refused`);
    };
    // The beat just turned to on (0 or 1), and a walk to x before it turns.
    const onBeat = async (on, x) => { await beatTurns(on); await g.walkTo(x); };

    // 1 FIRST FACET, the lesson: Bore Nine's cage brings Ash in, in the Blue,
    // where two Slivers wake. Along the Blue's floor to the seam where it
    // meets the Red's, for the cell there; back to the Red on the seam, and
    // the Trundler on the step at the way out shot from it; up the step.
    await expectRoom(0, "FIRST FACET");
    if ((await beeb.peek("room_sector")) !== 5) throw new Error("the First Facet isn't in Sector 5");
    await face("R");
    await fight("the First Facet's Slivers", 5, 6);
    await g.walkTo(48);
    if (await alive(7)) throw new Error("the First Facet's cell wasn't taken");
    await mark("facet");
    await shiftTo(0, "the First Facet");
    await face("R");
    if (!(await fireUntilDead(4, 200))) throw new Error("the First Facet's Trundler lived");
    await g.walkTo(82);
    await g.jump("R", 10);
    await cross("R", 1); await settle();
    // 2 THE REFRACTOR: the Prism's pulse turns the middle of the floor from
    // one phase to the other on the beat, flickering first. Along the Red's
    // floor; over the middle a half at a time, on the seam between its halves
    // as it turns; into the Blue on the seam at its end.
    await expectRoom(1, "THE REFRACTOR");
    await g.walkTo(36);
    await frameRate("the refractor's floor turning");
    await onBeat(1, 64);
    await mark("refractor");
    await onBeat(0, 92);
    await shiftTo(1, "the Refractor");
    await cross("R", 2); await settle();
    // 3 CRITICAL ANGLE: a Gadfly between two walls of the Red's that hang
    // short of the floor. Under its ghost along the Blue's floor; into the
    // Red behind the second wall, where it can't come, and shoot it under the
    // wall; out through the Blue's wall.
    await expectRoom(2, "CRITICAL ANGLE");
    await g.walkTo(104);
    await shiftTo(0, "the Critical Angle");
    await face("L");
    await mark("critical");
    if (!(await fireUntilDead(4, 300))) throw new Error("the Critical Angle's Gadfly lived");
    await cross("R", 3); await settle();
    // 4 DOUBLE IMAGE: the Red's bay with a Drill Sergeant, the Blue's with the
    // swarm. Up onto the block at the way in for its charges, and one lobbed
    // at the sergeant; up the pillar behind it, into the Blue there, and the
    // swarm; over the block's image, and out.
    await expectRoom(3, "DOUBLE IMAGE");
    await g.walkTo(2);
    await g.jump("R", 8);
    await g.walkTo(18);
    await face("R");
    await mark("double");
    await g.tap("G", 2); await g.gf(40);
    await dead(4, "Double Image");
    await g.walkTo(66);
    await g.jump("R", 10);
    if ((await g.st()).y !== 72) throw new Error("Ash missed Double Image's pillar");
    await shiftTo(1, "Double Image");
    await face("R");
    await fight("Double Image's swarm", 6, 7, 8);
    await g.walkTo(94);
    await g.jump("R", 14);
    await cross("R", 4); await settle();
    // 5 SPECTRUM WALK: runs of each phase's blocks, the other's hopped. Along
    // the Blue's runs, hopping the Red's; into the Red on the seam before the
    // last run, its Trundler off; shoot it.
    await expectRoom(4, "SPECTRUM WALK");
    await g.walkTo(16);
    await g.jump("R", 16);
    await g.walkTo(54);
    await g.jump("R", 12);
    await mark("spectrum");
    await g.walkTo(76);
    await until(async () => (await thing(4)).x >= 92, 300);
    await shiftTo(0, "the Spectrum Walk");
    await face("R");
    if (!(await fireUntilDead(4, 200))) throw new Error("the Spectrum Walk's Trundler lived");
    await cross("R", 5); await settle();
    // 6 INTERFERENCE: the whole floor turns phase on the beat, run by run.
    // Across in the Red, a run at a time, to the island for its cell; into
    // the Blue at the Red's wall there; across again in the Blue, up onto the
    // far ledge, and back to the Red at the Blue's wall.
    await expectRoom(5, "INTERFERENCE");
    await g.walkTo(8);
    await frameRate("the interference's floor turning");
    await onBeat(0, 24); await onBeat(1, 40); await onBeat(0, 58);
    if (await alive(4)) throw new Error("the Interference's cell wasn't taken");
    await mark("interference");
    await shiftTo(1, "the Interference");
    await onBeat(0, 80); await onBeat(1, 96); await onBeat(0, 110);
    await g.jump("R", 6);
    await shiftTo(0, "the Interference's far ledge");
    await cross("R", 6); await settle();
    // 7 FOCAL LENGTH: the swarm hangs over the Prism's floor, still in the
    // Red. The Trundler, shot crouching from the step at the way in, where it
    // can't come; along under the swarm's ghosts, where a shift is refused,
    // to the floor's far end; into the Blue there, and the swarm comes in a
    // line.
    await expectRoom(6, "FOCAL LENGTH");
    await g.walkTo(4);
    await face("R");
    if (!(await fireUntilDead(4, 300, true))) throw new Error("the Focal Length's Trundler lived");
    await g.walkTo(50);
    await shift();
    if ((await g.st()).phase !== 0) throw new Error("a shift under the Focal Length's swarm wasn't refused");
    await mark("focal");
    await g.walkTo(86);
    await shiftTo(1, "the Focal Length");
    await face("L");
    await fight("the Focal Length's swarm", 5, 6, 7, 8);
    await cross("R", 7); await settle();
    // 8 THE DARK FRINGE: the Hinge's fight before the Hinge, and the bands go
    // dark. The Slivers from the way in, along the Blue's floor; up the
    // pillar; into the Red there, out of the sergeant's fire, and a charge
    // lobbed at it; along the Red's floor and up the step.
    await expectRoom(7, "THE DARK FRINGE");
    await face("R");
    await fight("the Dark Fringe's Slivers", 5, 6);
    await g.walkTo(42);
    await g.jump("R", 8);
    if ((await g.st()).y !== 80) throw new Error("Ash missed the Dark Fringe's pillar");
    await shiftTo(0, "the Dark Fringe");
    await face("R");
    await mark("fringe");
    await g.tap("G", 2); await g.gf(40);
    await dead(4, "the Dark Fringe");
    await g.walkTo(104);
    await g.jump("R", 10);
    await cross("R", 8); await settle();

    // 9 THE HINGE: the Drill Sergeant the size of a house in the Red, the
    // crystal bloom in the Blue, one heart. In from the Dark Fringe, in the
    // Red, onto the ledge, which the pillar shields from its gun; up onto the
    // pillar, over the gun's line, and two charges lobbed at the plate, which
    // dent it and crack it. Into the Blue on the pillar, where the crystal's
    // cracked open on the core; down onto the Blue's blocks, and the core
    // shot through the crack, through the Slivers the bloom sheds in front of
    // it. The swarm cleared, back up onto the pillar and into the Red for the
    // next round. Three bolts in the core, and the Hinge folds shut.
    await expectRoom(8, "THE HINGE");
    if (!(await beeb.peek("hinge_on"))) throw new Error("the Hinge isn't in its room");
    if ((await g.st()).cells < 8 || (await beeb.peek("grenades")) < 9) throw new Error("the fight started short of cells or charges");
    if ((await g.st()).phase !== 0) throw new Error("Ash came into the Hinge in the Blue");
    const round = async () => beeb.peek("hg_round");
    await g.walkTo(24); await g.jump("R", 12);
    if ((await g.st()).y !== 72) throw new Error("Ash missed the Hinge's pillar");
    let hingeFrames = 0, hingeVsyncs = 0;
    for (let r = 0; r < 3; r++) {
        await face("R");
        if (r === 0) await mark("hinge_red");
        await g.tap("G", 2); await g.gf(30);
        if ((await beeb.peek("hg_plate")) !== 1) throw new Error(`the Hinge's plate wasn't dented in round ${r + 1}`);
        if (r === 0) await mark("hinge_dent");
        await g.tap("G", 2); await g.gf(30);
        if (!(await beeb.peek("hg_open"))) throw new Error(`the Hinge's plate didn't crack in round ${r + 1}`);
        if (r === 0) await mark("hinge_cracked");
        await shift();
        if ((await g.st()).phase !== 1) throw new Error(`the shift into the Blue was refused in round ${r + 1}`);
        if (r === 0) { await g.gf(14); await mark("hinge_blue"); }
        await g.walkTo(46); await face("R");
        // (The frame rate while the core's shot through the swarm.)
        const f0 = await beeb.peek("frame"), v0 = await beeb.peek("vsyncs");
        await g.down("F");
        await until(async () => (await round()) > r || !(await beeb.peek("hg_open")), 200);
        if (r === 1) await mark("hinge_core");
        await g.up("F");
        hingeFrames += ((await beeb.peek("frame")) - f0) & 255; hingeVsyncs += ((await beeb.peek("vsyncs")) - v0) & 255;
        if ((await round()) <= r) throw new Error(`the Hinge's core wasn't hit in round ${r + 1}`);
        if (r === 2) break;
        await fight("the Hinge's swarm", 4, 5, 6, 7, 8, 9);
        await face("R");
        await g.jump("L", 12);
        if ((await g.st()).y !== 72) throw new Error(`Ash missed the pillar going back in round ${r + 1}`);
        await shift();
        if ((await g.st()).phase !== 0) throw new Error(`the shift back to the Red was refused in round ${r + 1}`);
        if (r === 0) await mark("hinge_ghosts");
    }
    console.log(`${"(frame rate)".padEnd(16)} ${hingeFrames} game frames in ${hingeVsyncs} VSyncs, the core shot through the swarm`);
    if (hingeFrames * 2 < hingeVsyncs - 2) throw new Error(`the Hinge dropped frames: ${hingeFrames} in ${hingeVsyncs} VSyncs`);
    // The ending: the Hinge folds shut, a column at a time, the Prism goes
    // dark a facet at a time, the lamps come up white, and the words.
    if (!(await beeb.peek("hg_won"))) throw new Error("the Hinge's core took its last bolt, but it wasn't beaten");
    await expectRoom(8, "THE HINGE");
    // (In VSyncs from the last bolt: the fold's columns, the facets, the dark
    // and the white, as src/endings.6502 times them.)
    await beeb.frames(40); await mark("hinge_fold");
    await beeb.frames(100); await mark("hinge_dark");
    await beeb.frames(130); await mark("hinge_white");
    const words = await beeb.runUntil("cards", 10);
    if (words.stopped_reason !== "breakpoint") throw new Error("the victory's words never came");
    await beeb.frames(20); await mark("ending");
    for (let card = 2; card <= 4; card++) {
        await g.tap("G", 2); await beeb.frames(10);
        if (card === 4) await mark("the_end");
    }
    await beeb.frames(50);
    await g.down("G");
    const again = await beeb.runUntil("game_start", 10);
    await g.up("G");
    if (again.stopped_reason !== "breakpoint") throw new Error("THE END didn't start a new game on a key");
    console.log(`${"THE END".padEnd(16)} and a new game`);
} catch (e) {
    console.log(`FAIL: ${e.message}`);
    console.log(`  (Ash: ${JSON.stringify(await g.st())})`);
    await beeb.close();
    process.exit(1);
}

await beeb.close();
