"""Original upbeat lo-fi loop, synthesized from scratch (no samples): pad, pluck arpeggio, bass, drums.

usage: python music.py <seconds> <out.wav>
"""
import sys
import wave

import numpy as np

SR = 44100
BPM = 104
BEAT = 60 / BPM
BAR = 4 * BEAT
rng = np.random.default_rng(7)


def note(n):  # MIDI -> Hz
    return 440.0 * 2 ** ((n - 69) / 12)


# Am - F - C - G, one bar each (MIDI notes)
CHORDS = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
BASS = [45, 41, 48, 43]


def env(n, a, d, s, r_len):
    """ADSR envelope of n samples (a, d, r in seconds, s level)."""
    a, d, r = int(a * SR), int(d * SR), int(r_len * SR)
    e = np.full(n, s, dtype=np.float64)
    e[:min(a, n)] = np.linspace(0, 1, a)[:n]
    if a < n:
        k = min(d, n - a)
        e[a:a + k] = np.linspace(1, s, d)[:k]
    if r and n > r:
        e[-r:] *= np.linspace(1, 0, r)
    return e


def tone(freq, dur, harmonics=((1, 1.0), (2, 0.3), (3, 0.12)), detune=0.0):
    t = np.arange(int(dur * SR)) / SR
    out = np.zeros_like(t)
    for h, amp in harmonics:
        out += amp * np.sin(2 * np.pi * freq * h * t)
        if detune:
            out += amp * 0.5 * np.sin(2 * np.pi * freq * h * (1 + detune) * t)
    return out


def add(buf, sig, start):
    i = int(start * SR)
    j = min(len(buf), i + len(sig))
    if i < len(buf):
        buf[i:j] += sig[:j - i]


def kick():
    t = np.arange(int(0.35 * SR)) / SR
    f = 110 * np.exp(-t * 18) + 42
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def snare():
    n = int(0.22 * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    noise = np.convolve(noise, np.ones(3) / 3, mode="same")
    return (0.55 * noise + 0.4 * np.sin(2 * np.pi * 190 * t)) * np.exp(-t * 22)


def hat():
    n = int(0.06 * SR)
    noise = rng.standard_normal(n)
    noise = noise - np.convolve(noise, np.ones(8) / 8, mode="same")  # high-pass-ish
    return noise * np.exp(-np.arange(n) / SR * 70)


def main(seconds, out):
    n = int(seconds * SR)
    left, right = np.zeros(n), np.zeros(n)
    bars = int(np.ceil(seconds / BAR))
    k, s, h = kick(), snare(), hat()
    for b in range(bars):
        t0 = b * BAR
        chord, bass = CHORDS[b % 4], BASS[b % 4]
        intro = b < 2  # first 2 bars: pad + arpeggio only
        # warm pad (slightly detuned, slow attack)
        for m in chord:
            p = tone(note(m), BAR, ((1, 1.0), (2, 0.18)), detune=0.003) * env(int(BAR * SR), 0.25, 0.4, 0.7, 0.3) * 0.05
            add(left, p, t0)
            add(right, p, t0)
        # pluck arpeggio in 8ths, ping-pong
        pattern = [0, 1, 2, 1, 2, 0, 1, 2]
        for i, idx in enumerate(pattern):
            m = chord[idx] + 12
            pl = tone(note(m), BEAT / 2 + 0.25, ((1, 1.0), (2, 0.4), (4, 0.1))) * env(int((BEAT / 2 + 0.25) * SR), 0.004, 0.18, 0.15, 0.2) * 0.06
            add(left if i % 2 == 0 else right, pl, t0 + i * BEAT / 2)
            add(right if i % 2 == 0 else left, pl * 0.45, t0 + i * BEAT / 2)
        if intro:
            continue
        # bass: root on 1 and the "and" of 2 and 3
        for pos, dur in ((0, 1.2), (1.5, 0.4), (2.5, 1.2)):
            bs = tone(note(bass), dur * BEAT, ((1, 1.0), (2, 0.25))) * env(int(dur * BEAT * SR), 0.01, 0.2, 0.6, 0.08) * 0.16
            add(left, bs, t0 + pos * BEAT)
            add(right, bs, t0 + pos * BEAT)
        # drums
        for beat in (0, 2.5):
            add(left, k * 0.42, t0 + beat * BEAT)
            add(right, k * 0.42, t0 + beat * BEAT)
        for beat in (1, 3):
            add(left, s * 0.13, t0 + beat * BEAT)
            add(right, s * 0.13, t0 + beat * BEAT)
        for i in range(8):
            swing = 0.03 if i % 2 else 0.0
            add(right if i % 2 else left, h * (0.05 if i % 2 else 0.07), t0 + i * BEAT / 2 + swing)

    stereo = np.stack([left, right], axis=1)
    # fade in 1.5 s, fade out 3 s, soft clip, normalize to -3 dBFS
    fi, fo = int(1.5 * SR), int(3 * SR)
    stereo[:fi] *= np.linspace(0, 1, fi)[:, None]
    stereo[-fo:] *= np.linspace(1, 0, fo)[:, None]
    stereo = np.tanh(stereo * 1.4)
    stereo *= 0.707 / np.max(np.abs(stereo))
    pcm = (stereo * 32767).astype(np.int16)
    with wave.open(out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f"{out}: {seconds}s, {BPM} BPM")


if __name__ == "__main__":
    main(float(sys.argv[1]), sys.argv[2])
