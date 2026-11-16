"""2026-11-16 — Deodorize your kitchen sink drain (home). lib/engine.py + lib/music_upbeat.py (clean style, upbeat=True).
Hook: "IT'S NOT YOUR DRAIN" — the smell is usually the gunk on the disposal splash guard.
    python3 render.py stills [scene,scene] [fracs]      -> work/stills/*.jpg
    python3 render.py render                            -> sink-drain-deodorize.mp4 (+ work/)
Sources checked: Maytag disposer odor guide (power off, scrub both sides of the splash guard with dish soap + small brush,
baking soda, citrus with cold water), InSinkErator (ice + citrus wedges, cool water), Sears Home Services (no bleach /
harsh chemicals, no boiling water), plumbing guidance (hot tap water rather than boiling on plastic pipes).
"""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from lib.engine import *
from lib.music_upbeat import make_track
from lib.music_styles import pick_style

SLUG = "2026-11-16-sink-drain-deodorize"
NAME = "sink-drain-deodorize"
CX, CY = 540, 1100                 # drain centre
R_HOLE, R_GUARD, R_FL = 76, 300, 385
PILL_Y = 1515

def lmask(draw_fn, blur=2):
    m = Image.new("L", (W, H), 0); draw_fn(ImageDraw.Draw(m))
    m = m.filter(ImageFilter.GaussianBlur(blur)) if blur else m
    return np.array(m).astype(np.float32) / 255

def disc(r, cx=CX, cy=CY):
    return lambda d: d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)

SLITS = [math.radians(22.5 + k * 45) for k in range(8)]

def make_bgs():
    rng = np.random.default_rng(1116)
    rr = random.Random(1116)
    R = np.sqrt((XF - CX) ** 2 + (YF - CY) ** 2)
    # ---- brushed stainless sink ----
    cols = np.array(Image.fromarray((rng.random((1, W)) * 255).astype(np.uint8)).resize((W, H), Image.NEAREST)).astype(np.float32) / 255
    brushed = (cols - 0.5) * 10 + (lowfreq(5, 40) - 0.5) * 8
    bowl = np.clip(R / 1100, 0, 1)                      # bowl slopes toward the drain: darker near centre
    steel = np.stack([150 + bowl * 55, 158 + bowl * 55, 168 + bowl * 52], -1) + brushed[..., None]
    band = np.exp(-(((XF * 0.55 + YF * 0.45) - 980) / 260) ** 2) * 34   # soft diagonal highlight
    steel += band[..., None]
    # ---- polished flange ring ----
    fl = lmask(disc(R_FL), 2)
    flc = np.stack([200 - (R - R_GUARD) * 0.25, 206 - (R - R_GUARD) * 0.25, 214 - (R - R_GUARD) * 0.22], -1)
    ang = np.arctan2(YF - CY, XF - CX)
    flc += (np.cos(ang * 2 + 0.8) * 16)[..., None] + ((np.sin(R * 0.9) * 2))[..., None]
    a = blend(steel, [(np.zeros_like(steel) + 70, lmask(lambda d: d.ellipse([CX - R_FL - 6, CY - R_FL - 2, CX + R_FL + 6, CY + R_FL + 14], fill=255), 10) * 0.35),
                      (flc, fl)])
    # ---- black rubber splash guard ----
    gm = lmask(disc(R_GUARD), 1.5)
    rub = np.stack([38 + 0 * R, 40 + 0 * R, 45 + 0 * R], -1)
    shine = np.exp(-(((XF - (CX - 110)) ** 2 + (YF - (CY - 120)) ** 2) / (2 * 120 ** 2))) * 40
    rub += shine[..., None] + (np.clip(1 - R / R_GUARD, 0, 1) * -8)[..., None]
    a = blend(a, [(rub, gm)])
    def slits(d):
        for t in SLITS:
            d.line([(CX + math.cos(t) * (R_HOLE - 4), CY + math.sin(t) * (R_HOLE - 4)),
                    (CX + math.cos(t) * (R_GUARD - 28), CY + math.sin(t) * (R_GUARD - 28))], fill=255, width=8)
    SL = lmask(slits, 1)
    a = blend(a, [(np.zeros_like(a) + 8, SL * 0.95), (np.zeros_like(a) + 6, lmask(disc(R_HOLE), 1.5))])
    ridge = lmask(lambda d: d.ellipse([CX - R_GUARD + 10, CY - R_GUARD + 10, CX + R_GUARD - 10, CY + R_GUARD - 10], outline=255, width=5), 2)
    a = blend(a, [(np.zeros_like(a) + 86, ridge * 0.5)])
    CLEANA = a.astype(np.float32)

    # ---- grime layers ----
    noise = lowfreq(31, 24)
    gunk_sl = lmask(lambda d: [d.line([(CX + math.cos(t) * R_HOLE, CY + math.sin(t) * R_HOLE),
                                       (CX + math.cos(t) * (R_GUARD - 30), CY + math.sin(t) * (R_GUARD - 30))], fill=255, width=34) for t in SLITS], 9)
    gunk_hole = lmask(lambda d: d.ellipse([CX - 150, CY - 150, CX + 150, CY + 150], fill=255), 16) * (1 - lmask(disc(R_HOLE - 6), 2))
    blot = np.clip((lowfreq(37, 30) - 0.55) * 3.0, 0, 1) * gm
    GUNK = np.clip(np.maximum(np.maximum(gunk_sl * 0.95, gunk_hole), blot * 0.6) * (0.6 + noise * 0.55), 0, 1)
    seam = lmask(lambda d: d.ellipse([CX - R_GUARD - 24, CY - R_GUARD - 24, CX + R_GUARD + 24, CY + R_GUARD + 24], outline=255, width=44), 10)
    SEAM = np.clip(seam * (0.5 + lowfreq(41, 30) * 0.8), 0, 1)
    FILM = np.clip((lowfreq(43, 26) - 0.3) * 1.2, 0, 1) * 0.3
    def spots(d):
        for _ in range(26):
            x, y = rr.uniform(40, 1040), rr.uniform(300, 1880)
            if (x - CX) ** 2 + (y - CY) ** 2 < (R_FL + 30) ** 2: continue
            r = rr.uniform(10, 26); d.ellipse([x - r, y - r, x + r, y + r], outline=255, width=4)
    SPOT = lmask(spots, 1.5) * 0.55
    def bits(d):
        for _ in range(70):                               # coffee grounds
            an = rr.uniform(0, 6.28); r = rr.uniform(90, 360); x, y = CX + math.cos(an) * r, CY + math.sin(an) * r
            s = rr.uniform(3, 7); d.ellipse([x - s, y - s, x + s, y + s], fill=255)
    BITS = lmask(bits, 0.8)
    def grains(d):
        for _ in range(16):                               # rice grains / food bits
            an = rr.uniform(0, 6.28); r = rr.uniform(110, 420); x, y = CX + math.cos(an) * r, CY + math.sin(an) * r
            o = rr.uniform(0, 3.14); L = rr.uniform(14, 22)
            d.line([(x - math.cos(o) * L, y - math.sin(o) * L), (x + math.cos(o) * L, y + math.sin(o) * L)], fill=255, width=12)
    GRAIN = lmask(grains, 1)
    def herbs(d):
        for _ in range(7):
            an = rr.uniform(0, 6.28); r = rr.uniform(140, 330); x, y = CX + math.cos(an) * r, CY + math.sin(an) * r
            s = rr.uniform(8, 14); d.polygon([(x - s, y), (x, y - s * 0.6), (x + s, y + 2), (x, y + s * 0.7)], fill=255)
    HERB = lmask(herbs, 0.8)
    C_GUNK = np.array([78, 58, 32], np.float32); C_SEAM = np.array([138, 98, 52], np.float32)
    C_FILM = np.array([150, 140, 118], np.float32); C_SPOT = np.array([228, 230, 228], np.float32)
    C_BIT = np.array([52, 36, 24], np.float32); C_GRAIN = np.array([236, 226, 196], np.float32)
    C_HERB = np.array([70, 120, 50], np.float32)
    def state(k=1.0):
        if k <= 0: return CLEANA
        d = CLEANA * (1 - 0.10 * k) + np.array([10, 6, -4], np.float32) * k
        return blend(d, [(C_FILM, FILM * k), (C_SPOT, SPOT * k), (C_SEAM, SEAM * 0.85 * k), (C_GUNK, GUNK * 0.9 * k),
                         (C_BIT, BITS * 0.9 * k), (C_GRAIN, GRAIN * k), (C_HERB, HERB * k)])
    return state, CLEANA

STATE, CLEAN = make_bgs()
DIRTY = STATE(1.0)

def fb(arr): return to_img(arr)
def layer(): return Image.new("RGBA", (W, H), (0, 0, 0, 0))

def green_wisps(img, t, x_max=W):
    lay = layer(); wisps(lay, t, [CX - 220, CX - 60, CX + 120, CX + 260], CY - 120, height=360, col=(120, 200, 70), width=16, amp=30, alpha=210)
    if x_max < W:
        a = np.array(lay.getchannel("A")); a[:, int(max(0, x_max)):] = 0; lay.putalpha(Image.fromarray(a))
    img.alpha_composite(lay)

# ---------- props ----------
def shaker(img, x, y, ang=-30):
    lay = Image.new("RGBA", (360, 360), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    rrect(d, [110, 120, 250, 330], 30, fill=(255, 255, 255), outline=INK, width=8)
    rrect(d, [126, 190, 234, 270], 12, fill=(255, 196, 40))
    rrect(d, [100, 70, 260, 128], 16, fill=ACCENT, outline=INK, width=8)
    for k in range(4): d.ellipse([132 + k * 28, 88, 144 + k * 28, 100], fill=INK)
    img.alpha_composite(lay.rotate(ang + 180, resample=Image.BICUBIC), (int(x - 180), int(y - 180)))

def falling(img, x, y, t, dist=260):
    d = ImageDraw.Draw(img); rng = random.Random(int(t * 30))
    for _ in range(46):
        f = rng.random(); px = x + rng.uniform(-36, 36) + f * 20; py = y + f * dist
        r = rng.uniform(2.5, 5.5); d.ellipse([px - r, py - r, px + r, py + r], fill=(255, 255, 255, int(255 * (1 - f * 0.5))))

def water_stream(img, t, top, col=(200, 230, 255), alpha=170, width=56):
    lay = layer(); d = ImageDraw.Draw(lay)
    for k in range(6):
        off = math.sin(t * 9 + k) * 3
        d.line([(CX + off - width / 2 + k * width / 6, top), (CX + off - width / 2 + k * width / 6, CY)], fill=col + (alpha,), width=int(width / 5))
    d.line([(CX - 6, top), (CX - 6, CY)], fill=(255, 255, 255, 200), width=8)
    rng = random.Random(int(t * 30))
    for _ in range(22):                                   # splash ring
        an = rng.uniform(0, 6.28); r = rng.uniform(40, 120)
        x, y = CX + math.cos(an) * r, CY + math.sin(an) * r * 0.8; s = rng.uniform(4, 9)
        d.ellipse([x - s, y - s, x + s, y + s], fill=col + (200,))
    img.alpha_composite(lay)

def soda_pile(img, k):
    if k <= 0: return
    d = ImageDraw.Draw(img); r = 70 * k
    d.ellipse([CX - r, CY - r * 0.9, CX + r, CY + r * 0.9], fill=(250, 250, 248))
    rng = random.Random(3)
    for _ in range(int(60 * k)):
        an = rng.uniform(0, 6.28); q = rng.random() ** 0.5 * (r + 40)
        x, y = CX + math.cos(an) * q, CY + math.sin(an) * q; s = rng.uniform(2, 4)
        d.ellipse([x - s, y - s, x + s, y + s], fill=(255, 255, 255))

def ice_cube(img, x, y, s=1.0, ang=0):
    lay = Image.new("RGBA", (200, 200), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    rrect(d, [40, 40, 160, 160], 26, fill=(205, 235, 250, 235), outline=(120, 170, 200), width=6)
    d.line([(64, 70), (100, 58)], fill=(255, 255, 255), width=10); d.line([(62, 92), (66, 120)], fill=(255, 255, 255), width=8)
    lay = lay.rotate(ang, resample=Image.BICUBIC)
    if s != 1.0: lay = lay.resize((max(1, int(200 * s)), max(1, int(200 * s))), Image.BICUBIC)
    img.alpha_composite(lay, (int(x - lay.width / 2), int(y - lay.height / 2)))

def lemon(img, x, y, s=1.0, ang=0):
    lay = Image.new("RGBA", (220, 220), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.pieslice([20, 30, 200, 210], 180, 360, fill=(255, 214, 40), outline=INK, width=7)
    d.pieslice([38, 48, 182, 192], 180, 360, fill=(255, 244, 170))
    for k in range(1, 5):
        a_ = math.radians(180 + k * 36); d.line([(110, 120), (110 + math.cos(a_) * 70, 120 + math.sin(a_) * 70)], fill=(255, 214, 40), width=5)
    lay = lay.rotate(ang, resample=Image.BICUBIC)
    if s != 1.0: lay = lay.resize((max(1, int(220 * s)), max(1, int(220 * s))), Image.BICUBIC)
    img.alpha_composite(lay, (int(x - lay.width / 2), int(y - lay.height / 2)))

# ---------- scenes ----------
TOTAL = 3
def _hook_extra(base, t, D, sx): green_wisps(base, t, sx)
HOOK = make_hook(DIRTY, CLEAN, [("IT'S NOT", 150, YELLOW), ("YOUR DRAIN", 160, YELLOW)],
                 "THE SMELL HIDES HERE", mark_xy=(CX - 150, CY + 20), check_xy=(860, 860), split_to=0.5,
                 labels=False, extra=_hook_extra)
def HOOK_F(t, D): return HOOK(t, D)
HOOK_F.headline_until = HOOK.headline_until
HOOK_D = 2.4

SAFETY = make_safety(lambda t: fb(DIRTY), [
    ("never", "Power OFF first. No hands inside"),
    ("no", "No bleach or drain-cleaner mixes"),
], title="Safety first", label="BEFORE YOU START")

C1 = make_card(1, "Scrub the splash guard", "Dish soap + small brush, both sides.", TOTAL)
SPIRAL = [(CX + math.cos(a_) * r, CY + math.sin(a_) * r * 0.95)
          for a_, r in ((i * 0.55, 400 - i * 13) for i in range(26))]
def x_scrub(t, D):
    t0 = 0.25
    p = ease_io(seg(t, t0, D - 0.4)) * (len(SPIRAL) - 1)
    m = trail_mask(SPIRAL, p, radius=125, blur=18) if t > t0 else 0
    base = fb(blend(DIRTY, [(CLEAN, m)]))
    if t0 - 0.1 < t < D - 0.3:
        x, y = path_point(SPIRAL, p)
        sd = ImageDraw.Draw(base); rng = random.Random(int(t * 15))
        for _ in range(14):                               # suds trailing the brush
            bx, by = x + rng.uniform(-110, 110), y + rng.uniform(-60, 90); r = rng.uniform(8, 20)
            sd.ellipse([bx - r, by - r, bx + r, by + r], fill=(255, 255, 255, 220), outline=(200, 225, 240), width=3)
        scrub_brush(base, x + math.sin(t * 30) * 14, y + 60, ang=-12 + math.sin(t * 30) * 6)
    else:
        green_wisps(base, t, W if t < t0 else 0)
    pill(base, W // 2, PILL_Y, "POWER OFF FIRST", F("Bold", 46), ACC2, INK, ease(seg(t, 0.3, 0.6)))
    return base

C2 = make_card(2, "Baking soda + hot water", "1/4 cup, wait 15 min, then hot tap water.", TOTAL)
def x_soda(t, D):
    base = fb(CLEAN)
    T1, T2 = 1.3, 1.55
    pile = ease(seg(t, 0.2, T1)) * (1 - ease(seg(t, T2 + 0.3, D - 0.2)))
    soda_pile(base, pile)
    if t < T1:
        fl = layer(); falling(fl, CX + 20, CY - 300, t); base.alpha_composite(fl)
        shaker(base, CX - 10, CY - 420, ang=-25 + math.sin(t * 24) * 8)
        pill(base, W // 2, PILL_Y, "1/4 CUP, WAIT 15 MIN", F("Bold", 46), ACC2, INK, ease(seg(t, 0.2, 0.5)))
    else:
        water_stream(base, t, 700, col=(210, 232, 250), alpha=int(170 * ease(seg(t, T1, T2))))
        wisps(base, t, [CX - 150, CX + 150, CX - 40], CY - 40, height=300, col=(255, 255, 255), width=14, alpha=170)
        pill(base, W // 2, PILL_Y, "HOT TAP WATER, NOT BOILING", F("Bold", 44), ACC2, INK, ease(seg(t, T1, T1 + 0.3)))
    return base

C3 = make_card(3, "Grind ice + citrus peels", "Power back on, cold water running.", TOTAL)
DROPS = [("ice", -140, 0.15, 20), ("lemon", 120, 0.45, -25), ("ice", 40, 0.8, 35), ("lemon", -60, 1.15, 15), ("ice", 150, 1.45, -10)]
def x_ice(t, D):
    base = fb(CLEAN)
    water_stream(base, t, 700, col=(150, 205, 250), alpha=150)
    for kind, dx, t0, ang in DROPS:
        f = seg(t, t0, t0 + 0.75)
        if f <= 0 or f >= 1: continue
        y = 720 + (CY - 720) * ease_io(min(1, f / 0.7)); x = CX + dx * (1 - ease(seg(f, 0.55, 1)))
        s = 1.0 - 0.9 * ease(seg(f, 0.6, 1.0))
        (ice_cube if kind == "ice" else lemon)(base, x, y, s, ang + t * 120)
    if t > 1.9:
        sparkles(base, t, 1.9, 0.9, [(250, 880), (830, 900), (300, 1330), (800, 1320), (540, 820)])
    pill(base, W // 2, PILL_Y, "COLD WATER RUNNING", F("Bold", 46), ACC2, INK, ease(seg(t, 0.25, 0.55)))
    return base

SP = [(250, 880), (830, 900), (330, 1300), (800, 1330), (640, 980), (900, 1150), (180, 1120)]
_BA = make_ba(DIRTY, CLEAN, y_label=SAFE_TOP + 120, handle_y=1660 - 160, spark_pts=SP)
def BA(t, D): return _BA(t, D)
BA.impact_at = _BA.impact_at

_OUT = make_loop_outro(CLEAN, HOOK(0.0, HOOK_D), ask="Did you know this one?")
def OUTRO(t, D): return _OUT(t, D)

SCENES = [
    ("01_hook", HOOK_F, HOOK_D),
    ("02_safety", SAFETY, 2.6),
    ("03_scrub", with_card(C1, x_scrub), 3.0),
    ("04_soda", with_card(C2, x_soda), 3.0),
    ("05_ice", with_card(C3, x_ice), 2.6),
    ("06_ba", BA, 2.6),
    ("07_outro", OUTRO, 2.3),
]

def music(dur, cuts, impacts, path):
    style, seed = pick_style(SLUG)
    print("music style", style, seed)
    make_track(dur, cuts, [0.0] + list(impacts), path, style=style, seed=seed, upbeat=True)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "stills"
    work = os.path.join(HERE, "work")
    if mode == "stills":
        only = sys.argv[2].split(",") if len(sys.argv) > 2 and sys.argv[2] else None
        fr = tuple(float(x) for x in sys.argv[3].split(",")) if len(sys.argv) > 3 else (0.0, 0.5, 0.95)
        print("\n".join(stills(SCENES, os.path.join(HERE, "stills"), fr, only)))
    else:
        print("total", build(SCENES, work, os.path.join(HERE, NAME + ".mp4"), music, limit=0.5))
