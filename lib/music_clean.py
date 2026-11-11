"""Clean, clear-sounding background music for Reels (numpy/scipy only, no samples, no licensed audio).

Why this exists: the older generators (music_upbeat "housepop" and the music_styles presets) build their
sounds from naive sawtooth/square waves, white-noise hi-hats and heavy tanh saturation. That aliases and
sounds harsh / metallic on phone speakers. Every instrument here is band-limited:
  * tones are additive sine partials (only harmonic ratios, nothing above ~12 kHz),
  * strings are Karplus-Strong with a soft, low-passed excitation,
  * percussion is pitched sine bodies plus gently band-passed noise (no bright white-noise hats),
  * a short smooth reverb, and a transparent look-ahead limiter instead of tanh clipping.

Styles (all upbeat, all clean):
  brightpop   118 BPM  piano offbeat stabs + marimba hook, round sine bass, soft clap, shaker
  pianohouse  122 BPM  four-on-the-floor, piano chords, glockenspiel melody, sub bass
  tropical    104 BPM  marimba + kalimba, syncopated bass, finger snaps
  acoustic    112 BPM  strummed nylon guitar (Karplus-Strong), claps, shaker, warm bass
  keysfunk    108 BPM  swung clean e-piano chords, glockenspiel licks, picked bass, rim clicks
  kalimbapop   96 BPM  kalimba hook, soft piano pad, bouncy bass, snaps

    import music_clean
    music_clean.make_clean(duration, cuts, impacts, "music.wav", style="brightpop", seed=3)

CLI preview: python3 lib/music_clean.py STYLE DUR out.wav
"""
import numpy as np, wave, sys
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.ndimage import maximum_filter1d

SR = 44100
NYQ_SAFE = 12000.0
CLEAN_STYLES = ["brightpop", "pianohouse", "tropical", "acoustic", "keysfunk", "kalimbapop"]
QUAL = {"m7": [0, 3, 7, 10], "7": [0, 4, 7, 10], "maj7": [0, 4, 7, 11], "m": [0, 3, 7], "maj": [0, 4, 7],
        "add9": [0, 4, 7, 14], "sus2": [0, 2, 7]}

# 16-step patterns (one bar of 16ths): x = hit, g = ghost (soft), . = rest
STYLES = {
    "brightpop": dict(bpm=118, swing=0.0,
        kick="x...x...x...x...", clap="....x.......x...", snap="................", shaker="x.x.x.x.x.x.x.x.",
        bass={0: 0, 3: 0, 6: 12, 8: 0, 11: 0, 14: 7}, bass_len=1.6,
        chord="piano", chord_steps=[2, 6, 10, 14], chord_len=1.2, chord_gain=0.85,
        lead="marimba", lead_a={0: 2, 3: 1, 6: 2, 8: 3, 11: 2, 14: 1}, lead_b={0: 3, 2: 2, 4: 1, 7: 2, 10: 0, 12: 1}, lead_gain=1.0,
        pad=False, prog=[(0, "add9"), (7, "maj"), (9, "m7"), (5, "maj7")]),
    "pianohouse": dict(bpm=122, swing=0.0,
        kick="x...x...x...x...", clap="....x.......x...", snap="................", shaker="..x...x...x...x.",
        bass={2: 0, 6: 0, 10: 0, 14: 0, 15: 12}, bass_len=1.7,
        chord="piano", chord_steps=[0, 3, 6, 10, 12], chord_len=1.4, chord_gain=0.9,
        lead="glock", lead_a={0: 2, 4: 3, 8: 2, 12: 1}, lead_b={0: 3, 2: 2, 6: 1, 8: 2, 12: 3, 14: 4}, lead_gain=0.8,
        pad=True, prog=[(9, "m7"), (5, "maj7"), (0, "maj"), (7, "maj")]),
    "tropical": dict(bpm=104, swing=0.0,
        kick="x...x...x...x...", clap="................", snap="....x.......x...", shaker="x.xxx.xxx.xxx.xx",
        bass={0: 0, 3: 0, 6: 7, 8: 0, 10: 12, 13: 7}, bass_len=1.4,
        chord="kalimba", chord_steps=[2, 5, 10, 13], chord_len=1.5, chord_gain=0.8,
        lead="marimba", lead_a={0: 2, 3: 3, 6: 2, 10: 1, 12: 2}, lead_b={0: 4, 3: 3, 6: 2, 8: 1, 10: 2, 14: 3}, lead_gain=1.0,
        pad=False, prog=[(2, "m7"), (7, "maj"), (0, "maj7"), (9, "m")]),
    "acoustic": dict(bpm=112, swing=0.0,
        kick="x.....x.x.......", clap="....x.......x...", snap="................", shaker="xgxgxgxgxgxgxgxg",
        bass={0: 0, 6: 0, 8: 7, 11: 0, 14: 5}, bass_len=1.8,
        chord="guitar", chord_steps=[0, 3, 6, 8, 10, 12, 14], chord_len=1.6, chord_gain=0.9,
        lead="glock", lead_a={0: 2, 6: 3, 8: 2, 12: 1}, lead_b={2: 1, 4: 2, 8: 3, 10: 2, 14: 1}, lead_gain=0.6,
        pad=False, prog=[(0, "maj"), (7, "maj"), (9, "m"), (5, "maj")]),
    "keysfunk": dict(bpm=108, swing=0.12,
        kick="x..x..x...x.....", clap="....x.......x...", snap="..g.....g.g...g.", shaker="x.x.x.x.x.x.x.x.",
        bass={0: 0, 3: 0, 6: 12, 7: 10, 10: 0, 12: 7, 14: 5}, bass_len=1.3,
        chord="epiano", chord_steps=[2, 7, 10, 15], chord_len=1.6, chord_gain=0.9,
        lead="glock", lead_a={0: 2, 3: 1, 6: 3, 10: 2, 12: 1}, lead_b={0: 3, 4: 2, 7: 1, 10: 0, 12: 2}, lead_gain=0.7,
        pad=False, prog=[(9, "m7"), (2, "7"), (7, "maj7"), (4, "m7")]),
    "kalimbapop": dict(bpm=96, swing=0.0,
        kick="x.....x...x.....", clap="....x.......x...", snap="......g.......g.", shaker="..x...x...x...x.",
        bass={0: 0, 6: 0, 10: 7, 14: 5}, bass_len=2.0,
        chord="piano", chord_steps=[0, 8], chord_len=3.5, chord_gain=0.55,
        lead="kalimba", lead_a={0: 2, 2: 1, 3: 2, 6: 3, 8: 2, 10: 1, 11: 2, 14: 0},
        lead_b={0: 3, 2: 2, 4: 1, 6: 2, 8: 4, 11: 3, 14: 2}, lead_gain=1.0,
        pad=True, prog=[(5, "maj7"), (0, "add9"), (9, "m7"), (7, "sus2")]),
}


def note(m): return 440.0 * 2 ** ((m - 69) / 12)


def _sos(kind, f, order=2):
    return butter(order, f, btype=kind, fs=SR, output="sos")


def _filt(x, kind, f, order=2): return sosfilt(_sos(kind, f, order), x)


def additive(f, n, partials, attack=0.003, rel_at=None, rel=0.05):
    """partials: list of (ratio, amp, decay_s). Partials above NYQ_SAFE are dropped (no aliasing)."""
    t = np.arange(n) / SR
    out = np.zeros(n)
    for ratio, amp, dec in partials:
        fr = f * ratio
        if fr >= NYQ_SAFE: continue
        out += amp * np.sin(2 * np.pi * fr * t) * np.exp(-t / dec)
    out *= np.minimum(1.0, t / attack)
    if rel_at is not None: out *= np.clip((rel_at + rel - t) / rel, 0, 1)
    return out


# ---------------- instruments ----------------
def piano(m, L):
    f = note(m); n = int((L + 0.6) * SR); B = 0.00035
    parts = [(k * np.sqrt(1 + B * k * k), 0.9 / k ** 1.4, 0.9 / (1 + 0.45 * k)) for k in range(1, 11)]
    x = additive(f, n, parts, 0.002, L, 0.25)
    # soft hammer: tiny low-passed thump, no bright noise
    th = int(0.012 * SR)
    x[:th] += _filt(np.random.default_rng(m).normal(0, 1, th), "low", 1800) * np.linspace(1, 0, th) * 0.04
    return x * 0.16


def epiano(m, L):
    f = note(m); n = int((L + 0.5) * SR); t = np.arange(n) / SR
    idx = 0.9 * np.exp(-t / 0.35)                      # gentle FM, ratio 1:1 -> warm, not bell-like
    x = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * t))
    x += 0.15 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.15)
    env = np.minimum(1, t / 0.004) * (0.25 + 0.75 * np.exp(-t / 0.5)) * np.clip((L + 0.2 - t) / 0.2, 0, 1)
    return x * env * 0.11


def marimba(m, L):
    f = note(m); n = int(min(L + 0.4, 0.9) * SR)
    return additive(f, n, [(1, 1.0, 0.38), (4, 0.22, 0.05), (10, 0.05, 0.015)], 0.001) * 0.22


def kalimba(m, L):
    f = note(m); n = int(min(L + 0.6, 1.2) * SR)
    return additive(f, n, [(1, 1.0, 0.55), (2, 0.12, 0.12), (3, 0.06, 0.05)], 0.001) * 0.2


def glock(m, L):
    f = note(m); n = int(min(L + 0.8, 1.5) * SR)
    return additive(f, n, [(1, 1.0, 0.7), (3, 0.10, 0.12)], 0.001) * 0.11


def guitar(m, L, rng=None):
    """Karplus-Strong nylon string with a soft, low-passed pluck."""
    f = note(m); n = int((L + 0.5) * SR); p = max(2, int(round(SR / f)))
    rng = rng or np.random.default_rng(m)
    buf = _filt(rng.uniform(-1, 1, p), "low", min(3500, f * 8))
    out = np.zeros(n); b = buf.copy(); i = 0; damp = 0.996
    # vectorised in blocks of one period
    while i < n:
        k = min(p, n - i)
        out[i:i + k] = b[:k]
        b = damp * 0.5 * (b + np.roll(b, -1))
        i += k
    t = np.arange(n) / SR
    out *= np.clip((L + 0.3 - t) / 0.3, 0, 1)
    return _filt(out, "low", 5000) * 0.28


def pad(m, L):
    f = note(m); n = int(L * SR); t = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * (1 + d) * t) for d in (-0.003, 0.0, 0.003)) / 3
    x += 0.25 * np.sin(2 * np.pi * 2 * f * t)
    return x * np.minimum(1, t / 0.25) * np.clip((L - t) / 0.3, 0, 1) * 0.035


def bass(m, L):
    f = note(m); n = int((L + 0.05) * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) + 0.22 * np.sin(2 * np.pi * 2 * f * t) + 0.06 * np.sin(2 * np.pi * 3 * f * t)
    env = np.minimum(1, t / 0.004) * (0.45 + 0.55 * np.exp(-t / 0.18)) * np.clip((L - t) / 0.04, 0, 1)
    return x * env * 0.34


INSTR = {"piano": piano, "epiano": epiano, "marimba": marimba, "kalimba": kalimba, "glock": glock,
         "guitar": guitar, "pad": pad}


# ---------------- drums (clean) ----------------
def d_kick():
    n = int(0.35 * SR); t = np.arange(n) / SR
    f = 50 + 90 * np.exp(-t / 0.03)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.17)
    click = np.sin(2 * np.pi * 1200 * t) * np.exp(-t / 0.003) * 0.12
    return (body + click) * 0.85


def d_clap(rng):
    n = int(0.22 * SR); t = np.arange(n) / SR
    x = _filt(_filt(rng.normal(0, 1, n), "high", 900), "low", 3200)
    env = np.zeros(n)
    for o in (0.0, 0.010, 0.020):
        env += (t >= o) * np.exp(-np.clip(t - o, 0, None) / 0.007) * 0.5
    env += (t >= 0.028) * np.exp(-np.clip(t - 0.028, 0, None) / 0.06)
    return x * env * 0.22


def d_snap():
    n = int(0.08 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 1700 * t) * 0.6 + np.sin(2 * np.pi * 420 * t)) * np.exp(-t / 0.012) * 0.16


def d_shaker(rng):
    n = int(0.07 * SR); t = np.arange(n) / SR
    x = _filt(_filt(rng.normal(0, 1, n), "high", 4500), "low", 8500)
    return x * np.minimum(1, t / 0.006) * np.exp(-t / 0.02) * 0.11


# ---------------- fx ----------------
def whoosh(rng, dur=0.45):
    n = int(dur * SR); t = np.arange(n) / SR
    x = rng.normal(0, 1, n); out = np.zeros(n); steps = 10
    for k in range(steps):
        a, b = int(k * n / steps), int((k + 1) * n / steps)
        lo = 300 + 3000 * (k / steps) ** 2
        out[a:b] = _filt(x, "band", [lo, min(lo * 2.0, 7000)])[a:b]
    return out * (t / dur) ** 2 * np.clip((dur + 0.02 - t) / 0.05, 0, 1) * 0.35


def impact(rng):
    n = int(1.1 * SR); t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(42 + 70 * np.exp(-t / 0.05)) / SR) * np.exp(-t / 0.4)
    air = _filt(rng.normal(0, 1, n), "low", 2500) * np.exp(-t / 0.15) * 0.15
    return (boom + air) * 0.75


def _reverb_ir(rng, secs=0.9):
    n = int(secs * SR); t = np.arange(n) / SR
    ir = np.stack([_filt(rng.normal(0, 1, n), "low", 5000), _filt(rng.normal(0, 1, n), "low", 5000)], 1)
    ir *= np.exp(-t / (secs / 5))[:, None]
    ir[: int(0.012 * SR)] = 0                       # pre-delay
    return ir / np.sqrt((ir ** 2).sum(0, keepdims=True))


def _limit(x, ceil, look=0.003, release=0.08):
    """Transparent look-ahead peak limiter (no waveshaping)."""
    peak = np.max(np.abs(x), axis=1)
    w = max(1, int(look * SR))
    need = np.minimum(1.0, ceil / np.maximum(maximum_filter1d(peak, 2 * w + 1), 1e-9))
    # smooth: instant attack (already looked ahead), exponential release
    g = need.copy(); a = np.exp(-1 / (release * SR))
    # vectorised enough for 40 s; simple loop in blocks
    for i in range(1, len(g)):
        if g[i] > g[i - 1]: g[i] = a * g[i - 1] + (1 - a) * g[i]
    return x * g[:, None]


def render(dur, cuts, impacts, style, seed=0):
    S = STYLES[style]; rng = np.random.default_rng(seed + 7)
    N = int(SR * dur) + SR
    mel = np.zeros((N, 2)); drums = np.zeros((N, 2)); fx = np.zeros((N, 2))
    step = 60 / S["bpm"] / 4; bar = step * 16
    transpose = int(rng.integers(-2, 3))            # small key change per seed so repeats of a style still differ

    def add(buf, sig, t0, pan=0.0, gain=1.0):
        i = int(t0 * SR)
        if i >= N or i + len(sig) <= 0: return
        if i < 0: sig = sig[-i:]; i = 0
        sig = sig[: N - i] * gain
        l = np.cos((pan + 1) * np.pi / 4); r = np.sin((pan + 1) * np.pi / 4)
        buf[i:i + len(sig), 0] += sig * l; buf[i:i + len(sig), 1] += sig * r

    K, CL, SNP = d_kick(), d_clap(rng), d_snap()
    shakers = [d_shaker(rng) for _ in range(4)]
    cache = {}

    def inst(name, m, L):
        k = (name, m, round(L, 3))
        if k not in cache: cache[k] = INSTR[name](m, L)
        return cache[k]

    kick_times = []
    nbars = int(np.ceil(dur / bar)) + 1
    for b in range(nbars):
        pc, q = S["prog"][b % len(S["prog"])]
        pc += transpose
        root = 60 + pc - (12 if pc > 6 else 0)
        tones = [root + iv for iv in QUAL[q]]
        lead = S["lead_a"] if (b // 2) % 2 == 0 else S["lead_b"]
        if S["pad"]:
            for i, m in enumerate(tones[:3]): add(mel, inst("pad", m, bar), b * bar, (-0.4, 0, 0.4)[i])
        for s in range(16):
            t = b * bar + s * step + (S["swing"] * step if s % 2 == 1 else 0.0)
            if S["kick"][s] == "x": add(drums, K, t); kick_times.append(t)
            if S["clap"][s] == "x": add(drums, CL, t, 0.05)
            c = S["snap"][s]
            if c in "xg": add(drums, SNP, t, -0.2, 1.0 if c == "x" else 0.45)
            c = S["shaker"][s]
            if c in "xg": add(drums, shakers[s % 4], t, 0.3, 1.0 if c == "x" else 0.5)
            if s in S["bass"]:
                add(mel, bass(36 + pc + S["bass"][s], step * S["bass_len"]), t, 0.0, 1.0)
            if s in S["chord_steps"]:
                L = step * S["chord_len"]
                strum = 0.012 if S["chord"] == "guitar" else 0.0
                for i, m in enumerate(tones):
                    add(mel, inst(S["chord"], m + (0 if S["chord"] in ("kalimba",) else 0), L), t + i * strum,
                        (-0.3, -0.1, 0.1, 0.3)[i % 4], S["chord_gain"])
            if s in lead:
                idx = lead[s]; m = tones[idx % len(tones)] + 12 * (1 + idx // len(tones))
                add(mel, inst(S["lead"], m, step * 2), t, 0.3 if (s // 2) % 2 else -0.3, S["lead_gain"])

    # light sidechain on the melodic bus so the kick stays punchy without distortion
    gain = np.ones(N); Ld = int(0.3 * SR); dip = 1 - 0.22 * np.exp(-np.arange(Ld) / SR / 0.07)
    for t in kick_times:
        i = int(t * SR)
        if i < N: gain[i:i + Ld] *= dip[: N - i][:Ld]
    mel *= gain[:, None]

    for c in cuts:
        w = whoosh(rng); add(fx, w, c - len(w) / SR + 0.02, -0.3); add(fx, w * 0.8, c - len(w) / SR + 0.03, 0.3)
    for c in impacts:
        add(fx, impact(rng), c, 0.0)

    # smooth short reverb on melody (+ a little on claps) for a polished, clear sound
    ir = _reverb_ir(rng)
    send = mel * 0.20 + drums * 0.05
    wet = np.stack([fftconvolve(send[:, 0], ir[:, 0])[:N], fftconvolve(send[:, 1], ir[:, 1])[:N]], 1)
    mix = mel + drums * 0.9 + fx * 0.8 + wet * 0.5
    mix = _filt(mix.T, "high", 30).T                 # remove sub rumble
    mix = mix + 0.6 * _filt(mix.T, "band", [1800, 6500]).T   # presence lift: clear on phone speakers
    mix = mix[: int(SR * dur)]
    t = np.arange(len(mix)) / SR
    mix *= (np.clip(t / 0.01, 0, 1) * np.clip((dur - t) / 1.5, 0, 1) ** 1.3)[:, None]
    return mix


def make_clean(dur, cuts=(), impacts=(), path="music.wav", style="brightpop", seed=0, lufs=-15.0):
    """Render a clean track to 16-bit stereo WAV at ~lufs with peaks <= -2 dBFS. Returns measured LUFS (or None)."""
    mix = render(dur, list(cuts), list(impacts), style, seed)
    ceil = 10 ** (-2.0 / 20); measured = None
    try:
        import pyloudnorm as pyln
        meter = pyln.Meter(SR)
        for _ in range(3):
            mix = pyln.normalize.loudness(mix, meter.integrated_loudness(mix), lufs)
            mix = _limit(mix, ceil)
        measured = float(meter.integrated_loudness(mix))
    except ImportError:
        mix = _limit(mix / (np.max(np.abs(mix)) + 1e-9) * 1.6, ceil)
    mix = np.clip(mix, -ceil, ceil)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())
    return measured


if __name__ == "__main__":
    st, d, p = sys.argv[1], float(sys.argv[2]), sys.argv[3]
    print(st, "lufs", make_clean(d, [d / 3, 2 * d / 3], [1.0], p, st, seed=1))
