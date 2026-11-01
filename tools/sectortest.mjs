#!/usr/bin/env node
// A sector's load at the cage (src/sector.6502, decision 42), on one machine (make check runs
// it on each):
//
//   node tools/sectortest.mjs [--model B-DFS1.2] [--shots DIR]
//
// From the first room, with the cage's way down poked in (Sector 2's room 0) and the cage
// taken, it checks:
// - the game's memory the OS and the DFS write (the DFS's workspace, page 8) is back as it was;
// - the screen is black and the chip silent while the DFS runs;
// - Ash arrives in Sector 2, and the game keeps its frame rate there;
// - a death there brings the room back from the bank, not the disc;
// - a game over there loads Sector 1 again for the new game;
// - with a disc that has no S2, the screen says so; SPACE straight away gives the error again
//   (the DFS still has that disc's catalogue); and once the disc is back, SPACE loads it.
// And it says how long a load took, and how much the DFS wrote at SE_FILE (a DFS may write
// the whole of the file's last sector, and SE_FILE leaves room for that).
import { execFileSync } from "child_process";
import { readFileSync, writeFileSync } from "fs";
import { resolve } from "path";
import { startBeeb } from "./beeb.mjs";

const args = process.argv.slice(2);
const opt = (name, dflt) => { const i = args.indexOf(`--${name}`); return i >= 0 ? args[i + 1] : dflt; };
const model = opt("model", process.env.REDSHIFT_MODEL || "B-DFS1.2");
const SHOTS = opt("shots", null);
const DISC = "build/redshift.ssd";

const b = await startBeeb({ disc: DISC, bootUntil: "game_start", model, symbols: "build/redshift.json" });
let failed = false;
const fail = (msg) => { console.log(`FAIL (${model}): ${msg}`); failed = true; };
const say = (msg) => console.log(`${model}: ${msg}`);
const sym = (s) => b.addr(s);
const peek = (s) => b.peek(s);
const range = (lo, hi) => b.read(lo, hi - lo);
const same = (x, y) => x.length === y.length && x.every((v, i) => v === y[i]);
const text = (r) => r.content.find((c) => c.type === "text")?.text ?? "";
const shot = async (name) => {
    const f = resolve(SHOTS ?? "build", `sectortest_${name}.png`);
    await b.shot(f);
    return f;
};
// Whether a screenshot has anything on it that isn't black.
const lit = (file) => +execFileSync("python3", ["-c", `
from PIL import Image
print(int(Image.open("${file}").convert("L").getbbox() is not None))
`]).toString();
// A file in the disc's catalogue: where its name is, and its length.
const catalogue = (name) => {
    const ssd = readFileSync(DISC);
    for (let k = 8; k < 8 + ssd[0x105]; k += 8) {
        if (ssd.toString("latin1", k, k + 7).trimEnd() === name && (ssd[k + 7] & 0x7f) === 0x24) {
            const i = 0x100 + k;
            return { at: k, length: ssd[i + 4] | (ssd[i + 5] << 8) | (((ssd[i + 6] >> 4) & 3) << 16) };
        }
    }
    throw new Error(`no ${name} on ${DISC}`);
};
const until = async (test, frames = 600) => {
    for (let i = 0; i < frames; i += 5) { if (await test()) return true; await b.frames(5); }
    return test();
};
const arrived = async (sector) => (await peek("room")) === 0 && (await peek("room_sector")) === sector
    && (await peek("blackout")) === 0 && (await peek("pl_dead")) === 0;
// The cage's way down from the first room: Sector 2's room 0.
const takeCage = async () => {
    await b.write("room_exits", [0xff, 0xff, 0xff, sym("NEXT_SECTOR")]);
    await b.write("cage_go", [1]);
};
// Game frames over VSyncs, with keys held as in play.
const frameRate = async () => {
    const f0 = await peek("frame");
    for (const key of ["X", "Z"]) { await b.keyDown(key); await b.run(0.6); await b.keyUp(key); }
    const frames = ((await peek("frame")) - f0) & 255;
    if (frames * 2 < 60 - 4) fail(`${frames} game frames in 60 VSyncs`);
    return frames;
};

try {
    const work = [sym("DFS_WORK"), sym("DFS_WORK_END")], page8 = [sym("OS_SOUND"), sym("OS_SOUND") + 256];
    const file = sym("SE_FILE"), fileEnd = file + sym("ROOMS_PAGES") * 256;
    await b.frames(170);                                    // (Sector 1's card)

    // --- The cage, and the load -------------------------------------------------------------
    await takeCage();
    await b.runUntil("sector_load", 10);
    let cycles = 0;
    let r = await b.runUntil("sector_load.theirs", 10);
    cycles += r.cycles_run;
    const before = [await range(...work), await range(...page8)];
    await b.write(file, new Array(fileEnd - file).fill(0xa5));      // (to see what the DFS writes)
    r = await b.runUntil("osfile", 10);
    cycles += r.cycles_run;
    cycles += (await b.frames(10)).cycles_run;
    const mid = await shot("loading");
    if (lit(mid) !== 0) fail("the screen isn't black while the DFS runs");
    const chip = text(await b.call("read_sound_state", { session_id: b.session_id }));
    const vols = [...chip.matchAll(/vol=(\d+)/g)].map((m) => +m[1]);   // (attenuation: 15 is off)
    if (vols.length !== 4 || vols.some((v) => v !== 15)) fail(`the chip isn't silent while the DFS runs: ${vols}`);
    r = await b.runUntil("se_back.restored", 30);
    cycles += r.cycles_run;
    if (r.stopped_reason !== "breakpoint") throw new Error("the load never came back");
    const after = [await range(...work), await range(...page8)];
    if (!same(before[0], after[0])) fail("the DFS's workspace isn't the game's again after the load");
    if (!same(before[1], after[1])) fail("page 8 isn't the game's again after the load");
    r = await b.runUntil("sector_load.done", 10);
    cycles += r.cycles_run;
    say(`the load took ${cycles} cycles (${(cycles / 2e6).toFixed(2)}s)`);
    // (S2's bytes, and anything a DFS writes past them to its last sector's end.)
    const buf = await range(file, fileEnd);
    const written = buf.reduce((last, v, i) => (v !== 0xa5 ? i : last), -1) + 1;
    say(`the DFS wrote up to ${written} bytes at SE_FILE, for S2's ${catalogue("S2").length}`);
    if (written > catalogue("S2").length) say("(it wrote past the file: SE_FILE leaves room for that)");
    if ((await peek("loaded_sector")) !== 2) fail(`loaded_sector is ${await peek("loaded_sector")}, not 2`);
    if (!(await until(() => arrived(2), 400))) fail("Ash didn't arrive in Sector 2");
    if (SHOTS) await shot("arrived");
    say(`in Sector 2: ${await frameRate()} game frames in 60 VSyncs`);

    // --- A death there: the room from the bank ---------------------------------------------
    const lives = await peek("lives");
    await b.breakpoint("sector_load");
    await b.tap("ESCAPE", 0.1);
    r = await b.run(3);
    await b.clearBreakpoints();
    if (r.stopped_reason === "breakpoint") fail("a death in Sector 2 loaded from the disc");
    if ((await peek("lives")) !== lives - 1) fail(`lives ${await peek("lives")} after a death, from ${lives}`);
    if (!(await arrived(2))) fail("after a death, not back in Sector 2's room");

    // --- A game over there: Sector 1 again ---------------------------------------------------
    await b.write("lives", [1]);
    await b.tap("ESCAPE", 0.1);
    r = await b.runUntil("game_over.key", 20);
    await b.tap("SPACE", 0.1);
    r = await b.runUntil("sector_load.done", 20);
    if (r.stopped_reason !== "breakpoint") fail("a new game didn't load Sector 1");
    if (!(await until(() => arrived(1), 400))) fail("a new game didn't start in Sector 1's room 0");
    if ((await peek("lives")) !== sym("START_LIVES")) fail("a new game's lives");

    // --- A disc without S2 -------------------------------------------------------------------
    const ssd = readFileSync(DISC);
    ssd[catalogue("S2").at] = "X".charCodeAt(0);
    const wrong = resolve("build/sectortest_nos2.ssd");
    writeFileSync(wrong, ssd);
    await b.call("load_disc", { session_id: b.session_id, image_path: wrong, drive: 0 });
    await takeCage();
    r = await b.runUntil("se_error", 30);
    if (r.stopped_reason !== "breakpoint") throw new Error("no error from a disc without S2");
    r = await b.runUntil("se_error.wait", 10);
    const raw = await b.read("se_msg", 33);
    const msg = String.fromCharCode(...raw.slice(0, raw.indexOf(0)));
    say(`with no S2 on the disc, the screen says: ${msg}`);
    if (!/not found/i.test(msg)) fail(`the error's message: ${msg}`);
    await b.frames(5);
    const shown = await shot("error");
    if (lit(shown) === 0) fail("the error isn't on the screen");
    await b.frames(20);
    if ((await peek("loaded_sector")) !== 1) fail("the failed load changed loaded_sector");
    // SPACE at once, with the drive still spinning, so DFS 1.2 takes the catalogue it has: the
    // same error again. (Once, this hung in the DFS, searching the game's code as its catalogue.)
    await b.tap("SPACE", 0.1);
    r = await b.runUntil("se_error.wait", 30);
    if (r.stopped_reason !== "breakpoint") fail("a retry at once, with the same disc, didn't give the error again");
    // The disc back, a person's while later.
    await b.call("load_disc", { session_id: b.session_id, image_path: resolve(DISC), drive: 0 });
    await b.run(4);
    await b.tap("SPACE", 0.1);
    r = await b.runUntil("sector_load.done", 30);
    if (r.stopped_reason !== "breakpoint") fail("SPACE didn't load S2 once the disc was back");
    if (!(await until(() => arrived(2), 400))) fail("Ash didn't arrive in Sector 2 after the error");
    say(`in Sector 2 after the error: ${await frameRate()} game frames in 60 VSyncs`);
} catch (e) {
    fail(e.message);
} finally {
    await b.close();
}
process.exit(failed ? 1 : 0);
