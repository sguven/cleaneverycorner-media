import numpy as np, wave, sys

SR = 44100
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 37.5
BPM = 100
BEAT = 60 / BPM
BAR = 4 * BEAT
N = int(SR * DUR)
out = np.zeros((N, 2), np.float32)
rng = np.random.default_rng(1)

def note(m): return 440.0 * 2 ** ((m - 69) / 12)

def add(sig, t0, pan=0.0, gain=1.0):
    i = int(t0 * SR)
    if i >= N: return
    sig = sig[: N - i] * gain
    l = np.cos((pan + 1) * np.pi / 4); r = np.sin((pan + 1) * np.pi / 4)
    out[i:i + len(sig), 0] += sig * l
    out[i:i + len(sig), 1] += sig * r

def env(n, a=0.005, d=0.4, s=0.0, rel=0.05, length=None):
    t = np.arange(n) / SR
    e = np.minimum(1, t / a) * (s + (1 - s) * np.exp(-t / d))
    if length is not None:
        e *= np.clip((length + rel - t) / rel, 0, 1)
    return e

def epiano(m, length):
    n = int((length + 0.6) * SR); t = np.arange(n) / SR; f = note(m)
    s = np.sin(2*np.pi*f*t) + 0.35*np.sin(2*np.pi*2*f*t)*np.exp(-t/0.25) + 0.12*np.sin(2*np.pi*3*f*t)*np.exp(-t/0.12)
    s *= 1 + 0.08*np.sin(2*np.pi*4.5*t)  # tremolo
    return s * env(n, 0.004, 0.9, 0.25, 0.4, length) * 0.16

def pluck(m, length=0.35):
    n = int((length + 0.3) * SR); t = np.arange(n) / SR; f = note(m)
    s = np.sign(np.sin(2*np.pi*f*t)) * 0.3 + np.sin(2*np.pi*f*t)
    # soften square: lowpass via moving average
    k = 18; s = np.convolve(s, np.ones(k)/k, mode="same")
    return s * env(n, 0.002, 0.16, 0, 0.1, length) * 0.10

def bass(m, length):
    n = int((length + 0.1) * SR); t = np.arange(n) / SR; f = note(m)
    s = np.sin(2*np.pi*f*t) + 0.25*np.sin(2*np.pi*2*f*t)
    return s * env(n, 0.01, 0.6, 0.5, 0.08, length) * 0.30

def kick():
    n = int(0.35 * SR); t = np.arange(n) / SR
    f = 50 + 110 * np.exp(-t / 0.03)
    ph = 2*np.pi*np.cumsum(f)/SR
    return np.sin(ph) * np.exp(-t / 0.12) * 0.55

def hat():
    n = int(0.06 * SR); s = rng.normal(0, 1, n)
    s = s - np.convolve(s, np.ones(6)/6, mode="same")  # highpass-ish
    return s * np.exp(-np.arange(n)/SR / 0.015) * 0.06

def clap():
    n = int(0.2 * SR); s = rng.normal(0, 1, n)
    s = np.convolve(s, np.ones(4)/4, mode="same")
    e = np.exp(-np.arange(n)/SR / 0.05)
    return s * e * 0.10

def shaker():
    n = int(0.08 * SR); s = rng.normal(0, 1, n)
    s = s - np.convolve(s, np.ones(3)/3, mode="same")
    t = np.arange(n)/SR
    return s * np.minimum(1, t/0.02) * np.exp(-t/0.03) * 0.035

# C  G  Am  F  (C major), voicings around middle C
prog = [(48, [60, 64, 67, 71]), (43, [59, 62, 67, 69]), (45, [60, 64, 69, 71]), (41, [60, 65, 69, 72])]
arp_pat = [0, 2, 1, 3, 2, 1, 3, 2]
nbars = int(np.ceil(DUR / BAR))
for b in range(nbars):
    t0 = b * BAR
    root, ch = prog[b % 4]
    section = 0 if b < 2 else 1  # first 2 bars: intro (no drums)
    for m in ch:
        add(epiano(m, BAR * 0.95), t0, pan=rng.uniform(-0.3, 0.3))
    # bass: root on 1, fifth-ish pickup on 3.5
    add(bass(root, BEAT * 2.4), t0)
    add(bass(root + 7 if b % 2 == 0 else root + 12, BEAT * 0.9), t0 + BEAT * 2.5)
    add(bass(root, BEAT * 0.9), t0 + BEAT * 3.5, gain=0.8)
    if section:
        for i, k in enumerate(arp_pat):
            add(pluck(ch[k] + 12), t0 + i * BEAT / 2, pan=0.35 if i % 2 else -0.35, gain=0.9)
        for q in range(4):
            if q in (0, 2): add(kick(), t0 + q * BEAT)
            if q in (1, 3): add(clap(), t0 + q * BEAT, pan=0.05)
            add(hat(), t0 + q * BEAT + BEAT / 2, pan=0.2)
            add(shaker(), t0 + q * BEAT + BEAT / 4, pan=-0.25)
            add(shaker(), t0 + q * BEAT + 3 * BEAT / 4, pan=-0.25, gain=0.7)
        if b % 4 == 3: add(kick(), t0 + 3.5 * BEAT, gain=0.6)

# gentle sidechain pump on everything except drums is approximated globally
t = np.arange(N) / SR
pump = 1 - 0.18 * np.exp(-((t % BEAT) / 0.09)) * (t > 2 * BAR)
out *= pump[:, None]

# simple stereo reverb-ish: a few delayed, filtered copies
rev = np.zeros_like(out)
for d, g in [(0.031, 0.25), (0.047, 0.2), (0.071, 0.15), (0.113, 0.1)]:
    k = int(d * SR)
    rev[k:, 0] += out[:-k, 1] * g; rev[k:, 1] += out[:-k, 0] * g
out += np.convolve(rev[:, 0], np.ones(40)/40, mode="same")[:, None] * 0 + rev

# fades
fi = np.clip(t / 0.4, 0, 1); fo = np.clip((DUR - t) / 2.0, 0, 1)
out *= (fi * fo)[:, None]
out /= np.max(np.abs(out)) + 1e-9
out *= 10 ** (-1.5 / 20)
pcm = (out * 32767).astype(np.int16)
with wave.open(sys.argv[2] if len(sys.argv) > 2 else "music.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("ok")
