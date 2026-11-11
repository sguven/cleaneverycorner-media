"""Style presets for the generated Reel background music (numpy only, no samples, no licensed audio).

Six upbeat styles; "housepop" is the original sound (lib/music_upbeat.py), the other five live here:
funk, disco, futurebounce, dembow, trap, synthwave.  Each style differs in tempo, swing, drum kit and pattern,
bass sound, chord/lead instrument and chord progression, so videos do not sound alike.

    from lib.music_styles import pick_style
    style, seed = pick_style("2026-11-09-some-slug")        # rotates, never repeats the last 2 styles, idempotent per slug
    make_track(dur, cuts, impacts, "music.wav", style=style, seed=seed)

CLI preview: python -m lib.music_styles STYLE DUR out.wav
"""
import numpy as np, wave, json, os, sys, hashlib

SR = 44100
ALL_STYLES = ["housepop", "funk", "disco", "futurebounce", "dembow", "trap", "synthwave"]   # legacy (saw/noise based)
# Since 2026-11-11 only the clean, band-limited styles of lib/music_clean.py are rotated (the legacy ones sounded metallic).
ROTATION = ["brightpop", "pianohouse", "tropical", "acoustic", "keysfunk", "kalimbapop"]

QUAL = {"m7": [0, 3, 7, 10], "7": [0, 4, 7, 10], "maj7": [0, 4, 7, 11], "m": [0, 3, 7], "maj": [0, 4, 7]}

# patterns are 16 steps (one bar of 16ths): x = full hit, g = ghost, o = open hat, . = rest
STYLES = {
    "funk": dict(
        bpm=106, swing=0.14,
        kick="x..x..x...x.....", snare="..g.x..g..g.x.g.", snare_kind="snare", hat="x.x.x.x.x.x.x.o.",
        bass={0: 0, 3: 0, 6: 12, 7: 10, 10: 0, 12: 7, 14: 5}, bass_kind="pluck", bass_len=1.5,
        chord_kind="epiano", chord_steps=[2, 7, 10, 15], chord_len=1.6, chord_gain=0.9,
        lead_kind="square", lead={0: 2, 3: 1, 6: 3, 10: 2, 12: 1}, lead_len=1.4, lead_gain=0.7,
        prog=[(9, "m7"), (2, "7"), (7, "maj7"), (4, "7")], sidechain=0.2),
    "disco": dict(
        bpm=118, swing=0.0,
        kick="x...x...x...x...", snare="....x.......x...", snare_kind="clap", hat="x.o.x.o.x.o.x.o.",
        bass={i: (12 if (i // 2) % 2 else 0) for i in range(0, 16, 2)}, bass_kind="sine_saw", bass_len=1.6,
        chord_kind="supersaw", chord_steps=[2, 6, 10, 14], chord_len=1.3, chord_gain=0.8,
        lead_kind="pluck", lead={0: 0, 2: 1, 4: 2, 6: 3, 8: 2, 10: 1, 12: 2, 14: 3}, lead_len=1.5, lead_gain=1.0,
        prog=[(9, "m7"), (2, "m7"), (7, "maj7"), (0, "maj7")], sidechain=0.3),
    "futurebounce": dict(
        bpm=126, swing=0.0,
        kick="x...x...x...x...", snare="....x.......x...", snare_kind="clap", hat="..o...o...o...o.",
        bass={2: 0, 6: 0, 10: 0, 14: 0, 15: 12}, bass_kind="saw", bass_len=2.0,
        chord_kind="supersaw", chord_steps=[0, 3, 6, 10], chord_len=2.2, chord_gain=1.0,
        lead_kind="supersaw", lead={0: 2, 3: 3, 6: 2, 8: 1, 10: 2, 12: 3}, lead_len=2.0, lead_gain=0.8,
        prog=[(3, "maj"), (10, "maj"), (0, "m"), (8, "maj")], sidechain=0.6),
    "dembow": dict(
        bpm=98, swing=0.0,
        kick="x...x...x...x...", snare="...x..x....x..x.", snare_kind="snare", hat="x.x.x.x.x.x.x.x.",
        bass={0: 0, 6: 0, 10: 7, 14: 5}, bass_kind="808", bass_len=2.5,
        chord_kind="guitar", chord_steps=[0, 6, 10], chord_len=2.0, chord_gain=0.9,
        lead_kind="pluck", lead={0: 2, 2: 1, 3: 2, 6: 3, 8: 2, 10: 1, 11: 2, 14: 0}, lead_len=1.4, lead_gain=1.0,
        prog=[(7, "m"), (3, "maj"), (10, "maj"), (5, "maj")], sidechain=0.25),
    "trap": dict(
        bpm=140, swing=0.0,
        kick="x.....x...x.....", snare="........x.......", snare_kind="clap", hat="xgxgxgxgxgxxxgxg",
        bass={0: 0, 6: 0, 10: 7, 14: 0}, bass_kind="808", bass_len=3.5,
        chord_kind="pad", chord_steps=[0], chord_len=16, chord_gain=0.8,
        lead_kind="bell", lead={0: 2, 3: 1, 6: 3, 10: 2, 12: 1}, lead_len=2.0, lead_gain=1.0,
        prog=[(1, "m"), (9, "maj"), (4, "maj"), (11, "maj")], sidechain=0.3),
    "synthwave": dict(
        bpm=112, swing=0.0,
        kick="x...x...x...x...", snare="....x.......x...", snare_kind="snare", hat="x.x.x.x.x.x.x.x.",
        bass={i: 0 for i in range(0, 16, 2)}, bass_kind="saw", bass_len=1.7,
        chord_kind="pad", chord_steps=[0], chord_len=16, chord_gain=0.9,
        lead_kind="pluck", lead={i: [0, 1, 2, 3, 2, 1, 2, 3][i % 8] for i in range(16)}, lead_len=1.3, lead_gain=0.8,
        prog=[(0, "m"), (8, "maj"), (3, "maj"), (10, "maj")], sidechain=0.35),
}


def note(m): return 440.0 * 2 ** ((m - 69) / 12)
def lp(x, k): return np.convolve(x, np.ones(k) / k, mode="same") if k > 1 else x


def env(n, a=0.003, d=0.2, s=0.0, length=None, rel=0.04):
    t = np.arange(n) / SR
    e = np.minimum(1, t / a) * (s + (1 - s) * np.exp(-t / d))
    if length is not None: e *= np.clip((length + rel - t) / rel, 0, 1)
    return e


def saw(f, n, det=0.0):
    t = np.arange(n) / SR
    return 2 * ((f * (1 + det) * t) % 1) - 1


# ---------------- instruments (mono arrays) ----------------
def i_pluck(m, L):
    n = int((L + 0.25) * SR); f = note(m)
    return lp(saw(f, n) + saw(f, n, 0.006), 4) * env(n, 0.002, 0.12, 0, L, 0.08) * 0.2

def i_square(m, L):
    n = int((L + 0.1) * SR); t = np.arange(n) / SR
    s = np.sign(np.sin(2 * np.pi * note(m) * t) + 0.35)
    return lp(s, 6) * env(n, 0.003, 0.14, 0.1, L, 0.04) * 0.12

def i_epiano(m, L):
    n = int((L + 0.3) * SR); t = np.arange(n) / SR; f = note(m)
    mod = np.sin(2 * np.pi * f * 2 * t) * 1.6 * np.exp(-t / 0.25)
    return np.sin(2 * np.pi * f * t + mod) * env(n, 0.004, 0.35, 0.0, L, 0.12) * 0.09

def i_guitar(m, L):
    n = int((L + 0.3) * SR); f = note(m)
    s = lp(saw(f, n) + 0.5 * saw(f * 2, n), 5)
    return s * env(n, 0.002, 0.22, 0.0, L, 0.1) * 0.12

def i_bell(m, L):
    n = int((L + 0.5) * SR); t = np.arange(n) / SR; f = note(m)
    mod = np.sin(2 * np.pi * f * 3.5 * t) * 2.0 * np.exp(-t / 0.2)
    return np.sin(2 * np.pi * f * t + mod) * np.exp(-t / 0.45) * np.clip((L + 0.45 - t) / 0.2, 0, 1) * 0.16

def i_supersaw(m, L):
    n = int((L + 0.2) * SR); f = note(m)
    s = sum(saw(f, n, d) for d in (-0.012, -0.006, 0.0, 0.006, 0.012)) / 5
    return lp(s, 5) * env(n, 0.006, 0.4, 0.55, L, 0.08) * 0.16

def i_pad(m, L):
    n = int(L * SR); t = np.arange(n) / SR; f = note(m)
    s = np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.004 * t) + 0.25 * saw(f, n, 0.004)
    return s * np.minimum(1, t / 0.15) * np.clip((L - t) / 0.12, 0, 1) * 0.045

def b_pluck(m, L):
    n = int((L + 0.05) * SR); f = note(m)
    return np.tanh((lp(saw(f, n), 8) * 0.7 + np.sin(2 * np.pi * f * np.arange(n) / SR)) * 1.4) * env(n, 0.003, 0.14, 0.15, L) * 0.45

def b_sine_saw(m, L):
    n = int((L + 0.05) * SR); f = note(m)
    return np.tanh((lp(saw(f, n), 10) * 0.6 + np.sin(2 * np.pi * f * np.arange(n) / SR)) * 1.4) * env(n, 0.004, 0.18, 0.35, L) * 0.42

def b_saw(m, L):
    n = int((L + 0.05) * SR); f = note(m)
    s = lp(saw(f, n) + saw(f, n, 0.008), 10) * 0.5 + np.sin(2 * np.pi * f * np.arange(n) / SR)
    return np.tanh(s * 1.5) * env(n, 0.004, 0.25, 0.5, L) * 0.4

def b_808(m, L):
    n = int((L + 0.05) * SR); t = np.arange(n) / SR; f = note(m)
    ph = 2 * np.pi * np.cumsum(f * (1 + 1.2 * np.exp(-t / 0.02))) / SR
    return np.tanh(np.sin(ph) * 1.8) * np.exp(-t / (L * 0.8)) * np.clip((L - t) / 0.05, 0, 1) * 0.5

LEADS = {"pluck": i_pluck, "square": i_square, "bell": i_bell, "supersaw": i_supersaw}
CHORDS = {"epiano": i_epiano, "supersaw": i_supersaw, "guitar": i_guitar, "pad": i_pad}
BASSES = {"pluck": b_pluck, "sine_saw": b_sine_saw, "saw": b_saw, "808": b_808}


def render(dur, cuts, impacts, style, seed=0):
    S = STYLES[style]; rng = np.random.default_rng(seed + 101)
    N = int(SR * dur)
    music = np.zeros((N, 2), np.float32); drums = np.zeros((N, 2), np.float32); fx = np.zeros((N, 2), np.float32)
    step = 60 / S["bpm"] / 4; beat = step * 4; bar = step * 16

    def add(buf, sig, t0, pan=0.0, gain=1.0):
        i = int(t0 * SR)
        if i >= N or i + len(sig) <= 0: return
        if i < 0: sig = sig[-i:]; i = 0
        sig = sig[: N - i] * gain
        l = np.cos((pan + 1) * np.pi / 4); r = np.sin((pan + 1) * np.pi / 4)
        buf[i:i + len(sig), 0] += sig * l; buf[i:i + len(sig), 1] += sig * r

    # drum one-shots
    def kick():
        n = int(0.32 * SR); t = np.arange(n) / SR
        s = np.sin(2 * np.pi * np.cumsum(48 + 140 * np.exp(-t / 0.025)) / SR) * np.exp(-t / 0.16)
        s[:200] += rng.normal(0, 0.3, 200) * np.exp(-np.arange(200) / 40)
        return np.tanh(s * 1.6) * 0.9
    def clap():
        n = int(0.25 * SR); t = np.arange(n) / SR
        s = rng.normal(0, 1, n); s = s - lp(s, 8); e = np.zeros(n)
        for o in (0, 0.011, 0.022): e += (t >= o) * np.exp(-np.clip(t - o, 0, None) / 0.008) * 0.6
        e += (t >= 0.03) * np.exp(-np.clip(t - 0.03, 0, None) / 0.07)
        return s * e * 0.38
    def snare():
        n = int(0.28 * SR); t = np.arange(n) / SR
        nz = rng.normal(0, 1, n); nz = nz - lp(nz, 4)
        return (nz * np.exp(-t / 0.09) * 0.45 + np.sin(2 * np.pi * 185 * t) * np.exp(-t / 0.05) * 0.5) * 0.8
    def hat(open_=False):
        n = int((0.16 if open_ else 0.05) * SR); s = rng.normal(0, 1, n); s = s - lp(s, 3)
        return s * np.exp(-np.arange(n) / SR / (0.05 if open_ else 0.012)) * (0.16 if open_ else 0.10)

    K, SN, HC, HO = kick(), (clap() if S["snare_kind"] == "clap" else snare()), hat(), hat(True)
    bass_fn, chord_fn, lead_fn = BASSES[S["bass_kind"]], CHORDS[S["chord_kind"]], LEADS[S["lead_kind"]]
    cache = {}
    def cached(fn, m, L):
        k = (fn.__name__, m, round(L, 3))
        if k not in cache: cache[k] = fn(m, L)
        return cache[k]

    kick_times = []
    nbars = int(np.ceil(dur / bar)) + 1
    for b in range(nbars):
        pc, q = S["prog"][b % len(S["prog"])]
        r = 60 + pc - (12 if pc > 6 else 0)
        tones = [r + iv for iv in QUAL[q]]
        for s in range(16):
            t = b * bar + s * step + (S["swing"] * step if s % 2 == 1 else 0.0)
            if S["kick"][s] == "x": add(drums, K, t); kick_times.append(t)
            c = S["snare"][s]
            if c in "xg": add(drums, SN, t, 0.05, 1.0 if c == "x" else 0.4)
            c = S["hat"][s]
            if c in "xg": add(drums, HC, t, 0.25, 1.0 if c == "x" else 0.5)
            if c == "o": add(drums, HO, t, 0.25)
            if s in S["bass"]:
                add(music, cached(bass_fn, 36 + pc + S["bass"][s], step * S["bass_len"]), t)
            if s in S["chord_steps"]:
                L = step * S["chord_len"]
                for i, m in enumerate(tones):
                    add(music, cached(chord_fn, m + (12 if S["chord_kind"] in ("epiano", "guitar") else 0), L), t,
                        (-0.3, -0.1, 0.1, 0.3)[i % 4], S["chord_gain"])
            if s in S["lead"]:
                idx = S["lead"][s]; m = tones[idx % len(tones)] + 12 * (1 + idx // len(tones))
                add(music, cached(lead_fn, m, step * S["lead_len"]), t, 0.35 if (s // 2) % 2 else -0.35, S["lead_gain"])

    # sidechain pump on melodic bus, keyed to kick hits
    gain = np.ones(N)
    L = int(0.4 * SR); dip = 1 - S["sidechain"] * np.exp(-np.arange(L) / SR / 0.08)
    for t in kick_times:
        i = int(t * SR)
        if i < N: gain[i:i + L] *= dip[: N - i][: L]
    music *= gain[:, None]

    t = np.arange(N) / SR
    for c in cuts:                      # whoosh into the cut
        Lw = 0.45; n = int(Lw * SR); tt = np.arange(n) / SR
        cs = np.cumsum(np.concatenate([[0], rng.normal(0, 1, n)]))
        idx = np.arange(n); k = np.linspace(14, 2, n).astype(int); a = np.maximum(0, idx - k)
        y = (cs[idx + 1] - cs[a]) / (idx + 1 - a)
        sw = y * (tt / Lw) ** 2 * np.clip((Lw + 0.03 - tt) / 0.06, 0, 1) * 0.55
        add(fx, sw, c - Lw + 0.02, -0.4); add(fx, sw * 0.8, c - Lw + 0.03, 0.4)
    for c in impacts:                   # boom on reveals
        n = int(1.2 * SR); tt = np.arange(n) / SR
        boom = np.sin(2 * np.pi * np.cumsum(40 + 80 * np.exp(-tt / 0.06)) / SR) * np.exp(-tt / 0.45)
        nz = lp(rng.normal(0, 1, n), 3) * np.exp(-tt / 0.12) * 0.35
        add(fx, np.tanh((boom + nz) * 1.5) * 0.9, c, 0.0)

    mix = music + drums * 0.85 + fx * 0.9
    k = int(0.018 * SR); mix[k:, 0] += mix[:-k, 1] * 0.12; mix[k:, 1] += mix[:-k, 0] * 0.12
    mix *= (np.clip(t / 0.01, 0, 1) * np.clip((dur - t) / 1.5, 0, 1))[:, None]
    mix = np.tanh(mix / (np.max(np.abs(mix)) + 1e-9) * 1.3) * 0.89
    return mix


def make_styled(dur, cuts=(), impacts=(), path="music.wav", style="funk", seed=0, lufs=-15.0):
    """Clean styles (ROTATION) are rendered by lib/music_clean.py; legacy names only reproduce old Reels.
    Render a styled track to a 16-bit stereo WAV, loudness ~lufs (if pyloudnorm is installed), peak <= -1.5 dB.
    Returns the measured integrated loudness (or None when pyloudnorm is missing; ffmpeg loudnorm in the mux step covers it)."""
    if style in ROTATION:
        try: from . import music_clean
        except ImportError: import music_clean
        return music_clean.make_clean(dur, cuts, impacts, path, style=style, seed=seed, lufs=lufs)
    mix = render(dur, list(cuts), list(impacts), style, seed).astype(np.float64)
    measured = None
    try:
        import pyloudnorm as pyln
        meter = pyln.Meter(SR); ceil = 10 ** (-2.0 / 20)
        for _ in range(2):
            mix = pyln.normalize.loudness(mix, meter.integrated_loudness(mix), lufs)
            mix = np.tanh(mix / ceil) * ceil
        mix = np.clip(mix, -ceil, ceil); measured = float(meter.integrated_loudness(mix))
    except ImportError:
        pass
    pcm = (mix * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    return measured


# ---------------- rotation ----------------
DEFAULT_STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "content", "music_state.json")


def pick_style(slug, state_path=DEFAULT_STATE):
    """Return (style, seed) for this Reel and remember it. Idempotent per slug; avoids the last 2 styles;
    otherwise picks the least-used clean style (ROTATION) so all six get rotated evenly."""
    state = {"log": []}
    if os.path.exists(state_path):
        with open(state_path) as f: state = json.load(f)
    for e in state["log"]:
        if e["slug"] == slug: return e["style"], e["seed"]
    recent = [e["style"] for e in state["log"][-2:]]
    counts = {s: sum(1 for e in state["log"] if e["style"] == s) for s in ROTATION}
    style = min([s for s in ROTATION if s not in recent], key=lambda s: (counts[s], ROTATION.index(s)))
    seed = int(hashlib.sha1(slug.encode()).hexdigest()[:6], 16) % 1000
    state["log"].append({"slug": slug, "style": style, "seed": seed})
    os.makedirs(os.path.dirname(state_path) or ".", exist_ok=True)
    with open(state_path, "w") as f: json.dump(state, f, indent=1)
    return style, seed


if __name__ == "__main__":
    st, d, p = sys.argv[1], float(sys.argv[2]), sys.argv[3]
    print("lufs", make_styled(d, [d / 3, 2 * d / 3], [d / 2], p, st, seed=1))
