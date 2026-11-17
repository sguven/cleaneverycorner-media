"""2026-11-17 — Fix foggy headlights (car). lib/engine.py + lib/music_upbeat.py (clean style, upbeat=True).
Hook: "TOOTHPASTE WON'T LAST" (myth / common mistake) -> split screen yellowed lens | crystal clear lens.
    python3 render.py stills [scene,scene] [fracs]      -> stills/*.jpg
    python3 render.py render                            -> foggy-headlights.mp4 (+ work/)
Sources checked: Chemical Guys "Does toothpaste clean headlights" (mild abrasive, re-oxidizes in ~2-4 weeks without UV
protection; tape off surrounding paint; apply UV protection the same session), Empire Abrasives restoration guide
(UV breaks down the polycarbonate's coating; painter's tape around the lens; wet sand with progressively finer grits,
keep the surface wet; plastic polish; UV sealant, reapply). Kit labels: gloves + ventilation for the sealant, follow cure time.
"""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from lib.engine import *
from lib.music_upbeat import make_track
from lib.music_styles import pick_style

SLUG = "2026-11-17-foggy-headlights"
NAME = "foggy-headlights"
PILL_Y = 1515

def chaikin(pts, it=4):
    for _ in range(it):
        out = []
        for i in range(len(pts)):
            (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
            out += [(0.75 * x0 + 0.25 * x1, 0.75 * y0 + 0.25 * y1), (0.25 * x0 + 0.75 * x1, 0.25 * y0 + 0.75 * y1)]
        pts = out
    return pts

LENS = chaikin([(95, 1060), (250, 930), (620, 870), (930, 880), (1010, 990), (975, 1230), (820, 1390),
                (420, 1430), (170, 1380), (80, 1230)])
LCX = sum(p[0] for p in LENS) / len(LENS); LCY = sum(p[1] for p in LENS) / len(LENS)
TAPE = [(LCX + (x - LCX) * 1.075, LCY + (y - LCY) * 1.11) for x, y in LENS]
REFL = [(330, 1150, 165), (690, 1120, 150)]       # reflector bowls (x, y, r)

def lmask(draw_fn, blur=2):
    m = Image.new("L", (W, H), 0); draw_fn(ImageDraw.Draw(m))
    m = m.filter(ImageFilter.GaussianBlur(blur)) if blur else m
    return np.array(m).astype(np.float32) / 255

def gblur(arr, r):
    return np.array(to_img(arr).convert("RGB").filter(ImageFilter.GaussianBlur(r))).astype(np.float32)

def make_bgs():
    rng = np.random.default_rng(1117)
    # ---- deep blue metallic paint, hood crease, black bumper trim ----
    g = np.clip(YF / H, 0, 1)
    paint = np.stack([22 + g * 18, 46 + g * 26, 96 + g * 40], -1)
    flake = (rng.random((H, W)).astype(np.float32) - 0.5) * 10
    paint += flake[..., None] + ((lowfreq(5, 70) - 0.5) * 22)[..., None]
    refl = np.exp(-(((XF * 0.35 - YF * 0.9) + 520) / 140) ** 2) * 70          # sky reflection band
    paint += refl[..., None] * np.array([0.8, 0.9, 1.0])
    crease = lmask(lambda d: d.line([(0, 780), (1080, 700)], fill=255, width=10), 6)
    paint = blend(paint, [(np.zeros_like(paint) + np.array([190, 210, 240]), crease * 0.7)])
    trim = lmask(lambda d: d.polygon([(0, 1560), (1080, 1520), (1080, 1920), (0, 1920)], fill=255), 2)
    trimc = np.zeros_like(paint) + np.array([26, 28, 32]) + ((lowfreq(7, 8) - 0.5) * 12)[..., None]
    paint = blend(paint, [(trimc, trim)])
    slats = lmask(lambda d: [d.line([(40, 1640 + k * 70), (1040, 1610 + k * 70)], fill=255, width=14) for k in range(4)], 2)
    paint = blend(paint, [(np.zeros_like(paint) + 60, slats * 0.8)])
    # ---- housing interior (clean) ----
    lm = lmask(lambda d: d.polygon(LENS, fill=255), 2)
    gap = lmask(lambda d: d.polygon(TAPE, fill=255), 10) * (1 - lm)
    paint = blend(paint, [(np.zeros_like(paint) + 8, gap * 0.55)])
    inner = np.stack([46 + g * 30, 50 + g * 30, 58 + g * 30], -1)
    for cx, cy, r in REFL:
        R = np.sqrt((XF - cx) ** 2 + (YF - cy) ** 2)
        m = lmask(lambda d: d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255), 2)
        chrome = 110 + 120 * np.clip(R / r, 0, 1) + 26 * np.cos(R / r * 9) + 30 * np.cos(np.arctan2(YF - cy, XF - cx) * 2)
        chrome = np.stack([chrome * 0.95, chrome * 0.98, chrome * 1.03], -1)
        inner = blend(inner, [(chrome, m)])
        pr = int(r * 0.42)                                   # projector lens
        inner = blend(inner, [(np.zeros_like(inner) + np.array([16, 20, 28]), lmask(lambda d: d.ellipse([cx - pr, cy - pr, cx + pr, cy + pr], fill=255), 2))])
        inner = blend(inner, [(np.zeros_like(inner) + 245, lmask(lambda d: d.ellipse([cx - pr * 0.55, cy - pr * 0.6, cx - pr * 0.1, cy - pr * 0.2], fill=255), 4) * 0.85)])
    drl_pts = [(150, 1335), (380, 1375), (650, 1355), (860, 1290), (950, 1200)]
    glow = lmask(lambda d: d.line(drl_pts, fill=255, width=40, joint="curve"), 16)
    drl = lmask(lambda d: d.line(drl_pts, fill=255, width=18, joint="curve"), 2)
    inner = blend(inner, [(np.zeros_like(inner) + np.array([200, 225, 255]), glow * 0.7), (np.zeros_like(inner) + 252, drl)])
    # ---- lens states ----
    gloss = (lmask(lambda d: d.line([(170, 1010), (420, 925), (760, 895), (940, 915)], fill=255, width=26, joint="curve"), 6) * 0.75
             + np.clip(np.exp(-(((XF * 0.6 + YF * 0.8) - 1330) / 90) ** 2), 0, 1) * 0.22)
    CLEAN_IN = blend(inner, [(np.zeros_like(inner) + 255, gloss)])
    POL_IN = blend(gblur(inner, 1.5) * 0.92 + 14, [(np.zeros_like(inner) + 255, gloss * 0.25)])
    crazing = np.clip((lowfreq(21, 6) - 0.45) * 2.5, 0, 1)
    speck = (rng.random((H, W)).astype(np.float32) > 0.985).astype(np.float32)
    speck = np.array(Image.fromarray((speck * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255
    fog = gblur(inner, 14)
    yel = np.array([214, 178, 92], np.float32)
    DIRTY_IN = fog * 0.42 + yel * 0.5 + 18
    DIRTY_IN = blend(DIRTY_IN, [(np.zeros_like(inner) + np.array([236, 214, 150]), crazing * 0.35),
                                (np.zeros_like(inner) + np.array([120, 96, 50]), speck * 0.6),
                                (np.zeros_like(inner) + np.array([170, 140, 70]), np.clip((lowfreq(23, 40) - 0.5) * 1.6, 0, 1) * 0.5)])
    SAND_IN = gblur(inner, 18) * 0.3 + np.array([228, 228, 224], np.float32) * 0.66 + (rng.random((H, W, 1)).astype(np.float32) - 0.5) * 10
    rim = lmask(lambda d: d.line(LENS + LENS[:1], fill=255, width=6), 1.5)
    def comp(interior):
        return blend(paint, [(interior, lm), (np.zeros_like(paint) + 20, rim * 0.8)])
    return comp(DIRTY_IN), comp(SAND_IN), comp(POL_IN), comp(CLEAN_IN), lm

DIRTY, SANDED, POLISHED, CLEAN, LM = make_bgs()

def fb(arr): return to_img(arr)
def layer(): return Image.new("RGBA", (W, H), (0, 0, 0, 0))

def tape(img, p=1.0):
    if p <= 0: return
    n = int(len(TAPE) * p)
    if n < 2: return
    lay = layer(); d = ImageDraw.Draw(lay)
    pts = TAPE[:n] + (TAPE[:1] if p >= 1 else [])
    d.line(pts, fill=(52, 120, 210, 255), width=48, joint="curve")
    d.line(pts, fill=(90, 155, 235, 255), width=30, joint="curve")
    img.alpha_composite(lay)

def drops(img, t, n=40, seed=0):
    d = ImageDraw.Draw(img); rng = random.Random(seed)
    for _ in range(n):
        x, y = rng.uniform(140, 960), rng.uniform(920, 1390)
        if LM[int(y), int(x)] < 0.5: continue
        r = rng.uniform(5, 12) * (0.85 + 0.15 * math.sin(t * 6 + x))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(200, 225, 245, 150), outline=(255, 255, 255, 200), width=2)

def sand_block(img, x, y, ang=0):
    lay = Image.new("RGBA", (420, 420), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    rrect(d, [70, 150, 350, 290], 26, fill=(255, 196, 40), outline=INK, width=8)
    rrect(d, [70, 262, 350, 300], 10, fill=(70, 74, 82), outline=INK, width=6)
    d.chord([130, 70, 290, 230], 180, 360, fill=ACCENT, outline=INK, width=8)
    img.alpha_composite(lay.rotate(ang, resample=Image.BICUBIC), (int(x - 210), int(y - 280)))

def applicator(img, x, y, ang=0):
    lay = Image.new("RGBA", (360, 360), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    rrect(d, [80, 140, 280, 240], 24, fill=(245, 248, 250), outline=INK, width=8)
    rrect(d, [80, 205, 280, 240], 12, fill=(150, 205, 245), outline=INK, width=6)
    img.alpha_composite(lay.rotate(ang, resample=Image.BICUBIC), (int(x - 180), int(y - 220)))

def zigzag(rows, x0=180, x1=900, y0=960, y1=1370):
    pts = []
    for i in range(rows):
        y = y0 + (y1 - y0) * i / (rows - 1)
        pts += [(x0, y), (x1, y)] if i % 2 == 0 else [(x1, y), (x0, y)]
    return pts

# ---------- scenes ----------
TOTAL = 3
HOOK = make_hook(DIRTY, CLEAN, [("TOOTHPASTE", 150, YELLOW), ("WON'T LAST", 160, YELLOW)],
                 "THE REAL FIX: 3 STEPS", mark_xy=(290, 1160), check_xy=(840, 1020), split_to=0.5, labels=True)
HOOK_D = 2.4

SAFETY = make_safety(lambda t: fb(DIRTY), [
    ("ok", "Gloves + fresh air for the UV sealant"),
    ("no", "Don't sand before taping off the paint"),
], title="Safety first", label="BEFORE YOU START")

SAND_PATH = zigzag(6)
C1 = make_card(1, "Tape, then wet sand", "Fine grit. Keep the lens wet.", TOTAL)
def x_sand(t, D):
    t0 = 0.3
    p = ease_io(seg(t, t0, D - 0.3)) * (len(SAND_PATH) - 1)
    m = trail_mask(SAND_PATH, p, radius=105, blur=14) * LM if t > t0 else 0
    base = fb(blend(DIRTY, [(SANDED, m)]))
    drops(base, t, 46, seed=3)
    tape(base, ease(seg(t, 0.0, 0.35)))
    if t > t0 - 0.05:
        x, y = path_point(SAND_PATH, p)
        sand_block(base, x + math.sin(t * 34) * 10, y, ang=math.sin(t * 34) * 4)
    pill(base, W // 2, PILL_Y, "KEEP IT WET", F("Bold", 46), ACC2, INK, ease(seg(t, 0.3, 0.6)))
    return base

POL_PATH = [(200 + 680 * k / 60 + math.cos(k * 0.55) * 95, 1130 + math.sin(k * 0.55) * 170 + 40 * math.sin(k * 0.11)) for k in range(61)]
C2 = make_card(2, "Polish it clear", "Plastic polish + a clean microfiber.", TOTAL)
def x_polish(t, D):
    t0 = 0.2
    p = ease_io(seg(t, t0, D - 0.35)) * (len(POL_PATH) - 1)
    m = trail_mask(POL_PATH, p, radius=150, blur=22) * LM if t > t0 else 0
    base = fb(blend(SANDED, [(POLISHED, m)]))
    tape(base, 1.0)
    if t > t0 - 0.05 and t < D - 0.2:
        x, y = path_point(POL_PATH, p)
        towel(base, x, y, ang=math.sin(t * 8) * 10, col=(255, 196, 40), stripe=(255, 226, 140))
    pill(base, W // 2, PILL_Y, "SMALL CIRCLES", F("Bold", 46), ACC2, INK, ease(seg(t, 0.25, 0.55)))
    return base

SEAL_PATH = zigzag(5, 170, 920, 950, 1370)
C3 = make_card(3, "Seal with UV coat", "This is what stops re-yellowing.", TOTAL)
def x_seal(t, D):
    t0 = 0.2
    p = ease_io(seg(t, t0, D - 0.6)) * (len(SEAL_PATH) - 1)
    m = trail_mask(SEAL_PATH, p, radius=105, blur=16) * LM if t > t0 else 0
    base = fb(blend(POLISHED, [(CLEAN, m)]))
    if t < D - 0.55:
        x, y = path_point(SEAL_PATH, p)
        applicator(base, x, y, ang=-8)
    else:
        sparkles(base, t, D - 0.55, 1.0, [(260, 1000), (620, 930), (880, 1010), (430, 1300), (760, 1250)])
    pill(base, W // 2, PILL_Y, "THIN COAT, LET IT CURE", F("Bold", 46), ACC2, INK, ease(seg(t, 0.25, 0.55)))
    return base

SP = [(260, 1000), (620, 930), (880, 1010), (430, 1300), (760, 1250), (560, 1150), (900, 1150)]
_BA = make_ba(DIRTY, CLEAN, y_label=SAFE_TOP + 120, handle_y=1480, spark_pts=SP)
def BA(t, D): return _BA(t, D)
BA.impact_at = _BA.impact_at

_OUT = make_loop_outro(CLEAN, HOOK(0.0, HOOK_D), ask="Ever tried the toothpaste trick?")
def OUTRO(t, D): return _OUT(t, D)

SCENES = [
    ("01_hook", HOOK, HOOK_D),
    ("02_safety", SAFETY, 2.4),
    ("03_sand", with_card(C1, x_sand), 2.8),
    ("04_polish", with_card(C2, x_polish), 2.6),
    ("05_seal", with_card(C3, x_seal), 2.6),
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
