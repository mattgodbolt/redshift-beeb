#!/usr/bin/env python3
"""The BBC's SN76489, for turning writes to the chip into a WAV.

    snwav.py <log> <out.wav> [--secs N]

The log is what tools/musiccap.mjs saves: a line per write, the CPU
cycle (2MHz) it happened at and the byte, in hex. tools/mkmusic.py's
previews use render() directly, with times in seconds.

The model is jsbeeb's (src/soundchip.js), so a capture sounds as the
emulator played it:
- the counters run at 4MHz / 16, so a tone of period N toggles every N
  ticks: 125000 / N Hz (a period of 0 counts 1024);
- the noise shifts a 15-bit register (white: bits 0 and 1 fed back;
  periodic: bit 0 alone) on every second toggle of its own counter, which
  counts 16, 32 or 64 ticks, or tone 2's period; writing the noise
  register restarts it;
- each attenuation step is 2dB, 15 is silent; each channel's output is
  unipolar (0 or its level), then the BBC's DC restoration (a first-order
  high-pass at 1 / (2 pi 10K 4u7)).
"""
import argparse
import math
import wave

import numpy as np

TICKS = 4_000_000 / 16          # the counters' clock
CPU = 2_000_000                 # the log's cycles
RATE = 44100
LEVEL = [0.25 * 10 ** (-0.1 * a) for a in range(15)] + [0.0]


class Chip:
    def __init__(self):
        self.reg = [0, 0, 0, 0]     # tone periods, then the noise control
        self.att = [15, 15, 15, 15]
        self.latched = 0
        self.count = [0.0] * 4      # ticks to each counter's next toggle
        self.bit = [0, 0, 0, 0]
        self.lfsr = 1 << 14

    def write(self, v):
        if v & 0x80:
            self.latched = (v >> 4) & 7
            data, low = v & 15, True
        else:
            data, low = v & 0x3F, False
        ch, vol = self.latched >> 1, self.latched & 1
        if vol:
            self.att[ch] = data & 15
        elif ch == 3:
            self.reg[3] = data & 7
            self.lfsr = 1 << 14
        elif low:
            self.reg[ch] = (self.reg[ch] & 0x3F0) | data
        else:
            self.reg[ch] = (self.reg[ch] & 15) | (data << 4)

    def period(self, ch):
        if ch == 3:
            r = self.reg[3] & 3
            return self.period(2) if r == 3 else (16, 32, 64)[r]
        return self.reg[ch] or 1024

    def run(self, n):
        """n ticks of output (each channel's level or 0, summed)."""
        out = np.zeros(n)
        k = np.arange(n)
        for ch in range(3):
            p = self.period(ch)
            c = self.count[ch]
            flips = np.where(k < c, 0, 1 + np.floor((k - c) / p).astype(np.int64))
            if LEVEL[self.att[ch]]:
                out += ((self.bit[ch] ^ (flips & 1)) * LEVEL[self.att[ch]])
            total = 0 if n <= c else 1 + int((n - 1 - c) // p)
            self.bit[ch] ^= total & 1
            self.count[ch] = c + total * p - n
        # The noise: shifts on the toggles that set its bit.
        p, c = self.period(3), self.count[3]
        white = self.reg[3] & 4
        noise = np.empty(n)
        at = 0
        t = c
        while t < n:
            ti = max(int(math.ceil(t)), 0)
            noise[at:ti] = self.lfsr & 1
            at = ti
            self.bit[3] ^= 1
            if self.bit[3]:
                if white:
                    fb = (self.lfsr ^ (self.lfsr >> 1)) & 1
                    self.lfsr = (self.lfsr >> 1) | (fb << 14)
                else:
                    self.lfsr >>= 1
                    if not self.lfsr:
                        self.lfsr = 1 << 14
            t += p
        noise[at:] = self.lfsr & 1
        self.count[3] = t - n
        out += noise * LEVEL[self.att[3]]
        return out


def render(writes, path, secs=None, rate=RATE):
    """writes: (seconds, byte), in order. The WAV runs to secs, or a
    second past the last write."""
    chip = Chip()
    end = secs if secs is not None else (writes[-1][0] + 1 if writes else 1)
    total = int(end * TICKS)
    pieces, now = [], 0
    for t, v in writes:
        at = min(int(t * TICKS), total)
        if at > now:
            pieces.append(chip.run(at - now))
            now = at
        chip.write(v)
    if total > now:
        pieces.append(chip.run(total - now))
    sig = np.concatenate(pieces) if pieces else np.zeros(total)
    # Down to the output rate: each sample the mean over its span.
    csum = np.concatenate([[0.0], np.cumsum(sig)])
    n = int(len(sig) * rate / TICKS)
    edges = np.arange(n + 1) * (TICKS / rate)
    c = np.interp(edges, np.arange(len(csum)), csum)
    out = np.diff(c) / (TICKS / rate)
    # DC restoration.
    alpha = 1 - 2 * math.pi * (1 / (2 * math.pi * 10e3 * 4.7e-6)) / rate
    y = np.empty_like(out)
    prev_in = prev_out = 0.0
    for i, x in enumerate(out):
        prev_out = x - prev_in + alpha * prev_out
        prev_in = x
        y[i] = prev_out
    pcm = np.clip(y * 1.4, -1, 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes((pcm * 32000).astype("<i2").tobytes())
    return end


def read_log(path):
    writes = []
    for line in open(path):
        line = line.split("#")[0].split()
        if len(line) >= 2:
            writes.append((int(line[0]) / CPU, int(line[1], 16)))
    if writes:
        t0 = writes[0][0]
        writes = [(t - t0, v) for t, v in writes]
    return writes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log")
    ap.add_argument("wav")
    ap.add_argument("--secs", type=float)
    args = ap.parse_args()
    end = render(read_log(args.log), args.wav, args.secs)
    print(f"{args.wav}: {end:.1f}s")


if __name__ == "__main__":
    main()
