#!/usr/bin/env node
// The music as the game plays it (decision 30): every write to the sound
// chip for each piece, recorded in jsbeeb, checked against tools/mkmusic.py's
// model of the player, and rendered to a WAV through tools/snwav.py.
//
//   node tools/musiccap.mjs [outdir] [--model B-DFS1.2] [--quick]
//
// The title theme from the title page's loop (RSLOAD, the OS running);
// SECTOR 1's sting from the start of a game, as it runs on into the music
// under play; then, standing in the first room (kept safe from its
// enemies), each piece asked for in turn through the player's mu_req, the
// music under play once in each phase, and then again with Ash shifting
// every few seconds (play-shifting, recorded but not checked). Then M and
// P: the music silent, and back. Each piece's writes, a frame (a VSync) to
// a line, must be the
// model's (build/music-writes, which this makes). Logs (a CPU cycle and a
// byte a line, which tools/snwav.py reads) and WAVs go to outdir
// (build/music by default). --quick checks the first 20 seconds of each.
import { execFileSync } from "child_process";
import { mkdirSync, readFileSync, writeFileSync } from "fs";
import { startBeeb } from "./beeb.mjs";

const args = process.argv.slice(2);
const opt = (name, dflt) => {
    const i = args.indexOf(`--${name}`);
    if (i < 0) return dflt;
    const v = args[i + 1];
    args.splice(i, 2);
    return v;
};
const quick = args.includes("--quick");
if (quick) args.splice(args.indexOf("--quick"), 1);
const model = opt("model", process.env.REDSHIFT_MODEL || "B-DFS1.2");
const out = args[0] ?? "build/music";
mkdirSync(out, { recursive: true });
// CPU cycles a VSync: MODE 7's interlaced frame on the title page, and the
// game's 312 lines of 64us.
const TITLE_FRAME = 40000, GAME_FRAME = 312 * 128;

// The model's writes for each piece (python3 tools/mkmusic.py --writes).
const MUSIC = ["music/instruments.txt", "music/cards.txt", "music/play.txt", "music/over.txt"];
execFileSync("python3", ["tools/mkmusic.py", "build/music-writes/game.6502", ...MUSIC, "--writes", "build/music-writes"]);
execFileSync("python3", ["tools/mkmusic.py", "build/music-writes/title.6502", "music/instruments.txt", "music/title.txt",
    "--writes", "build/music-writes"]);
const expected = (name) => readFileSync(`build/music-writes/${name}.txt`, "utf8").split("\n")
    .slice(0, -1).map((l) => l.split(" ").filter(Boolean).map((h) => parseInt(h, 16)));

const b = await startBeeb({ disc: "build/redshift.ssd", symbols: "build/redshift.json", model });
let failed = false;
const fail = (msg) => { console.log(`FAIL (${model}): ${msg}`); failed = true; };

async function capture(secs, during) {
    await b.call("start_sound_capture", { session_id: b.session_id });
    if (during) await during();
    for (let left = secs; left > 0; left -= 5) {
        // (Kept safe: the first room's enemies would kill a player who stands still.)
        if (b.syms.pl_safe) await b.write("pl_safe", [250]);
        await b.run(Math.min(5, left));
    }
    const r = await b.call("stop_sound_capture", { session_id: b.session_id, max_entries: 1000000 });
    const text = r.content.find((c) => c.type === "text").text;
    return [...text.matchAll(/^(\d+): 0x([0-9a-f]{2})/gm)].map((m) => [+m[1], parseInt(m[2], 16)]);
}

// The writes in frames: each write's frame counted from the first's.
function frames(writes, period) {
    const out = [];
    if (!writes.length) return out;
    const t0 = writes[0][0];
    for (const [c, v] of writes) {
        const f = Math.floor((c - t0 + period / 4) / period);
        while (out.length <= f) out.push([]);
        out[f].push(v);
    }
    return out;
}

// The model's frames from the piece's start (its first writes) against the
// emulator's from the frame that wrote the same: before it, the game may
// have written other things (the music's first silence after start-up).
function check(name, got, want, secs, period = GAME_FRAME) {
    const n = Math.min(want.length, Math.round(secs * 50));
    const first = want.findIndex((w) => w.length);
    const g = frames(got, period);
    const start = g.findIndex((w) => w.join(" ") === want[first].join(" "));
    if (start < 0 || start > 10) {
        fail(`${name}: the piece never started (wanted [${want[first].join(" ")}])`);
        return;
    }
    for (let f = 0; f < n - first; f++) {
        const a = (g[start + f] ?? []).join(" "), e = (want[first + f] ?? []).join(" ");
        if (a !== e) {
            fail(`${name}: frame ${first + f} wrote [${a}], the model [${e}]`);
            return;
        }
    }
    console.log(`${name}: ${n - first} frames as the model plays them`);
}

function save(name, writes) {
    writeFileSync(`${out}/${name}.log`, writes.map(([c, v]) => `${c} ${v.toString(16).padStart(2, "0")}`).join("\n") + "\n");
    execFileSync("python3", ["tools/snwav.py", `${out}/${name}.log`, `${out}/${name}.wav`]);
}

const secsOf = (name) => expected(name).length / 50;
const len = (name) => (quick ? Math.min(20, secsOf(name)) : secsOf(name));
try {
    // The title page.
    await b.boot();
    await b.runUntil("rsload.space");
    await b.clearBreakpoints();
    let w = await capture(len("title"));
    check("title", w, expected("title"), len("title"), TITLE_FRAME);
    save("title", w);

    // SPACE: the game, and SECTOR 1's card.
    await b.tap("SPACE", 0.1);
    await b.runUntil("game_start");
    w = await capture(len("card1"));
    check("card1", w, expected("card1"), len("card1"));
    save("card1", w);
    await b.run(2);

    // Each piece from its start, standing still in the first room.
    const req = b.addr("mus.mu_req");
    const piece = async (name, number) => {
        w = await capture(len(name), () => b.write(req, [number]));
        check(name, w, expected(name), len(name));
        save(name, w);
    };
    for (let n = 2; n <= 5; n++) await piece(`card${n}`, b.addr(`mus.MUS_CARD${n}`));
    await piece("over", b.addr("mus.MUS_OVER"));
    await piece("play", b.addr("mus.MUS_PLAY"));
    // Into the Blue (its own sound first), then the same again.
    await b.tap("SHIFT", 0.1);
    await b.run(1);
    if ((await b.peek("phase")) !== 1) fail("SHIFT didn't shift");
    await piece("play-blue", b.addr("mus.MUS_PLAY"));

    // Back and forth, as a player shifts: the music follows, from where it
    // is (no model of this: the shifts land where they land).
    await b.tap("SHIFT", 0.1);
    await b.run(1);
    await b.call("start_sound_capture", { session_id: b.session_id });
    await b.write(req, [b.addr("mus.MUS_PLAY")]);
    for (let i = 0; i < (quick ? 2 : 8); i++) {
        await b.write("pl_safe", [250]);
        await b.write("cells", [5]);
        await b.run(5);
        await b.tap("SHIFT", 0.1);
    }
    await b.run(2);
    const r = await b.call("stop_sound_capture", { session_id: b.session_id, max_entries: 1000000 });
    w = [...r.content.find((c) => c.type === "text").text.matchAll(/^(\d+): 0x([0-9a-f]{2})/gm)]
        .map((m) => [+m[1], parseInt(m[2], 16)]);
    save("play-shifting", w);
    console.log("play-shifting: recorded");
    if ((await b.peek("phase")) !== 0) await b.tap("SHIFT", 0.1);

    // M: silent, though it plays on; and back. P the same, but it stops.
    for (const key of ["M", "P"]) {
        await b.tap(key, 0.1);
        await b.run(0.5);
        w = await capture(3);
        const sounding = w.filter(([, v]) => (v & 0x90) === 0x90 && (v & 15) !== 15);
        if (sounding.length) fail(`${key}: the music wrote a volume while off: ${sounding.length} times`);
        await b.tap(key, 0.1);
        w = await capture(3);
        if (!w.some(([, v]) => (v & 0x90) === 0x90 && (v & 15) !== 15)) fail(`${key}: the music didn't come back`);
        else console.log(`${key}: silent, then back`);
    }
} finally {
    await b.close();
}
process.exit(failed ? 1 : 0);
