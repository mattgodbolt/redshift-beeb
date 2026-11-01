#!/usr/bin/env node
// A playthrough of Sectors 1 to 3, from the first room to each sector's
// cage, each next sector's load from the disc, and Sector 4's first room, on
// the default build: the end-to-end test that the sectors can be finished
// without losing a life, and with --shots, the README's screenshots.
//
//   node tools/playthrough.mjs               play it, and fail if a room isn't reached,
//                                            a life is lost, a sergeant lives or a switch
//                                            isn't thrown
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
    // the Trundler off, shoot it, through the crystal's ghost for the cell,
    // and down through the trapdoor, which is the Blue's.
    await expectRoom(1, "THE CISTERN");
    await g.walkTo(12);
    await shift();
    await fireAt("the Cistern's Slivers", 4, 5, 6, 7);
    await mark("cistern");
    await g.walkTo(36);
    await g.jump("R", 14);
    await g.land();
    await until(async () => Math.abs((await thing(8)).x - (await g.st()).x) > 24, 300);
    {
        const t = await thing(8), s = await g.st();
        await shift();
        await face(t.x < s.x ? "L" : "R");
    }
    if (!(await fireUntilDead(8, 150))) throw new Error("the Cistern's Trundler lived");
    await g.walkTo(18);
    if ((await thing(9)).alive) throw new Error("the Cistern's cell wasn't taken");
    await g.walkUntilRoom("R", 2, 300); await settle(); await g.land();
    // 3 BOILER WALK: boiler to boiler over the boiling gaps. Shoot the
    // Trundler on the middle one, over, up onto its steam dome, out of the
    // sergeant's fire, and a charge lobbed at it; over to the welded door,
    // into the Blue there, and the Slivers behind it.
    await expectRoom(2, "BOILER WALK");
    await g.walkTo(104);
    await face("L");
    if (!(await fireUntilDead(5, 150))) throw new Error("the Boiler Walk's Trundler lived");
    await g.jump("L", 14);
    await g.walkTo(80);
    await g.jump("L", 8);
    await mark("boiler");
    await g.tap("G", 2); await g.gf(40);
    await dead(4, "the Boiler Walk");
    await g.walkTo(56);
    await g.jump("L", 24);
    await g.walkTo(20);
    await shift();
    await fireAt("the Boiler Walk's Slivers", 6, 7);
    await cross("L", 3); await settle(); await g.land();
    // 4 STEAM TRAP, the Red's road: Blue blocks bar the corridor, so back to
    // the Red at the way in; then the vents steam in turn on the beat, and
    // Ash goes from pocket to pocket as each stops, and into the shaft.
    await expectRoom(3, "STEAM TRAP");
    await g.walkTo(108);
    await shift();
    await frameRate("the vents steaming");
    await until(async () => (await beat()) === 0, 200);
    await until(async () => (await beat()) === 1, 200);
    await g.walkTo(80);
    await until(async () => (await beat()) === 0, 200);
    await g.walkTo(52);
    await mark("steam");
    await until(async () => (await beat()) === 1, 200);
    await g.walkTo(24);
    await until(async () => (await beat()) === 0, 200);
    await g.walkUntilRoom("L", 4, 200); await settle(); await g.land();
    // 5 DROWNED OFFICE: shoot the Trundler on the shelf, up onto the filing
    // cabinet, out of the sergeant's fire, and a charge lobbed at it; over to
    // its landing, into the Blue, and over the span to the door.
    await expectRoom(4, "DROWNED OFFICE");
    await face("R");
    if (!(await fireUntilDead(4, 150))) throw new Error("the Drowned Office's Trundler lived");
    await g.walkTo(8);
    await g.jump("R", 10);
    await g.walkTo(26);
    await g.jump("R", 6);
    await g.walkTo(31);
    await mark("office");
    await g.tap("G", 2); await g.gf(40);
    await dead(5, "the Drowned Office");
    await g.jump("R", 10);
    await g.walkTo(50);
    await g.jump("R", 14);
    await g.walkTo(82);
    await shift();
    await cross("R", 5); await settle();
    // 6 SLUICE GATE: in the Blue, down into the dry bed; the gate's handle
    // shot, which lifts the gate and drains the sump in both phases, and the
    // swarm the gate held back; on to the culvert's crystal, back to the Red
    // in the drained bed, the Trundler beyond, over the kerb and down.
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
    await fireAt("the Sluice Gate's Slivers", 6, 7, 8);
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
    await fireAt("the U-Bend's Slivers", 4, 5, 6, 7);
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
    // baffles of the Blue's hang over it. Down onto the first depth post,
    // and along the walkway while the flood's down, post to post; into the
    // Blue on the last, where the Slivers come over the basin, and up the
    // Blue's steps over it to the way out.
    await expectRoom(7, "OVERFLOW");
    await g.walkTo(106); await g.land();
    await frameRate("the sump flooding the walkway");
    await until(async () => (await beat()) === 1, 300);
    await until(async () => (await beat()) === 0, 300);
    await g.walkTo(86);
    await g.jump("L", 8);
    await mark("overflow");
    await until(async () => (await beat()) === 1, 300);
    await until(async () => (await beat()) === 0, 300);
    await g.walkTo(60);
    await g.jump("L", 8);
    await shift();
    await face("L");
    await fireAt("the Overflow's Slivers", 4, 5);
    await g.jump("L", 14);
    await g.jump("L", 14);
    await g.jump("L", 10);
    await g.jump("L", 20);
    await cross("L", 8); await settle();
    // 9 THE PLUGHOLE: a pack of charges on the bank; in the Blue, Slivers
    // come over the dry basin; across it and down the plughole while the
    // plug's drawn up, onto the crate under it; back to the Red there, out of
    // the Drill Sergeant's fire, a charge lobbed at it, and through the
    // crystal to THE CAGE.
    await expectRoom(8, "THE PLUGHOLE");
    await g.walkTo(108);
    await face("L");
    await fireAt("the Plughole's Slivers", 6, 7, 8);
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
    await g.walkTo(56);
    await g.down("L");
    await rideCage(4);
    await g.up("L");
    await g.gf(20); await mark("sector4");
    await until(async () => (await beeb.peek("room_sector")) === 4 && (await beeb.peek("blackout")) === 0, 200);
    await expectRoom(0, "THE END, FOR NOW");
    await g.gf(25);
} catch (e) {
    console.log(`FAIL: ${e.message}`);
    console.log(`  (Ash: ${JSON.stringify(await g.st())})`);
    await beeb.close();
    process.exit(1);
}

await beeb.close();
