"""2026-11-19 — Winter care for leather car seats (car). lib/engine.py + lib/music_upbeat.py (clean style, upbeat=True).
Hook (question): "IS WINTER CRACKING YOUR SEATS?" -> split screen salt-stained dull leather | clean conditioned leather.
    python3 render.py stills [scene,scene] [fracs]      -> stills/*.jpg
    python3 render.py render                            -> leather-seats-winter.mp4 (+ work/)
Sources checked: J.D. Power "How to clean leather seats" (vacuum seams first; cleaner on a microfiber, not on the seat;
no bleach/ammonia; don't oversaturate; wipe dry; test hidden spot; conditioner optional, protects),
Motor1 leather care tips (vacuum grit that scratches; no glass cleaner/bleach/ammonia/alcohol; perforated seats: apply
to brush/applicator, not the seat; dry away from direct heat; clean before conditioning; ~every 3 months).
"""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from lib.engine import *
from lib.music_upbeat import make_track
from lib.music_styles import pick_style

SLUG = "2026-11-19-leather-seats-winter"
NAME = "leather-seats-winter"
PILL_Y = 1515
X0, X1 = 200, 880                                   # centre insert between the two bolsters
SEAMS = [470, 690, 910, 1130, 1350, 1570, 1790]

def lmask(draw_fn, blur=2):
    m = Image.new("L", (W, H), 0); draw_fn(ImageDraw.Draw(m))
    m = m.filter(ImageFilter.GaussianBlur(blur)) if blur else m
    return np.array(m).astype(np.float32) / 255

def make_bgs():
    rng = np.random.default_rng(1119)
    # ---- shape / shading (puffy channels + side bolsters) ----
    shade = np.ones((H, W), np.float32)
    ins = (XF > X0) & (XF < X1)
    edges = [250] + SEAMS + [2010]
    for a, b in zip(edges[:-1], edges[1:]):
        band = (YF >= a) & (YF < b) & ins
        u = (YF - a) / (b - a)
        puff = np.clip(np.sin(np.pi * np.clip(u, 0, 1)), 0, 1) ** 0.6
        shade = np.where(band, 0.62 + 0.42 * puff - 0.10 * u, shade)
    top = (YF < 250) & ins
    shade = np.where(top, 0.62 + 0.4 * np.clip(np.sin(np.pi * np.clip(YF / 250, 0, 1) * 0.5 + np.pi / 2), 0, 1) ** 0.6, shade)
    lb = XF <= X0; rb = XF >= X1
    ul = np.clip((XF + 80) / (X0 + 80), 0, 1); ur = np.clip((W + 80 - XF) / (W + 80 - X1), 0, 1)
    shade = np.where(lb, 0.5 + 0.55 * np.clip(np.sin(np.pi * ul), 0, 1) ** 0.7, shade)
    shade = np.where(rb, 0.5 + 0.55 * np.clip(np.sin(np.pi * ur), 0, 1) ** 0.7, shade)
    shade *= 1 - 0.18 * ((XF - W / 2) / (W / 2)) ** 2
    shade = np.array(Image.fromarray(np.clip(shade * 200, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(4))).astype(np.float32) / 200
    grain = (lowfreq(3, 3) - 0.5) * 0.10 + (rng.random((H, W)).astype(np.float32) - 0.5) * 0.05
    base_col = np.array([150, 86, 44], np.float32)                       # cognac
    leather = base_col * (shade + grain)[..., None]
    # perforations in the insert pads
    perf = lmask(lambda d: [d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=255)
                            for a, b in zip([250] + SEAMS, SEAMS + [2010]) for y in range(a + 50, b - 40, 34)
                            for x in range(X0 + 40 + ((y // 34) % 2) * 17, X1 - 30, 34)], 0.8)
    leather = blend(leather, [(leather * 0.35, perf * 0.85)])
    # seam grooves + double stitching
    groove = lmask(lambda d: ([d.line([(X0, y), (X1, y)], fill=255, width=10) for y in SEAMS]
                              + [d.line([(x, 0), (x, H)], fill=255, width=14) for x in (X0, X1)]), 4)
    leather = blend(leather, [(np.zeros_like(leather) + np.array([40, 22, 12]), groove * 0.85)])
    def stitch_mask():
        def dr(d):
            for y in SEAMS:
                for off in (-20, 20):
                    for x in range(X0 + 14, X1 - 10, 26): d.line([(x, y + off), (x + 14, y + off)], fill=255, width=5)
            for x in (X0, X1):
                for off in (-24, 24):
                    for y in range(0, H, 26): d.line([(x + off, y), (x + off, y + 14)], fill=255, width=5)
        return lmask(dr, 0.8)
    st = stitch_mask()
    # ---- CLEAN: rich colour, satin sheen ----
    sheen = np.zeros((H, W), np.float32)
    for a, b in zip([250] + SEAMS, SEAMS + [2010]):
        c = a + (b - a) * 0.32
        sheen += np.exp(-((YF - c) / 26) ** 2) * ins * (0.55 + 0.45 * np.sin(XF / 210 + a))
    sheen += np.exp(-((XF - 70) / 30) ** 2) * 0.6 + np.exp(-((XF - 1000) / 30) ** 2) * 0.5
    sheen = np.clip(sheen, 0, 1)
    clean = leather * np.array([1.12, 1.08, 1.0]) + 6
    clean = blend(clean, [(np.zeros_like(clean) + np.array([255, 214, 170]), sheen * 0.38),
                          (np.zeros_like(clean) + np.array([238, 214, 172]), st)])
    # ---- CONDITIONED-but-not-buffed = clean minus some sheen; CLEANED (dull, no salt) ----
    dull = leather * 0.86 + np.array([18, 16, 14])
    dull = blend(dull, [(np.zeros_like(dull) + np.array([205, 188, 160]), st * 0.85)])
    # ---- DIRTY: dull + seam grime + grit + salt tide marks + fine cracks ----
    salt_f = lowfreq(41, 110) * 0.75
    for cx, cy, r in [(300, 1240, 170), (650, 820, 150), (860, 1480, 140), (420, 1660, 160), (140, 900, 120)]:
        salt_f += np.exp(-(((XF - cx) ** 2 + (YF - cy) ** 2) / (r * r))) * 0.55
    salt_f += (lowfreq(43, 12) - 0.5) * 0.12
    salt_f *= np.clip((YF - 520) / 120, 0, 1) * 0.15 + 0.85 * np.clip((YF - 520) / 120, 0, 1)   # keep the top clear
    inside = np.clip((salt_f - 0.72) / 0.04, 0, 1)
    tide = np.clip(1 - np.abs(salt_f - 0.73) / 0.012, 0, 1)
    tide = np.array(Image.fromarray((tide * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5))).astype(np.float32) / 255
    crack_n = lowfreq(57, 7)
    cracks = np.clip(1 - np.abs(crack_n - 0.5) / 0.03, 0, 1) * np.clip((shade - 0.85) * 4, 0, 1)
    speck = (rng.random((H, W)).astype(np.float32) > 0.988).astype(np.float32)
    speck = np.array(Image.fromarray((speck * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.1))).astype(np.float32) / 255
    seam_grime = lmask(lambda d: ([d.line([(X0, y), (X1, y)], fill=255, width=46) for y in SEAMS]
                                  + [d.line([(x, 0), (x, H)], fill=255, width=50) for x in (X0, X1)]), 14)
    gritty = blend(dull * 0.9 + np.array([10, 10, 12]), [(np.zeros_like(dull) + np.array([58, 48, 40]), seam_grime * 0.7),
                                                           (np.zeros_like(dull) + np.array([200, 196, 186]), speck * 0.75)])
    salted = blend(dull, [(np.zeros_like(dull) + np.array([232, 226, 214]), inside * 0.42),
                          (np.zeros_like(dull) + np.array([250, 248, 240]), tide * 0.9)])
    dirty = blend(gritty, [(np.zeros_like(dull) + np.array([232, 226, 214]), inside * 0.42),
                           (np.zeros_like(dull) + np.array([250, 248, 240]), tide * 0.9),
                           (np.zeros_like(dull) + np.array([214, 176, 140]), cracks * 0.45)])
    return dirty, salted, dull, clean

DIRTY, VACUUMED, CLEANED, CLEAN = make_bgs()
def fb(arr): return to_img(arr)

def zigzag(rows, x0=170, x1=910, y0=780, y1=1420):
    pts = []
    for i in range(rows):
        y = y0 + (y1 - y0) * i / (rows - 1)
        pts += [(x0, y), (x1, y)] if i % 2 == 0 else [(x1, y), (x0, y)]
    return pts

def applicator(img, x, y, ang=0):
    lay = Image.new("RGBA", (360, 360), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    rrect(d, [80, 140, 280, 240], 24, fill=(245, 248, 250), outline=INK, width=8)
    rrect(d, [80, 205, 280, 240], 12, fill=(255, 210, 120), outline=INK, width=6)
    img.alpha_composite(lay.rotate(ang, resample=Image.BICUBIC), (int(x - 180), int(y - 220)))

# ---------- scenes ----------
TOTAL = 3
HOOK = make_hook(DIRTY, CLEAN, [("IS WINTER", 150, YELLOW), ("CRACKING", 160, YELLOW), ("YOUR SEATS?", 150, YELLOW)],
                 "THE FIX: 3 STEPS", mark_xy=(300, 1240), check_xy=(820, 1030), split_to=0.5, labels=True)
HOOK_D = 2.4

SAFETY = make_safety(lambda t: fb(DIRTY), [
    ("never", "No bleach, ammonia or glass cleaner"),
    ("ok", "Test a hidden spot first"),
], title="Safety first", label="BEFORE YOU START")

# step 1: crevice tool along the seams pulls out grit and salt crumbs
VAC_PATH = [(X0, 760), (X0, 1460), (X0 + 20, 1350), (X1 - 20, 1350), (X1, 1130), (X0 + 20, 1130), (X0 + 20, 910), (X1 - 20, 910)]
C1 = make_card(1, "Vacuum the grit", "Salt and sand scratch leather.", TOTAL)
def x_vac(t, D):
    t0 = 0.25
    p = ease_io(seg(t, t0, D - 0.2)) * (len(VAC_PATH) - 1)
    m = trail_mask(VAC_PATH, p, radius=120, blur=20) if t > t0 else 0
    base = fb(blend(DIRTY, [(VACUUMED, m)]))
    if t > t0 - 0.1:
        x, y = path_point(VAC_PATH, p)
        crevice_tool(base, x + math.sin(t * 30) * 5, y, wand_to=(1300, 2100))
    pill(base, W // 2, PILL_Y, "GET INTO THE SEAMS", F("Bold", 46), ACC2, INK, ease(seg(t, 0.3, 0.6)))
    return base

# step 2: soft brush with leather cleaner lifts the salt rings
BR_PATH = zigzag(8, 60, 1020, 700, 1720)
FOAM = [(x, y) for y in range(720, 1720, 90) for x in range(90, 1000, 110)]
C2 = make_card(2, "Clean, then wipe dry", "Cleaner on the brush, not the seat.", TOTAL)
def x_brush(t, D):
    t0 = 0.2
    p = ease_io(seg(t, t0, D - 0.3)) * (len(BR_PATH) - 1)
    m = trail_mask(BR_PATH, p, radius=120, blur=18) if t > t0 else 0
    base = fb(blend(VACUUMED, [(CLEANED, m)]))
    if t > t0 - 0.05:
        x, y = path_point(BR_PATH, p)
        near = [(fx, fy) for fx, fy in FOAM if abs(fy - y) < 160 and abs(fx - x) < 260]
        bubbles(base, t, t0, near, rise=24, rmax=10, speed=2.2)
        detail_brush(base, x + math.sin(t * 36) * 14, y, ang=-30 + math.sin(t * 36) * 6)
    pill(base, W // 2, PILL_Y, "SOFT BRUSH, LIGHT PRESSURE", F("Bold", 46), ACC2, INK, ease(seg(t, 0.3, 0.6)))
    return base

# step 3: thin coat of conditioner, buff -> satin sheen
CO_PATH = [(120 + 840 * k / 50 + math.cos(k * 0.6) * 90, 1180 + math.sin(k * 0.6) * 330 + 60 * math.sin(k * 0.13)) for k in range(51)]
C3 = make_card(3, "Condition, then buff", "Thin coat. About every 3 months.", TOTAL)
SP3 = [(300, 900), (640, 860), (860, 1000), (420, 1250), (760, 1300), (560, 1100)]
def x_cond(t, D):
    t0 = 0.2
    p = ease_io(seg(t, t0, D - 0.6)) * (len(CO_PATH) - 1)
    m = trail_mask(CO_PATH, p, radius=170, blur=26) if t > t0 else 0
    base = fb(blend(CLEANED, [(CLEAN, m)]))
    if t < D - 0.55:
        x, y = path_point(CO_PATH, p)
        applicator(base, x, y, ang=math.sin(t * 9) * 8)
    else:
        sparkles(base, t, D - 0.55, 1.0, SP3)
    pill(base, W // 2, PILL_Y, "NO DIRECT HEAT TO DRY", F("Bold", 46), ACC2, INK, ease(seg(t, 0.3, 0.6)))
    return base

SP = [(260, 900), (620, 860), (880, 1000), (430, 1300), (760, 1250), (560, 1120), (900, 1400)]
_BA = make_ba(DIRTY, CLEAN, y_label=SAFE_TOP + 120, handle_y=1240, spark_pts=SP)
def BA(t, D): return _BA(t, D)
BA.impact_at = _BA.impact_at

_OUT = make_loop_outro(CLEAN, HOOK(0.0, HOOK_D), ask="Leather or cloth seats?")
def OUTRO(t, D): return _OUT(t, D)

SCENES = [
    ("01_hook", HOOK, HOOK_D),
    ("02_safety", SAFETY, 2.2),
    ("03_vac", with_card(C1, x_vac), 2.4),
    ("04_brush", with_card(C2, x_brush), 2.6),
    ("05_cond", with_card(C3, x_cond), 2.6),
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
