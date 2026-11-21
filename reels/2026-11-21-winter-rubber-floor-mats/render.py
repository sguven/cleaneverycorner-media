"""2026-11-21 — Winter rubber floor mats: salt and slush (car). lib/engine.py + lib/music_upbeat.py (clean style, upbeat=True).
Hook ("Stop..." / common mistake): "STOP SHINING YOUR FLOOR MATS" -> split screen salt-crusted mat | clean matte-black mat,
pill "SHINY = SLIPPERY PEDALS".
    python3 render.py stills [scene,scene] [fracs]      -> stills/*.jpg
    python3 render.py render                            -> winter-rubber-floor-mats.mp4 (+ work/)
Sources checked: Husky Liners "How to clean Weatherbeater floor liners" (remove + shake out; rinse with hose; mild soap
and water + brush for buildup; rinse thoroughly; air dry completely before reinstalling; no bleach/solvents/petroleum
cleaners, no wire brushes; "Never use household floor waxes or tire shine products. These can create slippery surfaces.";
silicone/waxy products slippery), WeatherTech "Top 3 mistakes" (advises against silicone-based cleaners/dressings:
shiny almost always means slippery; vacuum salt and grit regularly), WeatherTech salt-removal article (let cleaner soak,
scrub with a hand brush, rinse all dirty water, dry with microfiber).
"""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from lib.engine import *
from lib.music_upbeat import make_track
from lib.music_styles import pick_style

SLUG = "2026-11-21-winter-rubber-floor-mats"
NAME = "winter-rubber-floor-mats"
PILL_Y = 1515
MX0, MX1 = 46, 1034            # mat outer edge (carpet shows outside)
LIP = 74                       # raised border width

def lmask(draw_fn, blur=2):
    m = Image.new("L", (W, H), 0); draw_fn(ImageDraw.Draw(m))
    m = m.filter(ImageFilter.GaussianBlur(blur)) if blur else m
    return np.array(m).astype(np.float32) / 255

def make_bgs():
    rng = np.random.default_rng(1121)
    # ---------- geometry: raised ribs, heel pad, border lip ----------
    def ribs(d):
        IX0, IX1 = MX0 + LIP + 26, MX1 - LIP - 26
        for r, y in enumerate(range(10, H, 66)):
            off = (r % 2) * 110
            xs = list(range(IX0 - 220 + off, IX1, 220))
            for x in xs:
                a, b = max(IX0, x + 16), min(IX1, x + 220 - 16)
                if b - a > 30 and not (300 < y < 1720 and 330 < (a + b) / 2 < 750 and 1150 < y < 1650):
                    d.rounded_rectangle([a, y, b, y + 28], 12, fill=255)
        for y in range(1170, 1640, 44):                               # heel pad: diamond studs
            for x in range(350 + ((y // 44) % 2) * 22, 740, 44):
                d.polygon([(x, y - 14), (x + 14, y), (x, y + 14), (x - 14, y)], fill=255)
        d.rounded_rectangle([322, 1146, 758, 1660], 30, outline=255, width=12)
    raised = lmask(ribs, 1.2)
    mat = lmask(lambda d: d.rounded_rectangle([MX0, -80, MX1, H + 80], 60, fill=255), 1.5)
    lip = mat - lmask(lambda d: d.rounded_rectangle([MX0 + LIP, -80, MX1 - LIP, H + 80], 40, fill=255), 6)
    lip = np.clip(lip, 0, 1)
    hgt = raised * 0.8 + lip * 1.2 + mat * 0.2
    hb = np.array(Image.fromarray(np.clip(hgt * 120, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))).astype(np.float32) / 120
    gy, gx = np.gradient(hb)
    light = np.clip(1.0 - 9.0 * (gx * 0.6 + gy * 0.8), 0.45, 1.6)
    grain = (lowfreq(5, 4) - 0.5) * 0.06 + (rng.random((H, W)).astype(np.float32) - 0.5) * 0.05
    # carpet around the mat
    carpet = np.zeros((H, W, 3), np.float32) + np.array([58, 60, 66])
    carpet *= (1 + (rng.random((H, W)).astype(np.float32)[..., None] - 0.5) * 0.35)
    # ---------- CLEAN: deep matte black, soft satin (NOT glossy) ----------
    base = np.array([33, 35, 39], np.float32)
    clean_m = base * (light * (1 + grain))[..., None] + raised[..., None] * 6
    sat = np.exp(-((XF - 300) / 260) ** 2 - ((YF - 700) / 700) ** 2) * 0.12
    clean_m = clean_m + sat[..., None] * 120
    CLEAN = blend(carpet, [(clean_m, mat)])
    # ---------- WET (rinsed + soaped, still wet): darker, water beads, specular dots ----------
    wet_m = clean_m * 0.82
    beads = (rng.random((H, W)) > 0.9994).astype(np.float32)
    beads = np.array(Image.fromarray((beads * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(2.5))).astype(np.float32) / 255
    spec = np.clip(np.roll(np.roll(beads, -3, 0), -3, 1) - 0.5, 0, 1) * 1.6
    wet_m = blend(wet_m, [(np.zeros_like(wet_m) + np.array([95, 110, 125]), beads * 0.6), (np.zeros_like(wet_m) + 250, spec * 0.8)])
    WET = blend(carpet, [(wet_m, mat)])
    # ---------- salt + slush layers ----------
    low = (1 - raised) * (1 - lip)                                  # grooves / channels
    salt_f = lowfreq(41, 120) * 0.7
    for cx, cy, r in [(300, 1350, 260), (720, 1450, 230), (520, 900, 220), (820, 700, 180), (240, 520, 160), (600, 1750, 240)]:
        salt_f += np.exp(-(((XF - cx) ** 2 + (YF - cy) ** 2) / (r * r))) * 0.55
    salt_f += (lowfreq(43, 14) - 0.5) * 0.10
    inside = np.clip((salt_f - 0.70) / 0.05, 0, 1)
    tide = np.clip(1 - np.abs(salt_f - 0.71) / 0.012, 0, 1)
    tide = np.array(Image.fromarray((tide * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5))).astype(np.float32) / 255
    crust = np.clip(inside * (0.18 + 0.62 * low) + tide * 0.9, 0, 1) * mat
    haze = np.clip(salt_f - 0.45, 0, 1) * 0.7 * mat                 # faint whitish film left after rinse
    mud_f = lowfreq(61, 90)
    mud = np.clip((mud_f - 0.45) / 0.15, 0, 1) * (0.35 + 0.65 * low) * mat
    speck = (rng.random((H, W)).astype(np.float32) > 0.985).astype(np.float32)
    speck = np.array(Image.fromarray((speck * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0))).astype(np.float32) / 255 * mat
    dull_m = clean_m * 1.05 + np.array([38, 37, 34])                 # dried, greyed rubber
    SALTW = np.zeros_like(clean_m) + np.array([226, 222, 212])
    DIRTY = blend(carpet, [(blend(dull_m, [(np.zeros_like(dull_m) + np.array([92, 78, 62]), mud * 0.75),
                                           (SALTW, crust * 0.62),
                                           (np.zeros_like(dull_m) + np.array([170, 160, 140]), speck * 0.8)]), mat)])
    # RINSED: mud + grit gone, wet, salt film still visible in the channels
    RINSED = blend(WET, [(SALTW * 0.8, (haze * 0.35 + crust * 0.35 * low))])
    return DIRTY, RINSED, WET, CLEAN

DIRTY, RINSED, WET, CLEAN = make_bgs()
def fb(arr): return to_img(arr)

def zigzag(rows, x0, x1, y0, y1):
    pts = []
    for i in range(rows):
        y = y0 + (y1 - y0) * i / (rows - 1)
        pts += [(x0, y), (x1, y)] if i % 2 == 0 else [(x1, y), (x0, y)]
    return pts

def no_shine_badge(img, x, y, p):
    """generic 'SHINE' spray bottle with a red no-sign over it (no brand, drawn)."""
    if p <= 0: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    spray_bottle(lay, x, y, s=0.62, label="SHINE", liquid=(255, 160, 60))
    d = ImageDraw.Draw(lay)
    cx, cy, r = x - 25, y + 60, 175
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=RED, width=26)
    d.line([(cx - r * 0.7, cy - r * 0.7), (cx + r * 0.7, cy + r * 0.7)], fill=RED, width=26)
    s = 0.6 + 0.4 * back(p)
    lay = lay.crop((int(cx - 260), int(cy - 260), int(cx + 260), int(cy + 260)))
    lay = lay.resize((int(520 * s), int(520 * s)), Image.BICUBIC)
    img.alpha_composite(with_alpha(lay, min(1, p * 1.5)), (int(cx - 260 * s), int(cy - 260 * s)))

# ---------- scenes ----------
TOTAL = 3
HOOK = make_hook(DIRTY, CLEAN, [("STOP SHINING", 160, YELLOW), ("YOUR FLOOR MATS", 150, YELLOW)],
                 "SHINY = SLIPPERY PEDALS", mark_xy=(300, 1350), check_xy=(800, 1150), split_to=0.5, labels=True)
HOOK_D = 2.4

SAFETY = make_safety(lambda t: fb(DIRTY), [
    ("never", "No tire shine or silicone: slippery"),
    ("ok", "Mild soap only. No bleach or solvents"),
], title="Safety first", label="BEFORE YOU START")

# step 1: mat out of the car, shake, hose off slush and grit
JET_PATH = zigzag(6, 150, 930, 820, 1800)
C1 = make_card(1, "Pull it out, hose it off", "Rinse the slush and grit outside.", TOTAL)
def x_rinse(t, D):
    t0 = 0.2
    p = ease_io(seg(t, t0, D - 0.15)) * (len(JET_PATH) - 1)
    m = trail_mask(JET_PATH, p, radius=150, blur=24) if t > t0 else 0
    base = fb(blend(DIRTY, [(RINSED, m)]))
    if t > t0 - 0.1:
        tx, ty = path_point(JET_PATH, p)
        nx, ny = 995, 860
        hose_jet(base, nx, ny, tx, ty, t)
        hose_gun(base, nx, ny, ang=math.degrees(math.atan2(ty - ny, tx - nx)))
    pill(base, W // 2, PILL_Y, "MOST SALT RINSES RIGHT OFF", F("Bold", 46), ACC2, INK, ease(seg(t, 0.3, 0.6)))
    return base

# step 2: mild soap + stiff (not wire) brush, then rinse again
BR_PATH = zigzag(7, 170, 910, 860, 1800)
FOAM = [(x, y) for y in range(860, 1820, 95) for x in range(150, 960, 115)]
C2 = make_card(2, "Soap + brush, rinse", "Mild soap in water. Scrub the grooves.", TOTAL)
def x_scrub(t, D):
    t0 = 0.2
    p = ease_io(seg(t, t0, D - 0.3)) * (len(BR_PATH) - 1)
    m = trail_mask(BR_PATH, p, radius=135, blur=20) if t > t0 else 0
    base = fb(blend(RINSED, [(WET, m)]))
    if t > t0 - 0.05:
        x, y = path_point(BR_PATH, p)
        near = [(fx, fy) for fx, fy in FOAM if abs(fy - y) < 170 and abs(fx - x) < 280]
        bubbles(base, t, t0, near, rise=24, rmax=12, speed=2.2)
        scrub_brush(base, x + math.sin(t * 34) * 18, y + 40, ang=math.sin(t * 34) * 7)
    pill(base, W // 2, PILL_Y, "NO WIRE BRUSHES", F("Bold", 46), ACC2, INK, ease(seg(t, 0.3, 0.6)))
    return base

# step 3: dry completely with microfiber, NO shine products, back in dry
TW_PATH = [(150 + 760 * k / 40 + math.cos(k * 0.7) * 70, 1300 + math.sin(k * 0.7) * 420 + 80 * math.sin(k * 0.15)) for k in range(41)]
C3 = make_card(3, "Dry it fully, no shine", "Satin black = grippy and safe.", TOTAL)
SP3 = [(260, 1000), (700, 960), (880, 1250), (420, 1400), (760, 1600), (560, 1180)]
def x_dry(t, D):
    t0 = 0.15
    p = ease_io(seg(t, t0, D - 0.9)) * (len(TW_PATH) - 1)
    m = trail_mask(TW_PATH, p, radius=190, blur=30) if t > t0 else 0
    if t > D - 0.95: m = np.maximum(m, ease(seg(t, D - 0.95, D - 0.6)))   # finish the whole mat
    base = fb(blend(WET, [(CLEAN, m)]))
    if t < D - 0.85:
        x, y = path_point(TW_PATH, p)
        towel(base, x, y, ang=math.sin(t * 8) * 10, col=(90, 170, 230), stripe=(170, 215, 245))
    else:
        sparkles(base, t, D - 0.85, 1.0, SP3)
        no_shine_badge(base, 780, 1080, seg(t, D - 0.85, D - 0.45))
    pill(base, W // 2, PILL_Y, "BACK IN ONLY WHEN DRY", F("Bold", 46), ACC2, INK, ease(seg(t, 0.3, 0.6)))
    return base

SP = [(260, 900), (620, 860), (880, 1000), (430, 1300), (760, 1250), (560, 1120), (900, 1400)]
_BA = make_ba(DIRTY, CLEAN, y_label=SAFE_TOP + 120, handle_y=1240, spark_pts=SP)
def BA(t, D): return _BA(t, D)
BA.impact_at = _BA.impact_at

_OUT = make_loop_outro(CLEAN, HOOK(0.0, HOOK_D), ask="Rubber or carpet mats?")
def OUTRO(t, D): return _OUT(t, D)

SCENES = [
    ("01_hook", HOOK, HOOK_D),
    ("02_safety", SAFETY, 2.2),
    ("03_rinse", with_card(C1, x_rinse), 2.4),
    ("04_scrub", with_card(C2, x_scrub), 2.6),
    ("05_dry", with_card(C3, x_dry), 2.8),
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
