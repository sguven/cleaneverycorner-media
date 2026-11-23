"""2026-11-23 — Clean a glass stovetop (home). lib/engine.py + lib/music_upbeat.py (clean style, upbeat=True).
Hook (myth-bust / "not X, it's Y"): "DON'T SCRUB IT. SCRAPE IT." -> split screen burnt, hazy glass top | glossy clean glass,
pill "NO SCRATCHES". Then safety -> 3 steps -> before/after wipe -> loop outro.
    python3 render.py stills [scene,scene] [fracs]      -> stills/*.jpg
    python3 render.py render                            -> glass-stovetop.mp4 (+ work/)
Sources checked (2026-11-23): GE Appliances glass cooktop cleaning instructions (let the cooktop cool before cleaner and
scraping on burned-on residue; razor scraper at about 45 degrees; wipe residue off with a dry cloth or paper towel; sliding
rough pans scratches; sugary spills can pit the glass), Maytag "How to clean a glass cooktop" (warm-not-hot surface,
baking soda + water paste on burnt food, scrape at 45 degrees with an oven mitt, nonabrasive pad + soft dry cloth; avoid
steel wool, abrasive cleaners, bleach, ammonia, rust remover), KitchenAid ceramic glass cooktop care (scraper designed
for ceramic glass at ~45 degrees; no steel wool, abrasive powder cleansers, chlorine bleach, ammonia, rust remover).
"""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from lib.engine import *
from lib.music_upbeat import make_track
from lib.music_styles import pick_style

SLUG = "2026-11-23-glass-stovetop"
NAME = "glass-stovetop"
PILL_Y = 1515
BURNERS = [(290, 830, 190), (800, 780, 160), (290, 1380, 175), (790, 1320, 215)]
CRUST_L = (290, 1380)        # boil-over ring on the front-left burner (hook marker)
CRUST_R = (800, 1300)        # spill on the big front-right burner

def lmask(draw_fn, blur=2):
    m = Image.new("L", (W, H), 0); draw_fn(ImageDraw.Draw(m))
    m = m.filter(ImageFilter.GaussianBlur(blur)) if blur else m
    return np.array(m).astype(np.float32) / 255

def col(c): return np.zeros((H, W, 3), np.float32) + np.array(c, np.float32)

def make_bgs():
    rng = np.random.default_rng(1123)
    # ---- black glass with soft studio reflection ----
    base = col((20, 22, 27)) * (0.9 + 0.2 * lowfreq(3, 200))[..., None]
    rings = lmask(lambda d: [d.ellipse([x - r, y - r, x + r, y + r], outline=255, width=6) for x, y, r in BURNERS]
                  + [d.ellipse([x - r * 0.72, y - r * 0.72, x + r * 0.72, y + r * 0.72], outline=150, width=3) for x, y, r in BURNERS], 1.2)
    hatch = np.zeros((H, W), np.float32)
    for x, y, r in BURNERS:
        dist = np.sqrt((XF - x) ** 2 + (YF - y) ** 2)
        inside = np.clip((r - 10 - dist) / 6, 0, 1)
        hatch += inside * np.clip(np.sin(dist / 9.0) * 3 - 2.2, 0, 1) * 0.35
    glass = blend(base, [(col((120, 126, 138)), rings * 0.85), (col((70, 74, 84)), np.clip(hatch, 0, 1))])
    # front-edge control icons (simple dots + bar, no text)
    ctrl = lmask(lambda d: [d.ellipse([cx - 18, 1730 - 18, cx + 18, 1730 + 18], outline=255, width=5) for cx in (200, 400, 680, 880)]
                 + [d.line([(470, 1730), (610, 1730)], fill=255, width=6)], 1)
    glass = blend(glass, [(col((110, 118, 130)), ctrl * 0.6)])
    sheen = np.exp(-((XF * 0.55 + YF - 900) / 150) ** 2) * 0.16 + np.exp(-((XF * 0.55 + YF - 1180) / 45) ** 2) * 0.12
    clean = blend(glass, [(col((235, 242, 255)), np.clip(sheen, 0, 1))])
    glint = lmask(lambda d: [d.line([(140, 560), (360, 430)], fill=255, width=10), d.line([(700, 1660), (900, 1540)], fill=255, width=8),
                             d.line([(820, 520), (930, 455)], fill=255, width=6)], 3)
    clean = blend(clean, [(col((255, 255, 255)), glint * 0.55)])
    # ---- grime: dull haze, white boil-over residue, grease specks, burnt crust ----
    haze = np.clip(0.35 + 0.5 * lowfreq(11, 90), 0, 1)
    dull = blend(glass, [(col((112, 104, 94)), haze * 0.5)])
    wipes = np.clip(np.sin((XF * 0.8 - YF * 0.6) / 70 + lowfreq(12, 120) * 6) * 1.5 - 0.8, 0, 1) * lowfreq(13, 160)
    dull = blend(dull, [(col((150, 146, 140)), wipes * 0.35)])                         # old swirl marks
    residue = np.zeros((H, W), np.float32)
    for (x, y, r), k in zip(BURNERS, (21, 22, 23, 24)):
        dist = np.sqrt((XF - x - 14) ** 2 + (YF - y + 10) ** 2)
        residue += (np.exp(-((dist - r * 1.08) / 12) ** 2) + 0.6 * np.exp(-((dist - r * 0.55) / 10) ** 2)) * np.clip(lowfreq(k, 50) * 1.8 - 0.3, 0, 1)
    speck = (rng.random((H, W)).astype(np.float32) > 0.985).astype(np.float32)
    speck = np.array(Image.fromarray((speck * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.6))).astype(np.float32) / 255
    drops = lmask(lambda d: [d.ellipse([x - s, y - s * 0.8, x + s, y + s * 0.8], fill=255) for x, y, s in
                             [(random.Random(i).randint(80, 1000), random.Random(i + 99).randint(420, 1680), random.Random(i + 7).randint(5, 16)) for i in range(70)]], 1.5)
    # burnt crust: broken ring around the front-left burner + a big spill on the front-right burner
    nz = lowfreq(41, 24)
    dl = np.sqrt((XF - CRUST_L[0]) ** 2 + (YF - CRUST_L[1]) ** 2)
    ringL = np.exp(-((dl - 150) / 70) ** 2) * np.clip(lowfreq(42, 70) * 1.8 - 0.05, 0, 1.1) + np.exp(-(dl / 95) ** 2) * 0.7
    dr = np.sqrt(((XF - CRUST_R[0]) / 1.25) ** 2 + (YF - CRUST_R[1]) ** 2)
    spillR = np.exp(-(dr / 150) ** 2) * 1.1 + np.exp(-(((XF - 640) / 70) ** 2 + ((YF - 1470) / 50) ** 2)) * 0.8
    small = np.exp(-(((XF - 830) / 60) ** 2 + ((YF - 760) / 50) ** 2)) * 0.9
    crust_f = ringL + spillR + small
    crust = np.clip((crust_f - 0.42 - nz * 0.35) * 6.0, 0, 1)
    crust = np.array(Image.fromarray((crust * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))).astype(np.float32) / 255
    core = np.clip((crust_f - 0.62 - nz * 0.3) * 5, 0, 1)
    edge = np.clip(crust - core * 1.2, 0, 1)
    pits = (rng.random((H, W)).astype(np.float32) > 0.93).astype(np.float32) * crust
    grimy = blend(dull, [(col((214, 210, 200)), np.clip(residue, 0, 1) * 0.85),
                         (col((150, 110, 60)), np.clip(drops * 0.55 + speck * 0.5, 0, 0.7))])
    dirty = blend(grimy, [(col((112, 70, 34)), edge * 0.97),
                         (col((34, 20, 10)), core * 0.98),
                         (col((160, 120, 80)), pits * 0.7)])
    # PASTE: white baking-soda paste dabbed over the crust (slightly bigger, lumpy edge)
    pz = lowfreq(51, 30)
    paste = np.clip((crust_f - 0.30 - pz * 0.3) * 3.0, 0, 1)
    paste = np.array(Image.fromarray((paste * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))).astype(np.float32) / 255
    paste_col = blend(col((238, 236, 228)), [(col((205, 203, 196)), np.clip(lowfreq(52, 14) - 0.4, 0, 1) * 1.2)])
    pasted = blend(dirty, [(paste_col, paste * 0.96)])
    # SMEAR: crust scraped off; leftover cloudy paste film + the general haze (wiped away in step 3)
    smear = blend(grimy, [(col((176, 172, 164)), paste * 0.5)])
    return dirty, pasted, smear, clean, paste, crust

DIRTY, PASTED, SMEAR, CLEAN, PASTE, CRUST = make_bgs()
def fb(arr): return to_img(arr)

def vstrokes(cols, y0, y1):
    pts = []
    for i, x in enumerate(cols): pts += [(x, y0), (x, y1)] if i % 2 == 0 else [(x, y1), (x, y0)]
    return pts

# ---------- scenes ----------
TOTAL = 3
HOOK = make_hook(DIRTY, CLEAN, [("DON'T SCRUB IT.", 140, YELLOW), ("SCRAPE IT.", 175, YELLOW)],
                 "NO SCRATCHES", mark_xy=CRUST_L, check_xy=(800, 1060), split_to=0.5, labels=True)
HOOK_D = 2.2

SAFETY = make_safety(DIRTY, [
    ("ok", "Let the cooktop cool first"),
    ("no", "No steel wool, bleach or ammonia"),
    ("never", "Never mix cleaners"),
], title="Safety first", label="BEFORE YOU START")

# step 1: baking soda paste dabbed onto the burnt spots
C1 = make_card(1, "Baking soda paste", "Mix with a little water.\nDab it on the burnt spots.", TOTAL)
DABS = [(CRUST_L[0] + 150 * math.cos(a), CRUST_L[1] + 150 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 7)[:-1]] + \
       [CRUST_L, (CRUST_R[0] - 120, CRUST_R[1]), CRUST_R, (CRUST_R[0] + 120, CRUST_R[1]), (640, 1470), (830, 760)]
def x_paste(t, D):
    t0, t1 = 0.25, D - 0.35
    p = ease_io(seg(t, t0, t1))
    k = p * len(DABS)
    m = np.zeros((H, W), np.float32)
    for i, (x, y) in enumerate(DABS):
        q = clamp(k - i)
        if q > 0: m = np.maximum(m, np.exp(-(((XF - x) ** 2 + (YF - y) ** 2) / (150 * (0.4 + 0.6 * q)) ** 2)) * 1.6 * q)
    m = np.clip(m, 0, 1) * PASTE
    base = fb(blend(DIRTY, [(PASTED, m)]))
    if t > t0 - 0.1 and t < t1 + 0.2:
        i = min(int(k), len(DABS) - 1); x, y = DABS[i]
        # small spatula dabbing the paste
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        bob = abs(math.sin(t * 18)) * 20
        d.line([(x + 40, y - 40 - bob), (x + 300, y - 300 - bob)], fill=INK, width=30)
        d.line([(x + 40, y - 40 - bob), (x + 300, y - 300 - bob)], fill=ACCENT, width=18)
        rrect(d, [x - 50, y - 70 - bob, x + 70, y + 20 - bob], 30, fill=(240, 238, 230), outline=INK, width=7)
        base.alpha_composite(lay)
    pill(base, W // 2, PILL_Y, "LET IT SOFTEN FIRST", F("Bold", 46), ACC2, INK, ease(seg(t, 0.3, 0.6)))
    return base

# step 2: razor scraper, low angle, pushes the crust off
C2 = make_card(2, "Scraper at 45°", "Glass-safe razor scraper.\nLight pressure.", TOTAL)
SC_PATH = vstrokes([170, 290, 410], 1580, 1200) + [(410, 1200), (650, 1560)] + vstrokes([650, 790, 930], 1560, 1130)
SC_N = len(SC_PATH) - 1
def x_scrape(t, D):
    t0 = 0.2
    p = ease_io(seg(t, t0, D - 0.3)) * SC_N
    m = trail_mask(SC_PATH, p, radius=105, blur=10) if t > t0 else np.zeros((H, W), np.float32)
    base = fb(blend(PASTED, [(SMEAR, m)]))
    if t > t0 - 0.05 and t < D - 0.25:
        x, y = path_point(SC_PATH, p)
        razor_scraper(base, x, y, ang=math.sin(t * 30) * 3)
        # curls of crust pushed ahead of the blade
        d = ImageDraw.Draw(base)
        for j in range(5):
            cx = x - 80 + j * 40 + math.sin(t * 20 + j) * 6; cy = y - 20 - (j % 2) * 12
            if CRUST[int(clamp(cy, 0, H - 1)), int(clamp(cx, 0, W - 1))] > 0.05 or j % 2 == 0:
                d.ellipse([cx - 11, cy - 8, cx + 11, cy + 8], fill=(90, 56, 24), outline=(40, 24, 10), width=2)
    pill(base, W // 2, PILL_Y, "NO SCRUB PADS", F("Bold", 46), ACC2, INK, ease(seg(t, 0.3, 0.6)))
    return base

# step 3: wipe the residue off, buff dry with a soft cloth
TW_PATH = vstrokes([160, 360, 560, 760, 940], 760, 1640)
C3 = make_card(3, "Wipe, then buff dry", "Soft, dry microfiber.\nStreak-free shine.", TOTAL)
SP3 = [(240, 900), (640, 860), (880, 1000), (420, 1250), (760, 1300), (560, 1450), (300, 1600)]
def x_buff(t, D):
    t0 = 0.15
    p = ease_io(seg(t, t0, D - 0.55)) * (len(TW_PATH) - 1)
    m = trail_mask(TW_PATH, p, radius=135, blur=22) if t > t0 else 0
    base = fb(blend(SMEAR, [(CLEAN, m)]))
    if t < D - 0.5:
        x, y = path_point(TW_PATH, p)
        towel(base, x, y, ang=math.sin(t * 10) * 8, col=(120, 190, 240), stripe=(190, 225, 250))
    else:
        sparkles(base, t, D - 0.5, 1.0, SP3)
    pill(base, W // 2, PILL_Y, "DRY CLOTH = NO STREAKS", F("Bold", 46), ACC2, INK, ease(seg(t, 0.3, 0.6)))
    return base

SP = [(240, 900), (620, 820), (880, 1000), (430, 1300), (760, 1250), (560, 1120), (900, 1450)]
BA = make_ba(DIRTY, CLEAN, y_label=SAFE_TOP + 120, handle_y=1100, spark_pts=SP)

_OUT = make_loop_outro(CLEAN, HOOK(0.0, HOOK_D), ask="Glass top or gas?")
def OUTRO(t, D): return _OUT(t, D)

SCENES = [
    ("01_hook", HOOK, HOOK_D),
    ("02_safety", SAFETY, 2.3),
    ("03_paste", with_card(C1, x_paste), 2.4),
    ("04_scrape", with_card(C2, x_scrape), 2.7),
    ("05_buff", with_card(C3, x_buff), 2.3),
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
