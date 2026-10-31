#!/usr/bin/env node
// The smoke test (make check): boot past the title and the sector card,
// play a few seconds of keys, and check the game is still running and
// keeping up: game frames advance at one per two VSyncs, and the PC is
// in the game, not in the OS's BRK handler or off in the weeds.
//
//   node tools/smoke.mjs [--model B-DFS1.2]
import { startBeeb } from "./beeb.mjs";

const args = process.argv.slice(2);
const i = args.indexOf("--model");
const model = i >= 0 ? args[i + 1] : process.env.REDSHIFT_MODEL || "B-DFS1.2";
const b = await startBeeb({ disc: "build/redshift.ssd", bootUntil: "game_start", model, symbols: "build/redshift.json" });
let failed = false;
const fail = (msg) => { console.log(`FAIL (${model}): ${msg}`); failed = true; };
try {
    await b.frames(170);                            // the card
    // (frame is a byte: the run is under 10s, 250 game frames.)
    const f0 = await b.peek("frame");
    let secs = 0;
    // (Short of the first acid: a death redraws the room, a pause of its
    // own, and this checks the frames of play.)
    for (const [key, held] of [["X", 0.8], ["COLON_STAR", 0.3], ["RETURN", 1], ["SHIFT", 0.1], ["Z", 1], ["SPACE", 0.2]]) {
        await b.keyDown(key);
        await b.run(held);
        await b.keyUp(key);
        await b.run(0.2);
        secs += held + 0.2;
    }
    const frames = ((await b.peek("frame")) - f0) & 255, vsyncs = Math.round(secs * 50);
    console.log(`${model}: ${frames} game frames in ${vsyncs} VSyncs`);
    if (frames * 2 < vsyncs - 4) fail("the game fell behind (or stopped)");
    const pc = JSON.parse(await b.regs()).pc;
    if (pc >= 0x8000 && pc < 0xC000) fail(`PC in the sideways bank: &${pc.toString(16)}`);
    if (pc < 0x0E00 && !(pc >= 0x0100 && pc < 0x0200)) fail(`PC in low memory: &${pc.toString(16)}`);
    const room = await b.peek("room");
    if (room !== 0) fail(`in room ${room}, not the first`);
} finally {
    await b.close();
}
process.exit(failed ? 1 : 0);
