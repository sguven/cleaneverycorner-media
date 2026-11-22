"""2026-11-22 — Clean-as-you-cook Thanksgiving checklist (home). lib/engine.py + lib/music_upbeat.py (clean style, upbeat=True).
Hook (number promise): "NO DISH PILE AFTER DINNER" -> split screen messy counter + dish pile | clean counter, pill "3 RULES".
    python3 render.py stills [scene,scene] [fracs]      -> stills/*.jpg
    python3 render.py render                            -> clean-as-you-cook.mp4 (+ work/)
Sources checked: USDA FSIS "Happy Thanksgiving!" (safest to not wash raw turkey; after raw turkey wash boards, utensils,
counters with soap + hot water, then sanitize - 1 Tbsp unscented liquid chlorine bleach per gallon of water; leftovers
in the fridge within 2 hours), FoodSafety.gov "Don't forget your Thanksgiving food safety steps" (consider not rinsing raw
turkey - 1 in 4 who rinse cross-contaminate; repeat cleaning after raw turkey), Fred Meyer "5 simple tips for cleaning as
you cook Thanksgiving dinner" (one side of the sink full of soapy water to wash knives/boards and wipe spills as you go;
a big garbage bowl on the counter = 2-3 trash trips instead of 10-12). Empty-dishwasher-first: common host advice.
"""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from lib.engine import *
from lib.music_upbeat import make_track
from lib.music_styles import pick_style

SLUG = "2026-11-22-clean-as-you-cook"
NAME = "clean-as-you-cook"
PILL_Y = 1515
PILE = (280, 1080)           # dish pile on the messy side

def lmask(draw_fn, blur=2):
    m = Image.new("L", (W, H), 0); draw_fn(ImageDraw.Draw(m))
    m = m.filter(ImageFilter.GaussianBlur(blur)) if blur else m
    return np.array(m).astype(np.float32) / 255

def solid(c): return np.zeros((H, W, 3), np.float32) + np.array(c, np.float32)

# ---------- countertop: dark slate quartz, top-down ----------
def make_bgs():
    rng = np.random.default_rng(1122)
    tone = 0.92 + 0.12 * lowfreq(3, 160) + 0.05 * lowfreq(4, 40)
    base = np.array([78, 88, 100], np.float32) * tone[..., None]
    fleck = (rng.random((H, W)) > 0.985).astype(np.float32)
    fleck = np.array(Image.fromarray((fleck * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))).astype(np.float32) / 255
    vein = np.clip(1 - np.abs(np.sin((XF * 0.55 + YF * 0.8 + lowfreq(8, 200) * 260) / 95)) * 14, 0, 1) * 0.35
    counter = blend(base, [(solid((150, 160, 172)), fleck * 0.55), (solid((140, 150, 162)), vein)])
    # backsplash edge at the very top (wall) for depth
    wall = lmask(lambda d: d.rectangle([0, 0, W, 150], fill=255), 0)
    counter = blend(counter, [(solid((226, 222, 212)), wall), (solid((40, 46, 54)), lmask(lambda d: d.rectangle([0, 150, W, 166], fill=255), 2))])
    sheen = np.exp(-((XF - YF * 0.45 - 330) / 150) ** 2) * 0.22 + np.exp(-((XF - YF * 0.45 + 160) / 70) ** 2) * 0.14
    sheen *= (YF > 166)
    clean = blend(counter * 1.03, [(solid((235, 242, 250)), np.clip(sheen, 0, 1))])

    # ---- the mess ----
    flour = np.clip((lowfreq(21, 70) - 0.55) * 3.2, 0, 1) * np.exp(-(((XF - 760) ** 2) / 330 ** 2 + ((YF - 1350) ** 2) / 420 ** 2))
    gravy_spots = [(560, 980, 70), (640, 1060, 34), (470, 1420, 55), (820, 900, 42), (720, 1500, 30), (900, 1180, 48), (210, 1560, 40), (90, 800, 46), (480, 760, 30), (150, 1450, 36)]
    gravy = lmask(lambda d: [d.ellipse([x - r, y - r * 0.8, x + r * 1.1, y + r], fill=255) for x, y, r in gravy_spots]
                  + [d.ellipse([x + r * 1.2 + k * 14, y - r * 0.3 - k * 9, x + r * 1.2 + k * 14 + 16, y - r * 0.3 - k * 9 + 16], fill=255)
                     for x, y, r in gravy_spots for k in range(3)], 3)
    gl = lmask(lambda d: [d.ellipse([x - r * 0.55, y - r * 0.55, x - r * 0.15, y - r * 0.25], fill=255) for x, y, r in gravy_spots], 3)
    cran = lmask(lambda d: [d.line([(x, y), (x + 40, y + ln)], fill=255, width=w) for x, y, ln, w in
                            [(860, 1300, 120, 22), (900, 1330, 70, 14), (380, 860, 90, 18)]]
                 + [d.ellipse([x - 26, y - 22, x + 30, y + 26], fill=255) for x, y in [(990, 1440), (430, 960), (690, 820)]], 2)
    crumbs = (rng.random((H, W)) > 0.9965).astype(np.float32) * np.clip(lowfreq(41, 120) * 1.6 - 0.3, 0, 1)
    crumbs = np.array(Image.fromarray((crumbs * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1))).astype(np.float32) / 255
    dirty = blend(counter * 0.95, [(solid((236, 232, 222)), flour * 0.75),
                                   (solid((122, 72, 30)), gravy * 0.95),
                                   (solid((196, 140, 80)), gl * 0.6),
                                   (solid((150, 20, 44)), cran * 0.95),
                                   (solid((210, 170, 110)), crumbs)])
    dirty_np = dirty.copy()
    im = to_img(dirty); d = ImageDraw.Draw(im)
    peels(d)
    dirty = np.array(im.convert("RGB")).astype(np.float32)
    # with the dish pile (hook + before/after)
    imp = im.copy(); dish_pile(imp, *PILE)
    dirty_pile = np.array(imp.convert("RGB")).astype(np.float32)
    imc = to_img(clean); neat_set(imc)
    clean_set = np.array(imc.convert("RGB")).astype(np.float32)
    return dirty, dirty_pile, clean, clean_set, dirty_np

PEELS = [(620, 1240, 0, (240, 130, 40)), (700, 1290, 40, (240, 130, 40)), (560, 1330, 120, (226, 196, 140)),
         (760, 1180, 200, (226, 196, 140)), (850, 1420, 300, (240, 130, 40)), (640, 1440, 80, (226, 196, 140))]
def peel(d, x, y, a, col, s=1.0):
    r = 46 * s
    d.arc([x - r, y - r * 0.6, x + r, y + r * 0.6], a, a + 200, fill=INK, width=int(22 * s))
    d.arc([x - r, y - r * 0.6, x + r, y + r * 0.6], a, a + 200, fill=col, width=int(14 * s))
def peels(d):
    for x, y, a, c in PEELS: peel(d, x, y, a, c)

def plate_top(d, cx, cy, r, food=True, rng=None):
    d.ellipse([cx - r + 8, cy - r + 14, cx + r + 8, cy + r + 14], fill=(20, 26, 32, 110))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(246, 246, 242), outline=INK, width=7)
    d.ellipse([cx - r * 0.68, cy - r * 0.68, cx + r * 0.68, cy + r * 0.68], outline=(214, 216, 214), width=5)
    if food:
        rng = rng or random.Random(int(cx * 7 + cy))
        for k in range(5):
            a = rng.uniform(0, 6.28); rr = rng.uniform(0, r * 0.45); s = rng.uniform(r * 0.10, r * 0.22)
            x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
            col = rng.choice([(140, 82, 34), (178, 30, 52), (230, 190, 120), (120, 72, 30)])
            d.ellipse([x - s, y - s * 0.8, x + s, y + s * 0.8], fill=col)

def dish_pile(img, cx, cy):
    d = ImageDraw.Draw(img)
    # stacked messy plates
    for i, (dx, dy, r) in enumerate([(-30, 40, 200), (20, 10, 190), (-10, -20, 180), (30, -40, 170)]):
        plate_top(d, cx + dx, cy + dy, r, rng=random.Random(i * 13 + 5))
    # bowl on top + spoon
    d.ellipse([cx - 160, cy + 150, cx + 40, cy + 350], fill=(70, 150, 230), outline=INK, width=7)
    d.ellipse([cx - 130, cy + 180, cx + 10, cy + 320], fill=(236, 214, 170))
    d.line([(cx + 10, cy + 260), (cx + 190, cy + 430)], fill=INK, width=22)
    d.line([(cx + 10, cy + 260), (cx + 190, cy + 430)], fill=(200, 206, 212), width=12)

def neat_set(img):
    d = ImageDraw.Draw(img)
    plate_top(d, 780, 1150, 150, food=False)
    d.rounded_rectangle([920, 1020, 960, 1280], 16, fill=(200, 206, 212), outline=INK, width=6)      # fork/knife
    d.rounded_rectangle([600, 1020, 640, 1280], 16, fill=(200, 206, 212), outline=INK, width=6)
    # folded tea towel
    d.rounded_rectangle([700, 1320, 960, 1430], 22, fill=(255, 196, 40), outline=INK, width=7)
    for k in range(2): d.line([(720, 1355 + k * 40), (940, 1355 + k * 40)], fill=(255, 226, 140), width=10)

DIRTY, DIRTYP, CLEAN, CLEANS, DIRTY_NP = make_bgs()
def fb(arr): return to_img(arr)

# ---------- scenes ----------
TOTAL = 3
HOOK = make_hook(DIRTYP, CLEANS, [("NO DISH PILE", 160, YELLOW), ("AFTER DINNER", 150, YELLOW)],
                 "3 RULES", mark_xy=(PILE[0], PILE[1] - 60), check_xy=(830, 960), split_to=0.5, labels=True)
HOOK_D = 2.2

SAFETY = make_safety(DIRTY, [
    ("ok", "Raw turkey touched it? Wash, then sanitize"),
    ("never", "Don't rinse the raw turkey"),
], title="Food safety first", label="BEFORE YOU START")

# step 1: empty dishwasher first -> load as you go (plates fly from the pile into the rack)
C1 = make_card(1, "Empty the dishwasher first", "Then load as you go.", TOTAL)
SLOTS = [250, 350, 450, 550, 650, 750, 850]
def rack(img, t, n_in, fly):
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = 110, 760, 970, 1400
    d.rounded_rectangle([x0 - 20, y0 - 20, x1 + 20, y1 + 20], 40, fill=(214, 222, 228), outline=INK, width=9)
    d.rounded_rectangle([x0 + 10, y0 + 10, x1 - 10, y1 - 10], 30, fill=(186, 198, 206))
    for x in range(x0 + 40, x1 - 20, 50): d.line([(x, y1 - 160), (x, y1 - 40)], fill=(150, 160, 170), width=6)
    d.line([(x0 + 20, y1 - 100), (x1 - 20, y1 - 100)], fill=(150, 160, 170), width=8)
    d.line([(x0 + 20, y1 - 40), (x1 - 20, y1 - 40)], fill=(150, 160, 170), width=8)
    def side_plate(x, y, a=255):
        d.ellipse([x - 26, y - 170, x + 26, y + 170], fill=(246, 246, 242), outline=INK, width=6)
        d.ellipse([x - 12, y - 120, x + 12, y + 120], outline=(214, 216, 214), width=4)
    for i in range(n_in): side_plate(SLOTS[i], y1 - 200)
    if fly is not None:
        i, q = fly
        sx, sy = -120, 1700; ex, ey = SLOTS[i], y1 - 200
        x = sx + (ex - sx) * ease(q); y = sy + (ey - sy) * ease(q) - math.sin(q * math.pi) * 320
        side_plate(x, y)
    for x in range(x0 + 40, x1 - 20, 100): d.line([(x, y1 - 150), (x, y1 - 50)], fill=(120, 130, 140), width=7)
def x_load(t, D):
    base = fb(DIRTY); dim(base, 90)
    t0, per = 0.25, 0.27
    k = (t - t0) / per
    n_in = int(clamp(k, 0, len(SLOTS))); fly = None
    if 0 <= k < len(SLOTS): fly = (int(k), k - int(k))
    rack(base, t, n_in, fly)
    if n_in == len(SLOTS) and t > D - 0.5:
        sparkles(base, t, D - 0.5, 1.0, [(300, 900), (600, 880), (850, 1000), (500, 1100)])
    pill(base, W // 2, PILL_Y, "NO SINK PILE-UP", F("Bold", 46), ACC2, INK, ease(seg(t, 0.3, 0.6)))
    return base

# step 2: one side of the sink = hot soapy water; wash the knife and board as you go
C2 = make_card(2, "Fill the sink: hot soapy water", "Wash knives + boards as you go.", TOTAL)
BOARD_SPOTS = [(-120, -40, 28), (40, 10, 22), (110, -60, 18), (-40, 50, 24), (160, 30, 20)]
def board(img, cx, cy, dirt):
    lay = Image.new("RGBA", (700, 420), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([30, 60, 620, 360], 40, fill=(214, 160, 100), outline=INK, width=8)
    d.ellipse([540, 180, 590, 230], fill=(150, 104, 60), outline=INK, width=5)
    for k in range(6): d.line([(60, 100 + k * 45), (590, 104 + k * 45)], fill=(196, 142, 86), width=4)
    if dirt > 0:
        for dx, dy, r in BOARD_SPOTS:
            d.ellipse([320 + dx - r, 210 + dy - r, 320 + dx + r, 210 + dy + r], fill=(122, 72, 30, int(255 * dirt)))
    img.alpha_composite(lay.rotate(-12, resample=Image.BICUBIC, expand=False), (int(cx - 350), int(cy - 210)))
def x_sink(t, D):
    base = fb(CLEAN); dim(base, 60)
    bx, by = W // 2, 1250
    basin_back(base, bx, by, water=(170, 214, 240), col=(190, 200, 210))
    p = ease_io(seg(t, 0.35, D - 0.35))
    board(base, bx - 40, by - 170 + 30 * math.sin(t * 3), 1 - p)
    if 0.3 < t < D - 0.3:
        sx = bx - 220 + 360 * (0.5 + 0.5 * math.sin(t * 9)); sy = by - 190 + 40 * math.cos(t * 9)
        sponge(base, sx, sy, ang=math.sin(t * 18) * 8)
    basin_front(base, bx, by, water=(170, 214, 240), col=(190, 200, 210))
    bubbles(base, t, 0.0, [(bx - 300 + 60 * i, by + 10 + (i % 3) * 20) for i in range(11)], rise=60, rmax=16, speed=1.6)
    wisps(base, t, [bx - 220, bx, bx + 220], by - 120, height=260, alpha=170)
    if t > D - 0.45: sparkles(base, t, D - 0.45, 1.0, [(bx - 160, by - 230), (bx + 120, by - 260), (bx, by - 150)])
    pill(base, W // 2, PILL_Y, "WASH IT, REUSE IT", F("Bold", 46), ACC2, INK, ease(seg(t, 0.3, 0.6)))
    return base

# step 3: trash bowl on the counter + wipe spills before they dry
C3 = make_card(3, "Trash bowl + wipe spills now", "Fewer trips. Spills don't dry on.", TOTAL)
BOWL = (250, 1350)
WIPE = [(1000, 860), (420, 900), (1000, 1020), (420, 1080), (1000, 1200), (420, 1260), (1000, 1380), (520, 1460)]
def x_wipe(t, D):
    tp = 0.9                                            # peels fly into the bowl, then the towel wipes
    p = ease_io(seg(t, tp, D - 0.35)) * (len(WIPE) - 1)
    m = trail_mask(WIPE, p, radius=120, blur=20) if t > tp else 0
    # counter without peels (they fly away) - DIRTY has peels baked in; cover them with a peel-free version
    base = fb(blend(DIRTY_NP, [(CLEAN, m)]))
    d = ImageDraw.Draw(base)
    # bowl
    bx, by = BOWL
    d.ellipse([bx - 170 + 10, by - 170 + 16, bx + 170 + 10, by + 170 + 16], fill=(20, 26, 32, 110))
    d.ellipse([bx - 170, by - 170, bx + 170, by + 170], fill=(240, 240, 236), outline=INK, width=8)
    d.ellipse([bx - 135, by - 135, bx + 135, by + 135], fill=(214, 218, 220))
    for i, (x, y, a, c) in enumerate(PEELS):
        q = ease(seg(t, 0.1 + i * 0.1, 0.45 + i * 0.1))
        tx, ty = bx - 60 + (i % 3) * 55, by - 50 + (i // 3) * 70
        px = x + (tx - x) * q; py = y + (ty - y) * q - math.sin(q * math.pi) * 180
        peel(d, px, py, a + q * 160, c, s=1.0 - 0.25 * q)
    if t > tp - 0.05 and t < D - 0.3:
        x, y = path_point(WIPE, p)
        towel(base, x, y, ang=math.sin(t * 10) * 8, col=(120, 190, 240), stripe=(190, 225, 250))
    if t > D - 0.35: sparkles(base, t, D - 0.35, 1.0, [(600, 950), (880, 1100), (700, 1300)])
    pill(base, W // 2, PILL_Y, "2-3 TRASH TRIPS, NOT 10", F("Bold", 46), ACC2, INK, ease(seg(t, 0.3, 0.6)))
    return base


SP = [(620, 900), (880, 1000), (700, 1300), (900, 1400), (560, 1120)]
BA = make_ba(DIRTYP, CLEANS, y_label=SAFE_TOP + 120, handle_y=1560 - 120, spark_pts=SP)

_OUT = make_loop_outro(CLEAN, HOOK(0.0, HOOK_D), ask="Do you clean as you cook?")
def OUTRO(t, D): return _OUT(t, D)

SCENES = [
    ("01_hook", HOOK, HOOK_D),
    ("02_safety", SAFETY, 2.0),
    ("03_load", with_card(C1, x_load), 2.4),
    ("04_sink", with_card(C2, x_sink), 2.4),
    ("05_wipe", with_card(C3, x_wipe), 2.8),
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
