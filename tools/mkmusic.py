#!/usr/bin/env python3
"""REDSHIFT's music (music/*.txt) as data for its player (src/musicplay.6502).

    mkmusic.py <out.6502> <score.txt>... [--preview DIR] [--writes DIR]

The scores are text; the first lines of music/instruments.txt say how
they're written. Each output holds the pieces of the scores it's given,
numbered in order (MUS_<NAME>), and the instruments, drums and pitches
they use. --preview renders each piece to DIR/<name>.wav (and a phased
piece's Blue to <name>-blue.wav) from a model of the player, through
tools/snwav.py's chip; --writes saves the model's chip writes, a frame
per line, for tools/musiccap.mjs to check the emulator's against.

The events (a byte from &C0 a wait, &FE a stretch played from elsewhere,
&FF the end) and the envelopes follow chuckie-egg-2-beeb's
tools/mkmusic.py and src/music.6502 (MIT licence, Matt Godbolt's), which
arrange MIDI files; these are scores written for the chip.

The data, all indexed (so the player needs only its event pointer in
zero page):
    mu_envs             the envelopes: a byte a step, the attenuation in
                        the low four bits and the frames in the top four
                        (0: held until the next note); step 0 is silence
    ins_env, ins_flags  each instrument's first step, and MUI_BLIP (its
                        notes start an octave up for a frame)
    drum_ctl, drum_ins  each drum's noise control and instrument
    per_lo, per_hi      each pitch's period: the low four bits, the top six
    var_speed, var_base a variant's frames a row and its first pitch
    var_ins, var_quiet  ... and four bytes each: the instrument and the
                        attenuation added for channels 0, 1, 2 and noise
    piece_var           a piece's variant (a phased piece's Red; its Blue
                        is the next)
    piece_flags         MUP_PHASED
    piece_next          what follows it (itself to loop), &FF: nothing
    piece_lo, piece_hi  its order list: &FE p (play pattern p) ..., &FF
    pat_lo, pat_hi      each pattern's events, ending &FD:
        00-BF   a note: the channel in the top two bits, the pitch (from
                the variant's base) below; 63 silences the channel
        C0-EF   the next events are (byte - &BF) rows on
        F0-F7   drum (byte - &F0) on the noise channel
        F8      the noise channel silenced
        F9 b    channel (b >> 6) plays instrument (b & 63) from now on (two
                voices on a channel: before the first note of each in a
                pattern, and wherever the voice changes)
"""
import argparse
import copy
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

NOTE = re.compile(r"^([A-G])([#b]?)(\d)$")
SEMI = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
CHANNELS = {"0": 0, "1": 1, "2": 2, "noise": 3}
NOISE_RATE = {"hi": 0, "mid": 1, "lo": 2}
PHRYGIAN = {0, 1, 3, 5, 7, 8, 10}       # a phased piece's Red
FIXED = {0, 7}                          # ... the degrees the Blue keeps
REST, MAX_WAIT = 63, 48
MUI_BLIP, MUP_PHASED = 1, 1
FPS = 50


class ScoreError(Exception):
    pass


def midi(name):
    m = NOTE.match(name)
    if not m:
        return None
    n = 12 * (int(m[3]) + 1) + SEMI[m[1]] + {"#": 1, "b": -1, "": 0}[m[2]]
    return n


def period(m):
    return round(125000 / (440 * 2 ** ((m - 69) / 12)))


class Piece:
    def __init__(self, name, where):
        self.name, self.where = name, where
        self.speed = None
        self.speed_blue = None
        self.bar = None
        self.then = "stop"
        self.tonic = None               # phased: the Red is <tonic> Phrygian
        self.voices = {}                # name -> dict(ch, ins, quiet, blue_ins, blue_quiet, up)
        self.patterns = {}              # name -> {voice: [tokens]}
        self.play = []
        self.parent = None              # "from": the piece whose notes it plays


def parse(paths):
    instruments, drums, pieces = {}, {}, []
    for path in paths:
        piece = pattern = None
        for lineno, raw in enumerate(open(path), 1):
            where = f"{path}:{lineno}"
            line = raw.strip()
            if not line or line.startswith("#"):
                continue

            def err(msg):
                raise ScoreError(f"{where}: {msg}")
            words = line.split()
            key = words[0]
            if key.endswith(":"):
                if pattern is None:
                    err("a voice's line outside a pattern")
                v = key[:-1]
                if v not in piece.voices:
                    err(f"no voice {v} in {piece.name}")
                pattern.setdefault(v, []).append((words[1:], where))
                continue
            if key == "instrument":
                steps, flags = [], 0
                for w in words[2:]:
                    if w == "blip":
                        flags |= MUI_BLIP
                    elif ":" in w:
                        a, f = w.split(":")
                        steps.append((int(a), int(f)))
                    else:
                        steps.append((int(w), 0))
                if not steps or steps[-1][1] != 0:
                    err("an instrument ends with a held step (an attenuation alone)")
                if any(not 0 <= a <= 15 or f < 0 for a, f in steps):
                    err("an attenuation is 0-15")
                instruments[words[1]] = (steps, flags)
            elif key == "drum":
                if words[2] not in NOISE_RATE:
                    err(f"a drum's noise is one of {', '.join(NOISE_RATE)}")
                drums[words[1]] = (4 | NOISE_RATE[words[2]], words[3])
            elif key == "piece":
                piece = Piece(words[1], where)
                pattern = None
                pieces.append(piece)
            elif piece is None:
                err(f"{key} outside a piece")
            elif key == "speed":
                piece.speed = int(words[1])
                piece.speed_blue = int(words[2]) if len(words) > 2 else piece.speed
            elif key == "bar":
                piece.bar = int(words[1])
            elif key == "then":
                piece.then = words[1]
            elif key == "phased":
                piece.tonic = midi(words[1] + "4") % 12
            elif key == "from":
                parent = next((q for q in pieces if q.name == words[1] and not q.parent), None)
                if parent is None or piece.patterns or piece.voices:
                    err(f"from: an earlier piece's notes ({words[1]}?), before anything else")
                piece.parent = parent.name
                piece.speed, piece.speed_blue, piece.bar = parent.speed, parent.speed_blue, parent.bar
                piece.tonic, piece.patterns, piece.play = parent.tonic, parent.patterns, parent.play
                piece.then = parent.then
                piece.voices = copy.deepcopy(parent.voices)
            elif key == "voice":
                if words[2] not in CHANNELS:
                    err("a voice's channel is 0, 1, 2 or noise")
                v = dict(ch=CHANNELS[words[2]], ins=None, quiet=0, up=0)
                rest = words[3:]
                if v["ch"] != 3:
                    v["ins"] = rest.pop(0)
                v.update(options(rest, err))
                v["blue_ins"], v["blue_quiet"] = v["ins"], v["quiet"]
                if piece.parent:
                    was = piece.voices.get(words[1]) or err(f"{piece.parent} has no voice {words[1]}")
                    if was["ch"] != v["ch"]:
                        err(f"{words[1]} plays on channel {was['ch']} in {piece.parent}")
                    v["up"] = was["up"]
                piece.voices[words[1]] = v
            elif key == "blue":
                v = piece.voices.get(words[1]) or err(f"no voice {words[1]}")
                rest = words[2:]
                if rest and rest[0] not in ("quiet", "up"):
                    v["blue_ins"] = rest.pop(0)
                o = options(rest, err)
                v["blue_quiet"] = o.get("quiet", v["quiet"])
                if piece.parent and o.get("up", v["up"]) != v["up"]:
                    err("a piece played from another keeps its transpositions")
                v["up"] = o.get("up", v["up"])
            elif key in ("pattern", "play") and piece.parent:
                err(f"{piece.name} plays {piece.parent}'s notes: only its voices change")
            elif key == "pattern":
                pattern = piece.patterns.setdefault(words[1], {})
            elif key == "play":
                piece.play += words[1:]
            else:
                err(f"what's {key}?")
    return instruments, drums, pieces


def options(words, err):
    out = {}
    while words:
        k = words.pop(0)
        if k not in ("quiet", "up") or not words:
            err(f"what's {k}?")
        out[k] = int(words.pop(0))
    return out


def rows_of(piece, pname, voice, lines, drums):
    """A voice's tokens in a pattern, a row each, the bar lines checked."""
    tokens = []
    for words, where in lines:
        bar = 0
        for w in words:
            if w == "|":
                if piece.bar and bar != piece.bar:
                    raise ScoreError(f"{where}: {voice}'s bar in {pname} is {bar} rows, not {piece.bar}")
                bar = 0
                continue
            bar += 1
            if w in (".", "-"):
                tokens.append(w)
            elif piece.voices[voice]["ch"] == 3:
                if w not in drums:
                    raise ScoreError(f"{where}: no drum {w}")
                tokens.append(w)
            elif midi(w) is None:
                raise ScoreError(f"{where}: what's {w}?")
            else:
                tokens.append(midi(w))
        if bar and piece.bar and bar != piece.bar:
            raise ScoreError(f"{where}: {voice}'s last bar in {pname} is {bar} rows, not {piece.bar}")
    return tokens


def blue_of(piece, note, up):
    if piece.tonic is None:
        return note
    rel = (note - piece.tonic) % 12
    return note + (0 if rel in FIXED else 1) + up


def build(instruments, drums, pieces):
    """Everything the player reads, as named lists of bytes, plus the
    pieces' names in order."""
    names = [p.name for p in pieces]
    used_ins, used_drums = [], []

    def ins_index(name, where):
        if name not in instruments:
            raise ScoreError(f"{where}: no instrument {name}")
        if name not in used_ins:
            used_ins.append(name)
        return used_ins.index(name)

    def variants(p, bases):
        """A variant for each pitch table: the piece's speed and instruments."""
        first = len(var)
        for blue, base in enumerate(bases):
            ins, quiet = [0] * 4, [0] * 4
            for v, vo in reversed(list(p.voices.items())):      # (a channel's first voice)
                name = vo["blue_ins" if blue else "ins"]
                if name is not None:
                    ins[vo["ch"]] = ins_index(name, p.where)
                quiet[vo["ch"]] = vo["blue_quiet" if blue else "quiet"]
            var.append(dict(speed=p.speed_blue if blue else p.speed, base=base, ins=ins, quiet=quiet))
        return first

    def follower(p):
        return 0xFF if p.then == "stop" else names.index(p.name if p.then == "loop" else p.then)

    per, var, pieces_out, pats, built = [], [], [], [], {}
    for p in pieces:
        if p.parent:
            # Another's notes, pitches and order, on its own instruments.
            b = built[p.parent]
            pieces_out.append(dict(b, name=p.name, var=variants(p, b["bases"]), next=follower(p)))
            continue
        if p.speed is None:
            raise ScoreError(f"{p.where}: {p.name} has no speed")
        if p.then not in ("loop", "stop") and p.then not in names:
            raise ScoreError(f"{p.where}: {p.name} is followed by no piece {p.then}")
        if not p.play:
            raise ScoreError(f"{p.where}: {p.name} plays nothing")
        # Each pattern's rows.
        grids = {}
        for pname, lines in p.patterns.items():
            grid = {v: rows_of(p, pname, v, ls, drums) for v, ls in lines.items()}
            lengths = {len(t) for t in grid.values()}
            if len(lengths) != 1:
                raise ScoreError(f"{p.where}: {p.name}'s pattern {pname}: the voices' lengths differ: "
                                 + ", ".join(f"{v} {len(t)}" for v, t in grid.items()))
            grids[pname] = grid
        # The pitches: a phased piece's by (its voice's Blue transposition, note).
        keys = set()
        for grid in grids.values():
            for v, toks in grid.items():
                vo = p.voices[v]
                for t in toks:
                    if isinstance(t, int):
                        if p.tonic is not None and (t - p.tonic) % 12 not in PHRYGIAN:
                            raise ScoreError(f"{p.where}: {p.name} is phased, and its Red has a note "
                                             f"outside the Phrygian mode: {t}")
                        keys.add((vo["up"] if p.tonic is not None else 0, t))
        keys = sorted(keys, key=lambda k: (k[1], k[0]))
        if len(keys) > REST:
            raise ScoreError(f"{p.where}: {p.name} has more than {REST} pitches")
        index = {k: i for i, k in enumerate(keys)}
        tables = [[n for _, n in keys]]
        if p.tonic is not None:
            tables.append([blue_of(p, n, up) for up, n in keys])
        bases = []
        for table in tables:
            bases.append(len(per))
            per += [period(n) for n in table]
        first_var = variants(p, bases)
        # Voices that share a channel play at its loudness, and say which
        # instrument they are.
        sharing = {}
        for v, vo in p.voices.items():
            sharing.setdefault(vo["ch"], []).append(v)
        for ch, vs in sharing.items():
            if len({(p.voices[v]["quiet"], p.voices[v]["blue_quiet"]) for v in vs}) > 1:
                raise ScoreError(f"{p.where}: {p.name}'s voices on channel {ch} differ in quiet")
            if len(vs) > 1 and p.tonic is not None:
                raise ScoreError(f"{p.where}: {p.name} is phased, so its voices can't share channel {ch}")
        # The patterns' events.
        pat_index = {}
        for pname in dict.fromkeys(p.play):
            if pname not in grids:
                raise ScoreError(f"{p.where}: {p.name} plays no pattern {pname}")
            grid = grids[pname]
            length = len(next(iter(grid.values())))
            ev, gap, last = [], 0, {}
            for r in range(length):
                now, struck = [], set()
                for v, toks in sorted(grid.items(), key=lambda kv: p.voices[kv[0]]["ch"]):
                    vo, t = p.voices[v], toks[r]
                    ch = vo["ch"]
                    if t == ".":
                        continue
                    if ch in struck:
                        raise ScoreError(f"{p.where}: {p.name}'s pattern {pname}, row {r}: "
                                         f"two voices strike channel {ch}")
                    struck.add(ch)
                    if len(sharing[ch]) > 1 and ch != 3 and t != "-" and last.get(ch) != v:
                        now += [0xF9, ch << 6 | ins_index(vo["ins"], p.where)]
                        last[ch] = v
                    if ch == 3:
                        if t == "-":
                            now.append(0xF8)
                        else:
                            if t not in used_drums:
                                used_drums.append(t)
                            now.append(0xF0 + used_drums.index(t))
                    elif t == "-":
                        now.append(ch << 6 | REST)
                    else:
                        key = (vo["up"] if p.tonic is not None else 0, t)
                        now.append(ch << 6 | index[key])
                if now:
                    ev += waits(gap)
                    ev += now
                    gap = 0
                gap += 1
            ev += waits(gap) + [0xFD]
            pat_index[pname] = len(pats)
            pats.append(ev)
        order = []
        for pname in p.play:
            order += [0xFE, pat_index[pname]]
        order.append(0xFF)
        built[p.name] = dict(bases=bases, flags=MUP_PHASED if p.tonic is not None else 0,
                             order=order, label=f"mus_{p.name}")
        pieces_out.append(dict(built[p.name], name=p.name, var=first_var, next=follower(p)))
    if len(per) > 256 or len(pats) > 256 or len(used_drums) > 8:
        raise ScoreError("too many pitches, patterns or drums")
    for d in used_drums:
        ins_index(drums[d][1], "drum " + d)
    # The envelopes, step 0 silence.
    envs, ins_env, ins_flags = [0x0F], [], []
    for name in used_ins:
        steps, flags = instruments[name]
        ins_env.append(len(envs))
        ins_flags.append(flags)
        for a, f in steps:
            while f > 15:
                envs.append(15 << 4 | a)
                f -= 15
            envs.append(f << 4 | a)
    if len(envs) > 256:
        raise ScoreError("the envelopes are more than 256 steps")
    return dict(
        names=names, envs=envs, ins_env=ins_env, ins_flags=ins_flags, used_ins=used_ins,
        drum_ctl=[drums[d][0] for d in used_drums], drum_ins=[used_ins.index(drums[d][1]) for d in used_drums],
        used_drums=used_drums, per=per, var=var, pieces=pieces_out, pats=pats)


def waits(rows):
    out = []
    while rows > 0:
        n = min(rows, MAX_WAIT)
        out.append(0xBF + n)
        rows -= n
    return out


def eqb(values, per=16):
    values = list(values)
    if not values:
        return "    \\ (none)"
    return "\n".join("    EQUB " + ", ".join(f"&{v & 0xFF:02X}" for v in values[i:i + per])
                     for i in range(0, len(values), per))


def emit(d, sources):
    out = [f"\\ Made by tools/mkmusic.py from {', '.join(sources)}: don't edit.", ""]
    for i, name in enumerate(d["names"]):
        out.append(f"MUS_{name.upper()} = {i}")
    out += ["", "\\ The instruments: " + ", ".join(d["used_ins"]) + ".", ".mu_envs", eqb(d["envs"]),
            ".ins_env", eqb(d["ins_env"]), ".ins_flags", eqb(d["ins_flags"]),
            "\\ The drums: " + (", ".join(d["used_drums"]) or "none") + ".",
            ".drum_ctl", eqb(d["drum_ctl"]), ".drum_ins", eqb(d["drum_ins"]),
            ".per_lo", eqb(n & 15 for n in d["per"]), ".per_hi", eqb(n >> 4 for n in d["per"]),
            ".var_speed", eqb(v["speed"] for v in d["var"]), ".var_base", eqb(v["base"] for v in d["var"]),
            ".var_ins", eqb(sum((v["ins"] for v in d["var"]), [])),
            ".var_quiet", eqb(sum((v["quiet"] for v in d["var"]), [])),
            ".piece_var", eqb(p["var"] for p in d["pieces"]),
            ".piece_flags", eqb(p["flags"] for p in d["pieces"]),
            ".piece_next", eqb(p["next"] for p in d["pieces"]),
            ".piece_lo", "    EQUB " + ", ".join(f"LO({p['label']})" for p in d["pieces"]),
            ".piece_hi", "    EQUB " + ", ".join(f"HI({p['label']})" for p in d["pieces"]),
            ".pat_lo", "    EQUB " + ", ".join(f"LO(mpat_{i})" for i in range(len(d["pats"]))),
            ".pat_hi", "    EQUB " + ", ".join(f"HI(mpat_{i})" for i in range(len(d["pats"])))]
    for p in d["pieces"]:
        if p["label"] == f"mus_{p['name']}":
            out += [f".mus_{p['name']}", eqb(p["order"])]
    for i, ev in enumerate(d["pats"]):
        out += [f".mpat_{i}", eqb(ev)]
    return "\n".join(out) + "\n"


class Model:
    """The player (src/musicplay.6502), step for step, for the previews and
    for checking the emulator against: frame() returns that frame's chip
    writes. Every channel free (no game sounds), as at the title and the
    sector cards."""

    def __init__(self, d):
        self.d = d
        self.req, self.newphase, self.phase, self.piece = 0xFF, 0, 0, 0xFF
        self.free, self.dirty = 15, 0
        self.speed = self.base = self.tick = self.rows = 0
        self.ptr, self.ret, self.where = 0, 0, None
        self.note, self.env, self.cnt, self.att = [0xFF] * 4, [0] * 4, [0] * 4, [15] * 4
        self.ins, self.quiet = [0] * 4, [0] * 4
        self.out = []
        self.ends = 0               # pieces it has come to the end of

    # The event stream: ("order", piece) or ("pat", n), with an offset.
    def byte(self):
        kind, i = self.where
        data = self.d["pieces"][i]["order"] if kind == "order" else self.d["pats"][i]
        v = data[self.ptr]
        self.ptr += 1
        return v

    def write(self, v):
        self.out.append(v)

    def silence_voice(self, x):
        self.note[x], self.env[x], self.cnt[x], self.att[x] = 0xFF, 0, 0, 15

    def begin(self, piece):
        self.piece = piece
        self.where, self.ptr = ("order", piece), 0
        self.phase = self.newphase
        self.variant()

    def variant(self):
        p = self.d["pieces"][self.piece]
        v = self.d["var"][p["var"] + (p["flags"] & self.phase)]
        self.speed, self.base = v["speed"], v["base"]
        self.ins, self.quiet = list(v["ins"]), list(v["quiet"])

    def load_step(self, x):
        e = self.d["envs"][self.env[x]]
        self.att[x], self.cnt[x] = e & 15, e >> 4

    def write_vol(self, x):
        self.write(min(15, self.att[x] + self.quiet[x]) | (0x90 + 0x20 * x))

    def volume(self, x):
        if self.free & (1 << x):
            self.write_vol(x)
        else:
            self.dirty |= 1 << x

    def write_note(self, x, half=False):
        if self.note[x] == 0xFF:
            return
        if x == 3:
            self.write(0xE0 | self.note[x])
            return
        n = self.d["per"][self.note[x] + self.base]
        if half:
            n >>= 1
        self.write(0x80 | x << 5 | n & 15)
        self.write(n >> 4)

    def strike(self, x, a):
        if a == REST:
            self.silence_voice(x)
            if self.free & (1 << x):
                self.write_vol(x)
            else:
                self.dirty |= 1 << x
            return
        self.note[x] = a
        self.env[x] = self.d["ins_env"][self.ins[x]]
        self.load_step(x)
        if not self.free & (1 << x):
            self.dirty |= 1 << x
            return
        if self.d["ins_flags"][self.ins[x]] & MUI_BLIP and x != 3:
            self.write_note(x, half=True)
            self.dirty |= 1 << x
        else:
            self.write_note(x)
        self.write_vol(x)

    def events(self):
        while True:
            b = self.byte()
            if b < 0xC0:
                self.strike(b >> 6, b & 63)
            elif b < 0xF0:
                self.rows = b - 0xBF
                return
            elif b < 0xF8:
                k = b & 7
                self.ins[3] = self.d["drum_ins"][k]
                self.strike(3, self.d["drum_ctl"][k])
            elif b == 0xF8:
                self.strike(3, REST)
            elif b == 0xF9:
                b = self.byte()
                self.ins[b >> 6] = b & 63
            elif b == 0xFD:
                self.where, self.ptr = self.ret
            elif b == 0xFE:
                n = self.byte()
                self.ret = (self.where, self.ptr)
                self.where, self.ptr = ("pat", n), 0
            else:
                nxt = self.d["pieces"][self.piece]["next"]
                if nxt == 0xFF:
                    self.piece = 0xFF
                    return
                self.begin(nxt)
                self.tick = self.speed
                self.ends += 1

    def frame(self):
        self.out = []
        if self.req != 0xFF:
            self.begin(self.req)
            self.req = 0xFF
            self.tick = self.rows = 1
            for x in range(4):
                self.silence_voice(x)
            self.dirty = 15
        if self.piece != 0xFF and self.d["pieces"][self.piece]["flags"] & MUP_PHASED \
                and self.newphase != self.phase:
            self.phase = self.newphase
            self.variant()
            self.dirty |= 7
        for x in (3, 2, 1, 0):
            if self.cnt[x]:
                self.cnt[x] -= 1
                if not self.cnt[x]:
                    self.env[x] += 1
                    self.load_step(x)
                    self.volume(x)
        for x in (3, 2, 1, 0):
            if self.dirty & self.free & (1 << x):
                self.dirty &= ~(1 << x)
                self.write_note(x)
                self.write_vol(x)
        if self.piece != 0xFF:
            self.tick -= 1
            if not self.tick:
                self.tick = self.speed
                self.rows -= 1
                if not self.rows:
                    self.events()
        return self.out


def play_through(d, piece, phase=0, max_secs=240, tail=2.0):
    """The model's writes, a list per frame: once through the piece (to its
    end, or until it comes round again), then `tail` seconds more."""
    m = Model(d)
    m.req, m.newphase = piece, phase
    frames, done_at = [], None
    while len(frames) < max_secs * FPS:
        frames.append(m.frame())
        if done_at is None and (m.piece == 0xFF or m.ends):
            done_at = len(frames)
        if done_at is not None and len(frames) >= done_at + tail * FPS:
            break
    return frames, (done_at or len(frames)) / FPS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("scores", nargs="+")
    ap.add_argument("--preview", help="a WAV of each piece here, from the model")
    ap.add_argument("--writes", help="the model's chip writes for each piece here")
    args = ap.parse_args()
    try:
        d = build(*parse(args.scores))
    except ScoreError as e:
        sys.exit(f"mkmusic: {e}")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(emit(d, args.scores))
    size = (len(d["envs"]) + 2 * len(d["ins_env"]) + 2 * len(d["drum_ctl"]) + 2 * len(d["per"])
            + 10 * len(d["var"]) + 6 * len(d["pieces"]) + 2 * len(d["pats"])
            + sum(len(p["order"]) for p in d["pieces"] if p["label"] == f"mus_{p['name']}")
            + sum(len(e) for e in d["pats"]))
    summary = []
    for i, p in enumerate(d["pieces"]):
        phases = [0, 1] if p["flags"] & MUP_PHASED else [0]
        for ph in phases:
            frames, secs = play_through(d, i, ph, tail=0 if p["next"] == i else 2.5)
            label = p["name"] + ("-blue" if ph else "")
            summary.append(f"{label} {secs:.1f}s")
            if args.preview:
                from snwav import render
                Path(args.preview).mkdir(parents=True, exist_ok=True)
                writes = [(f / FPS, v) for f, ws in enumerate(frames) for v in ws]
                render(writes, Path(args.preview) / f"{label}.wav", len(frames) / FPS)
            if args.writes:
                Path(args.writes).mkdir(parents=True, exist_ok=True)
                with open(Path(args.writes) / f"{label}.txt", "w") as f:
                    for ws in frames:
                        f.write(" ".join(f"{v:02X}" for v in ws) + "\n")
    print(f"{args.out}: {size} bytes; " + ", ".join(summary))


if __name__ == "__main__":
    main()
