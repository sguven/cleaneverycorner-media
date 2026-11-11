"""Original upbeat background track for @cleaneverycorner Reels (generated in code, no samples).

NOTE (2026-11-11): the house-pop sound below is LEGACY (sounded metallic). New Reels use the clean styles of
lib/music_clean.py via music_styles.pick_style(slug) -> make_track(..., style=style, seed=seed).

124 BPM by default, four-on-the-floor kick, claps on 2 and 4, offbeat open hats, 16th shaker,
bouncy offbeat octave bass, bright pluck hook + chord stabs, energy from beat 1.
Whoosh/riser into every cut, impact on before/after reveals, 1.5 s fade-out.
Loudness is normalised later by lib.engine.mux (loudnorm -15 LUFS, TP -1.5).

    from lib.music_upbeat import make_track
    make_track(duration, cut_times, impact_times, "music.wav", seed=day_number)
CLI: python -m lib.music_upbeat DUR out.wav [cut,cut,...] [impact,...]
"""
import numpy as np, wave, sys

SR = 44100

# a few original 4-chord loops (root midi, chord tones); picked by seed so days differ a bit
PROGS = [
    [(45, [57, 60, 64, 67]), (41, [57, 60, 65, 69]), (48, [55, 60, 64, 67]), (43, [55, 59, 62, 67])],   # Am F C G
    [(48, [60, 64, 67, 71]), (45, [57, 60, 64, 69]), (41, [57, 60, 65, 69]), (43, [55, 59, 62, 67])],   # C Am F G
    [(50, [57, 62, 65, 69]), (46, [58, 62, 65, 70]), (41, [57, 60, 65, 69]), (48, [55, 60, 64, 67])],   # Dm Bb F C
]
HOOKS = [[0, 2, 3, 2, 1, 3, 2, 3], [3, 2, 0, 2, 3, 1, 2, 0], [0, 3, 2, 3, 1, 2, 3, 2]]

def note(m): return 440.0 * 2 ** ((m - 69) / 12)

def make_track(dur, cuts=(), impacts=(), path="music.wav", bpm=124, seed=0, style=None):
    """style=None/"housepop" -> this original sound; funk/disco/futurebounce/dembow/trap/synthwave -> lib.music_styles
    (use lib.music_styles.pick_style(slug) to rotate styles per video)."""
    if style not in (None, "housepop"):
        try: from . import music_styles
        except ImportError: import music_styles
        music_styles.make_styled(dur, cuts, impacts, path, style=style, seed=seed)
        return path
    rng = np.random.default_rng(seed + 1)
    N = int(SR * dur); out = np.zeros((N, 2), np.float32)
    drums = np.zeros((N, 2), np.float32)
    beat = 60 / bpm; bar = 4 * beat

    def add(buf, sig, t0, pan=0.0, gain=1.0):
        i = int(t0 * SR)
        if i >= N or i + len(sig) <= 0: return
        if i < 0: sig = sig[-i:]; i = 0
        sig = sig[: N - i] * gain
        l = np.cos((pan + 1) * np.pi / 4); r = np.sin((pan + 1) * np.pi / 4)
        buf[i:i + len(sig), 0] += sig * l; buf[i:i + len(sig), 1] += sig * r

    def env(n, a=0.003, d=0.2, s=0.0, length=None, rel=0.04):
        t = np.arange(n) / SR
        e = np.minimum(1, t / a) * (s + (1 - s) * np.exp(-t / d))
        if length is not None: e *= np.clip((length + rel - t) / rel, 0, 1)
        return e

    def lp(x, k): return np.convolve(x, np.ones(k) / k, mode="same") if k > 1 else x

    def kick():
        n = int(0.32 * SR); t = np.arange(n) / SR
        f = 48 + 140 * np.exp(-t / 0.025)
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.16)
        s[:200] += rng.normal(0, 0.3, 200) * np.exp(-np.arange(200) / 40)    # click
        return np.tanh(s * 1.6) * 0.9

    def clap():
        n = int(0.25 * SR); t = np.arange(n) / SR
        s = rng.normal(0, 1, n); s = s - lp(s, 8)
        e = np.zeros(n)
        for o in (0, 0.011, 0.022): e += (t >= o) * np.exp(-np.clip(t - o, 0, None) / 0.008) * 0.6
        e += (t >= 0.03) * np.exp(-np.clip(t - 0.03, 0, None) / 0.07)
        return s * e * 0.38

    def hat(open_=False):
        n = int((0.16 if open_ else 0.05) * SR); s = rng.normal(0, 1, n); s = s - lp(s, 3)
        return s * np.exp(-np.arange(n) / SR / (0.05 if open_ else 0.012)) * (0.16 if open_ else 0.10)

    def shaker():
        n = int(0.06 * SR); t = np.arange(n) / SR; s = rng.normal(0, 1, n); s = s - lp(s, 2)
        return s * np.minimum(1, t / 0.01) * np.exp(-t / 0.02) * 0.05

    def bass(m, length):
        n = int((length + 0.05) * SR); t = np.arange(n) / SR; f = note(m)
        saw = 2 * ((f * t) % 1) - 1
        s = lp(saw, 10) * 0.6 + np.sin(2 * np.pi * f * t)
        return np.tanh(s * 1.4) * env(n, 0.004, 0.18, 0.35, length) * 0.42

    def pluck(m, length=0.22, g=0.2):
        n = int((length + 0.25) * SR); t = np.arange(n) / SR; f = note(m)
        s = (2 * ((f * t) % 1) - 1) + (2 * ((f * 1.006 * t) % 1) - 1)
        s = lp(s, 4)
        return s * env(n, 0.002, 0.12, 0, length, 0.08) * g

    def stab(ch, length):
        n = int((length + 0.2) * SR); t = np.arange(n) / SR; s = np.zeros(n)
        for m in ch:
            f = note(m + 12)
            s += (2 * ((f * t) % 1) - 1) + 0.6 * (2 * ((f * 1.01 * t) % 1) - 1)
        return lp(s, 6) * env(n, 0.003, 0.09, 0.0, length, 0.05) * 0.06

    def pad(ch, length):
        n = int(length * SR); t = np.arange(n) / SR; s = np.zeros(n)
        for m in ch: s += np.sin(2 * np.pi * note(m) * t) + 0.3 * np.sin(2 * np.pi * note(m) * 2.003 * t)
        return s * np.minimum(1, t / 0.08) * np.clip((length - t) / 0.1, 0, 1) * 0.025

    prog = PROGS[seed % len(PROGS)]; hook = HOOKS[seed % len(HOOKS)]
    nbars = int(np.ceil(dur / bar)) + 1
    for b in range(nbars):
        t0 = b * bar; root, ch = prog[b % 4]
        add(out, pad(ch, bar), t0, 0.0)
        for q in range(4):
            tb = t0 + q * beat
            add(drums, kick(), tb, 0.0, 1.0)
            if q in (1, 3): add(drums, clap(), tb, 0.05)
            add(drums, hat(True), tb + beat / 2, 0.25)
            for s16 in (1, 3): add(drums, shaker(), tb + s16 * beat / 4, -0.3, 0.9)
            # bouncy bass: root on the offbeat 8th, octave pickup on last 16th
            add(out, bass(root, beat * 0.42), tb + beat / 2)
            add(out, bass(root + 12, beat * 0.2), tb + beat * 0.75, 0, 0.7)
            # chord stabs on the "and" of 2 and 4
            if q in (1, 3): add(out, stab(ch, beat * 0.3), tb + beat / 2, 0.1)
        # pluck hook in 8ths (rests every 4th bar's 2nd half for phrasing)
        for i, k in enumerate(hook):
            if b % 4 == 3 and i >= 5: continue
            add(out, pluck(ch[k] + 12), t0 + i * beat / 2, 0.35 if i % 2 else -0.35)
        if b % 4 == 3:   # snare-ish clap fill
            for j in range(4): add(drums, clap(), t0 + 3 * beat + j * beat / 4, 0.0, 0.5 + j * 0.12)

    # sidechain pump on the music bus
    t = np.arange(N) / SR
    out *= (1 - 0.45 * np.exp(-((t % beat) / 0.07)))[:, None]

    fx = np.zeros((N, 2), np.float32)
    for c in cuts:                      # whoosh/riser ending on the cut
        L = 0.45; n = int(L * SR); tt = np.arange(n) / SR
        s = rng.normal(0, 1, n)
        k = np.linspace(14, 2, n).astype(int)          # opening filter
        y = np.empty(n)
        cs = np.cumsum(np.concatenate([[0], s]))
        for i in range(n):
            a = max(0, i - k[i]); y[i] = (cs[i + 1] - cs[a]) / (i + 1 - a)
        e = (tt / L) ** 2 * np.clip((L + 0.03 - tt) / 0.06, 0, 1)
        sw = y * e * 0.55
        add(fx, sw, c - L + 0.02, -0.4, 1.0); add(fx, sw * 0.8, c - L + 0.03, 0.4, 1.0)
    for c in impacts:                   # boom + noise burst
        n = int(1.2 * SR); tt = np.arange(n) / SR
        f = 40 + 80 * np.exp(-tt / 0.06)
        boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.45)
        nz = rng.normal(0, 1, n); nz = lp(nz, 3) * np.exp(-tt / 0.12) * 0.35
        add(fx, np.tanh((boom + nz) * 1.5) * 0.9, c, 0.0)

    mix = out * 1.0 + drums * 0.85 + fx * 0.9
    # short stereo slap for width
    k = int(0.018 * SR); mix[k:, 0] += mix[:-k, 1] * 0.12; mix[k:, 1] += mix[:-k, 0] * 0.12
    fi = np.clip(t / 0.01, 0, 1); fo = np.clip((dur - t) / 1.5, 0, 1)
    mix *= (fi * fo)[:, None]
    mix = np.tanh(mix / (np.max(np.abs(mix)) + 1e-9) * 1.3) * 0.89
    pcm = (mix * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    return path

if __name__ == "__main__":
    d = float(sys.argv[1]); p = sys.argv[2]
    cuts = [float(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 and sys.argv[3] else []
    imps = [float(x) for x in sys.argv[4].split(",")] if len(sys.argv) > 4 and sys.argv[4] else []
    make_track(d, cuts, imps, p); print("ok", p)
