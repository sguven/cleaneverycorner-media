"""2026-11-25 — Red wine and gravy stains on a tablecloth (home). lib/engine.py + lib/music_upbeat.py (clean style, upbeat=True).
Hook (myth-bust / "it's not the wine, it's the dryer"): "THE DRYER LOCKS IT IN" -> split screen wine + gravy stained
tablecloth | clean white cloth, pill "3 STEPS, NO HEAT". Then safety -> 3 steps (blot + cold-water flush, dish soap on
gravy, oxygen-bleach soak + wash + air-dry check) -> before/after wipe -> loop outro ("Wine or gravy?").
    python3 render.py stills [scene,scene] [fracs]      -> stills/*.jpg
    python3 render.py render                            -> red-wine-gravy-tablecloth.mp4 (+ work/)
Sources checked (2026-11-25): Tide wine-stain guide (blot with an absorbent cloth; start with cold water; repeat before the
dryer because drying sets the stain; heat can make wine stains permanent; chlorine bleach only on white fabric), Tide
gravy-stain guide (pretreat with liquid detergent, gently work in; repeat before drying), Clorox gravy guide (scrape
excess, blot, rub in liquid dish soap, rinse; air-dry and check, repeat if needed), extension stain guides (Illinois /
K-State: blot, cold water first, oxygen bleach soak for washable fabrics, check before drying). Oxygen bleach: follow the
label, washable fabrics only (not wool/silk). Never mix chlorine bleach with vinegar/acids or ammonia (CDC/EPA).
"""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from lib.engine import *
from lib.music_upbeat import make_track
from lib.music_styles import pick_style

SLUG = "2026-11-25-red-wine-gravy-tablecloth"
NAME = "red-wine-gravy-tablecloth"
PILL_Y = 1505
WINE = (320, 1010, 160)        # x, y, radius of the red-wine splash (left half: dirty side of the hook)
GRAVY = (470, 1290, 115)       # gravy splat, crosses the hook split line

def lmask(draw_fn, blur=2):
    m = Image.new("L", (W, H), 0); draw_fn(ImageDraw.Draw(m))
    m = m.filter(ImageFilter.GaussianBlur(blur)) if blur else m
    return np.array(m).astype(np.float32) / 255

def col(c): return np.zeros((H, W, 3), np.float32) + np.array(c, np.float32)
def gblur(a, r):
    return np.array(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))).astype(np.float32) / 255

def blob(cx, cy, R, seed, rough=0.45, sharp=7.0, sx=1.0):
    d = np.sqrt(((XF - cx) / (R * sx)) ** 2 + ((YF - cy) / R) ** 2)
    n = lowfreq(seed, 40) - 0.5
    return np.clip((1.0 - d + rough * n) * sharp, 0, 1), d, n

def make_bgs():
    # ---- white cotton tablecloth: warm white, soft folds, teal border stripes, a plate at the top ----
    base = col((247, 244, 238)) * (0.94 + 0.08 * lowfreq(5, 260))[..., None]
    fold = np.exp(-((XF - 760 - 0.08 * YF) / 26) ** 2) * 0.05 + np.exp(-((YF - 700 - 0.05 * XF) / 30) ** 2) * 0.04
    base = base * (1 - fold)[..., None]
    stripes = lmask(lambda d: [d.rectangle([0, 1650, W, 1672], fill=255), d.rectangle([0, 1696, W, 1706], fill=255),
                               d.rectangle([0, 1742, W, 1764], fill=255)], 1)
    base = blend(base, [(col((14, 150, 170)), stripes * 0.75)])
    plate = lmask(lambda d: d.ellipse([700, 200, 1300, 640], fill=255), 2)
    well = lmask(lambda d: d.ellipse([790, 270, 1210, 570], fill=255), 6)
    rim = lmask(lambda d: d.ellipse([700, 200, 1300, 640], outline=255, width=10), 2)
    shadow = lmask(lambda d: d.ellipse([705, 225, 1310, 665], fill=255), 22)
    base = blend(base, [(col((150, 140, 128)), shadow * 0.35), (col((255, 255, 255)), plate),
                        (col((236, 236, 240)), well * 0.8), (col((14, 150, 170)), rim * 0.8)])
    # ---- red wine: irregular splash, darker dried rim, satellite droplets + a drip trail ----
    wx, wy, wr = WINE
    wcore, wd, wn = blob(wx, wy, wr, 31, rough=0.55, sx=1.15)
    inner, _, _ = blob(wx, wy, wr * 0.8, 31, rough=0.55, sx=1.15)
    rng = random.Random(1125)
    drops = lmask(lambda d: [d.ellipse([x - s, y - s * 0.85, x + s, y + s * 0.85], fill=255) for x, y, s in
                             [(wx + rng.uniform(-1, 1) * wr * 1.9, wy + rng.uniform(-0.9, 1.3) * wr * 1.15, rng.randint(7, 24)) for _ in range(26)]]
                  + [d.line([(wx + wr * 0.9, wy - 30), (wx + wr * 1.7, wy - 120), (wx + wr * 2.0, wy - 140)], fill=255, width=26),
                     d.ellipse([wx + wr * 2.0 - 30, wy - 170, wx + wr * 2.0 + 30, wy - 110], fill=255)], 1.5)
    wine = np.clip(wcore + drops, 0, 1)
    wrim = np.clip(wine - inner * 0.7, 0, 1)
    # ---- gravy: brown, glossy core + translucent grease halo ----
    gx, gy, gr = GRAVY
    gcore, _, _ = blob(gx, gy, gr, 47, rough=0.5, sx=1.3)
    ghalo = gblur(blob(gx, gy, gr * 1.35, 48, rough=0.5, sx=1.3)[0], 10)
    gdrops = lmask(lambda d: [d.ellipse([gx + a - s, gy + b - s, gx + a + s, gy + b + s], fill=255) for a, b, s in
                              [(-200, -60, 16), (190, 80, 12), (-150, 120, 10), (230, -70, 14), (60, -170, 9)]], 1.5)
    gravy = np.clip(gcore + gdrops, 0, 1)
    gloss = gblur(np.clip(gcore - blob(gx - 30, gy - 30, gr * 0.6, 49, rough=0.3, sx=1.3)[0] * 0, 0, 1) *
                  np.exp(-(((XF - gx + 50) / 60) ** 2 + ((YF - gy + 35) / 22) ** 2)), 4)
    # ---- weave texture applied on top of every state (stains soak into the fabric) ----
    weave = 1 - 0.045 * (np.abs(np.sin(XF * 0.55)) * 0.5 + np.abs(np.sin(YF * 0.55)) * 0.5) - 0.02 * lowfreq(7, 8)
    def fab(a): return a * weave[..., None]
    clean = base
    wine_full = [(col((128, 22, 52)), wine * 0.92), (col((84, 10, 36)), wrim * 0.85)]
    wine_pale = [(col((214, 150, 165)), wine * 0.55), (col((190, 120, 140)), wrim * 0.35)]
    gravy_full = [(col((196, 170, 126)), ghalo * 0.55), (col((132, 84, 40)), gravy * 0.93),
                  (col((240, 220, 190)), gloss * 0.6)]
    gravy_faint = [(col((226, 214, 192)), ghalo * 0.30)]
    DIRTY = fab(blend(clean, wine_full + gravy_full))
    BLOT = fab(blend(clean, wine_pale + gravy_full))
    SOAP = fab(blend(clean, wine_pale + gravy_faint))
    CLEAN = fab(clean)
    return DIRTY, BLOT, SOAP, CLEAN, wine, gravy

DIRTY, BLOT, SOAP, CLEAN, WINE_M, GRAVY_M = make_bgs()
NOISE = np.clip(lowfreq(61, 50) * 0.7 + lowfreq(62, 12) * 0.3, 0, 1)
def fb(arr): return to_img(arr)

# ---------- props ----------
def paper_towel(img, x, y, press=0.0, ang=0):
    """folded white paper towel pad with quilted dots; press 0..1 squashes it (blotting)."""
    lay = Image.new("RGBA", (420, 420), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    s = 1 - 0.08 * press
    x0, y0, x1, y1 = 210 - 150 * s, 210 - 110 * s, 210 + 150 * s, 210 + 110 * s
    rrect(d, [x0 + 10, y0 + 18, x1 + 10, y1 + 18], 26, fill=(60, 60, 70, 70))
    rrect(d, [x0, y0, x1, y1], 26, fill=(255, 255, 255), outline=INK, width=8)
    for i in range(5):
        for j in range(4):
            cx, cy = x0 + 45 + i * (x1 - x0 - 90) / 4, y0 + 40 + j * (y1 - y0 - 80) / 3
            d.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=(222, 228, 234))
    # wine soaked into the pad as it blots
    if press > 0:
        d.ellipse([210 - 90, 230 - 50, 210 + 90, 230 + 50], fill=(200, 90, 120, int(150 * min(1, press))))
    img.alpha_composite(lay.rotate(ang, resample=Image.BICUBIC), (int(x - 210), int(y - 210)))

def soap_bottle(img, x, y, ang=-35):
    """generic dish-soap squeeze bottle (no label/brand), nozzle near (x, y) pointing down-left."""
    lay = Image.new("RGBA", (520, 520), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    rrect(d, [180, 150, 340, 470], 50, fill=(110, 200, 150), outline=INK, width=8)
    rrect(d, [205, 230, 315, 420], 30, fill=(160, 228, 190))
    rrect(d, [215, 95, 305, 160], 14, fill=ACCENT, outline=INK, width=8)
    d.polygon([(240, 95), (280, 95), (266, 40), (254, 40)], fill=ACC2, outline=INK, width=6)
    lay = lay.rotate(180 + ang, resample=Image.BICUBIC)
    img.alpha_composite(lay, (int(x - 260), int(y - 470)))

def drip_drops(img, x, y, t, col=(110, 200, 150), n=3):
    d = ImageDraw.Draw(img)
    for i in range(n):
        f = (t * 2.2 + i / n) % 1
        cy = y + f * 160
        d.ellipse([x - 13, cy - 18, x + 13, cy + 14], fill=col, outline=INK, width=4)

# ---------- scenes ----------
TOTAL = 3
HOOK = make_hook(DIRTY, CLEAN, [("THE DRYER", 165, YELLOW), ("LOCKS IT IN", 165, YELLOW)],
                 "3 STEPS, NO HEAT", mark_xy=WINE[:2], check_xy=(810, 1060), split_to=0.5, labels=True)
HOOK_D = 2.2

SAFETY = make_safety(DIRTY, [
    ("ok", "Check the care label first"),
    ("ok", "Gloves for oxygen bleach"),
    ("never", "Never mix bleach with vinegar or ammonia"),
], title="Safety first", label="BEFORE YOU START")

# step 1: blot the wine (no rubbing), flush with cold water from the back
C1 = make_card(1, "Blot, don't rub", "Then flush with cold water\nfrom the back.", TOTAL)
DABS = [(WINE[0] - 70, WINE[1] - 40), (WINE[0] + 80, WINE[1] + 30), (WINE[0] - 40, WINE[1] + 90), (WINE[0] + 60, WINE[1] - 80), WINE[:2]]
def x_blot(t, D):
    t0, t1 = 0.25, D - 0.3
    p = ease_io(seg(t, t0, t1))
    m = dissolve(p, NOISE, 0.3) * np.clip(WINE_M * 1.4, 0, 1)
    base = fb(blend(DIRTY, [(BLOT, m)]))
    if t1 + 0.1 > t > t0 - 0.15:
        k = min(len(DABS) - 1, int(seg(t, t0, t1) * len(DABS)))
        x, y = DABS[k]
        ph = (seg(t, t0, t1) * len(DABS)) % 1
        press = math.sin(ph * math.pi)
        paper_towel(base, x, y - 90 * (1 - press), press=p + 0.2, ang=-6)
    pill(base, W // 2, PILL_Y, "COLD WATER, NOT HOT", F("Bold", 46), ACC2, INK, ease(seg(t, 0.3, 0.6)))
    return base

# step 2: dish soap on the gravy grease, work in gently, rinse cold
C2 = make_card(2, "Dish soap on gravy", "Work it in gently.\nRinse with cold water.", TOTAL)
GB = [(GRAVY[0] + a, GRAVY[1] + b) for a, b in [(-110, -20), (-40, 40), (30, -50), (100, 20), (-70, 70), (60, 60), (0, -10), (140, -40)]]
def x_soap(t, D):
    gx, gy, gr = GRAVY
    t0 = 0.9
    p = ease_io(seg(t, t0, D - 0.3))
    m = dissolve(p, NOISE, 0.3)
    base = fb(blend(BLOT, [(SOAP, m)]))
    if t < t0 + 0.1:
        q = ease(seg(t, 0.0, 0.25))
        soap_bottle(base, gx + 30 + (1 - q) * 300, gy - 120 - (1 - q) * 200)
        if t > 0.25: drip_drops(base, gx + 30, gy - 110, t)
    else:
        if t < D - 0.35:
            sponge(base, gx + 70 * math.cos(t * 9), gy - 10 + 40 * math.sin(t * 9), ang=math.sin(t * 9) * 8)
        bubbles(base, t, t0, GB, rmax=18, speed=1.6)
    pill(base, W // 2, PILL_Y, "SOAP CUTS THE GREASE", F("Bold", 46), ACC2, INK, ease(seg(t, 0.3, 0.6)))
    return base

# step 3: oxygen bleach soak (washable fabric, label directions), wash, air-dry and check
C3 = make_card(3, "Oxygen bleach soak", "Washable fabric, per label.\nWash, then air-dry and check.", TOTAL)
SB = [(150, 1600), (300, 1240), (470, 1480), (620, 1150), (760, 1560), (900, 1300), (230, 900), (980, 980)]
def x_soak(t, D):
    p = ease_io(seg(t, 0.3, D - 0.45))
    m = dissolve(p, NOISE, 0.3)
    arr = blend(SOAP, [(CLEAN, m)])
    tint = ease(seg(t, 0.0, 0.3)) * (1 - ease(seg(t, D - 0.4, D - 0.1)))
    arr = blend(arr, [(col((150, 205, 245)), np.full((H, W), 0.28 * tint, np.float32))])
    base = fb(arr)
    if tint > 0.05: bubbles(base, t, 0.0, SB, rmax=16, speed=1.1)
    timer(base, 790, 1140, ease_io(seg(t, 0.2, D - 0.4)), "SOAK", unit="per label", R=195)
    if t > D - 0.4: sparkles(base, t, D - 0.4, 0.9, [(320, 1000), (520, 1380), (240, 1250)])
    pill(base, W // 2, PILL_Y, "NO DRYER UNTIL IT'S GONE", F("Bold", 46), ACC2, INK, ease(seg(t, 0.3, 0.6)))
    return base

SP = [(240, 900), (620, 820), (880, 1000), (430, 1300), (760, 1250), (560, 1120), (900, 1450)]
BA = make_ba(DIRTY, CLEAN, y_label=SAFE_TOP + 120, handle_y=1200, spark_pts=SP)

_OUT = make_loop_outro(CLEAN, HOOK(0.0, HOOK_D), ask="Wine or gravy?")
def OUTRO(t, D): return _OUT(t, D)

SCENES = [
    ("01_hook", HOOK, HOOK_D),
    ("02_safety", SAFETY, 2.3),
    ("03_blot", with_card(C1, x_blot), 2.5),
    ("04_soap", with_card(C2, x_soap), 2.6),
    ("05_soak", with_card(C3, x_soak), 2.6),
    ("06_ba", BA, 2.6),
    ("07_outro", OUTRO, 2.4),
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
