"""2026-11-10 — Streak-free inside windshield (car). Uses lib/engine.py + lib/music_upbeat.py (+ style rotation).
python3 tools/render_streak_free_windshield_inside.py stills|render WORKDIR [OUT_MP4]
"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.engine import *
from lib.music_upbeat import make_track
from lib.music_styles import pick_style

SLUG = "2026-11-10-streak-free-windshield-inside"

GTOP, GBOT = 290, 1330                       # windshield top / bottom edge
def glass_x(y):                              # left / right glass edge at row y
    k = (y - GTOP) / (GBOT - GTOP)
    return 190 - 170 * k, 890 + 170 * k
VPX, VPY = 560, 930                          # road vanishing point
CORNER = (175, 1215)                         # missed corner for step 5

def make_bgs():
    rng = np.random.default_rng(10)
    grain = rng.normal(0, 1, (H, W)).astype(np.float32)
    # ---- glass mask ----
    gm_im = Image.new("L", (W, H), 0)
    ImageDraw.Draw(gm_im).polygon([(190, GTOP), (890, GTOP), (1060, GBOT), (20, GBOT)], fill=255)
    gm = np.array(gm_im.filter(ImageFilter.GaussianBlur(2))).astype(np.float32) / 255
    # ---- outside scene ----
    k = np.clip((YF - GTOP) / (900 - GTOP), 0, 1)[..., None]
    sky = np.array([92, 160, 222], np.float32) * (1 - k) + np.array([196, 222, 238], np.float32) * k
    sun = np.exp(-(((XF - 870) / 150) ** 2 + ((YF - 560) / 150) ** 2))
    sky += (sun * 50)[..., None]
    cl = Image.new("L", (W, H), 0); cd = ImageDraw.Draw(cl); rr = random.Random(4)
    for _ in range(9):
        x, y = rr.uniform(100, 1000), rr.uniform(360, 760); s = rr.uniform(50, 110)
        for j in range(4): cd.ellipse([x + j * s * 0.6 - s, y - s * 0.45 - (j % 2) * 20, x + j * s * 0.6 + s, y + s * 0.4], fill=200)
    clouds = np.array(cl.filter(ImageFilter.GaussianBlur(18))).astype(np.float32) / 255
    out = blend(sky, [(np.full((H, W, 3), 250, np.float32), clouds * 0.85)])
    hy = 905 - 38 * np.sin(XF / 170) - 18 * np.sin(XF / 63 + 1)
    hills = (YF > hy).astype(np.float32)
    out = blend(out, [(np.array([118, 150, 140], np.float32) + (grain * 2)[..., None], hills)])
    tr = Image.new("L", (W, H), 0); td = ImageDraw.Draw(tr); rr = random.Random(9)
    for _ in range(46):
        x = rr.uniform(-20, 1100)
        if abs(x - VPX) < 90: continue
        s = rr.uniform(18, 44); y = 935 - rr.uniform(0, 10)
        td.ellipse([x - s, y - 2.4 * s, x + s, y + 4], fill=255)
    trees = np.array(tr.filter(ImageFilter.GaussianBlur(2))).astype(np.float32) / 255
    out = blend(out, [(np.array([52, 98, 66], np.float32) + (lowfreq(5, 20) * 24)[..., None], trees)])
    grass_k = np.clip((YF - 930) / 400, 0, 1)[..., None]
    grass = np.array([128, 176, 96], np.float32) * (1 - grass_k) + np.array([92, 140, 70], np.float32) * grass_k + (grain * 3)[..., None]
    out = np.where((YF > 930)[..., None], grass, out)
    rk = np.clip((YF - VPY) / (GBOT - VPY), 0, 1)
    half = 14 + rk * 620
    road = (np.abs(XF - VPX) < half) & (YF > VPY)
    asph = np.array([88, 92, 98], np.float32) + (grain * 3)[..., None]
    out = np.where(road[..., None], asph, out)
    edge = road & (np.abs(np.abs(XF - VPX) - half * 0.9) < (1 + rk * 9))
    out = np.where(edge[..., None], np.array([236, 236, 230], np.float32), out)
    dash_on = ((np.sqrt(np.clip(YF - VPY, 0, None)) * 1.6) % 6) < 3.2
    cen = road & (np.abs(XF - VPX) < (1 + rk * 9)) & dash_on
    out = np.where(cen[..., None], np.array([250, 200, 50], np.float32), out)
    # hood
    hood_y = 1270 + 30 * ((XF - 540) / 540) ** 2
    hood = np.clip((YF - hood_y) / 3, 0, 1)
    hcol = np.array([36, 64, 104], np.float32) + (np.clip((YF - 1260) / 80, 0, 1) * -14)[..., None]
    hcol += (np.exp(-(((XF - 700) / 220) ** 2 + ((YF - 1285) / 12) ** 2)) * 70)[..., None]
    out = blend(out, [(hcol, hood)])
    # ---- interior (everything that is not glass) ----
    head = np.array([206, 200, 190], np.float32) + (grain * 2 + (lowfreq(8, 90) - 0.5) * 10)[..., None]
    head -= (np.clip((YF - 120) / 170, 0, 1) * 30)[..., None]
    pk = np.clip(np.abs(XF - 540) / 540, 0, 1)
    pillar = np.array([72, 76, 82], np.float32) + (grain * 2)[..., None] + (pk * 14)[..., None]
    inter = np.where((YF < GTOP - 6)[..., None], head, pillar)
    dash_top = GBOT + 16 * ((XF - 540) / 540) ** 2
    dk = np.clip((YF - dash_top) / 500, 0, 1)
    dashc = np.array([58, 62, 68], np.float32) * (1 - dk)[..., None] + np.array([34, 37, 42], np.float32) * dk[..., None]
    dashc += (grain * 2.5 + (lowfreq(12, 14) - 0.5) * 8)[..., None]
    dashc += (np.clip(1 - np.abs(YF - dash_top - 6) / 6, 0, 1) * 40)[..., None]       # top highlight
    isdash = (YF > dash_top)
    inter = np.where(isdash[..., None], dashc, inter)
    vent = isdash & (np.abs(YF - dash_top - 34) < 4) & (np.abs(XF - 540) < 330) & ((XF.astype(int) // 22) % 2 == 0)
    inter = np.where(vent[..., None], np.array([20, 22, 26], np.float32), inter)
    ng = 1 - gm
    def fin(state):
        a = blend(state, [(inter, ng)])
        im = to_img(a); d = ImageDraw.Draw(im)
        # rear-view mirror
        d.rectangle([528, 220, 552, 300], fill=(40, 42, 46))
        rrect(d, [400, 292, 680, 386], 30, fill=(36, 38, 42), outline=(18, 20, 24), width=6)
        rrect(d, [416, 306, 664, 372], 20, fill=(150, 162, 176))
        d.line([(440, 320), (520, 320)], fill=(196, 206, 216), width=6)
        # gauge hood + steering wheel (driver side, left)
        d.chord([60, 1470, 560, 1760], 180, 360, fill=(30, 33, 38))
        d.arc([140, 1560, 280, 1700], 180, 360, fill=(14, 150, 170), width=8)
        d.arc([340, 1560, 480, 1700], 180, 360, fill=(14, 150, 170), width=8)
        d.ellipse([-80, 1500, 680, 2260], outline=(22, 24, 28), width=78)
        d.ellipse([-62, 1518, 662, 2242], outline=(52, 56, 62), width=8)
        d.polygon([(40, 1900), (560, 1900), (420, 1960), (180, 1960)], fill=(26, 28, 32))
        # centre screen
        rrect(d, [650, 1470, 960, 1680], 22, fill=(16, 22, 30), outline=(8, 10, 14), width=6)
        rrect(d, [676, 1496, 934, 1540], 10, fill=(14, 150, 170))
        for j in range(3): rrect(d, [676, 1560 + j * 36, 676 + 220 - j * 50, 1580 + j * 36], 8, fill=(70, 84, 98))
        return np.array(im.convert("RGB")).astype(np.float32)
    # ---- dirt states (glass only) ----
    haze_a = gm * np.clip(0.34 + 0.24 * lowfreq(21, 70) + 0.20 * np.clip((YF - 700) / 600, 0, 1), 0, 0.78)
    HAZE = np.array([222, 224, 222], np.float32) + (sun * 26)[..., None]
    sm = Image.new("L", (W, H), 0); sd = ImageDraw.Draw(sm); rr = random.Random(17)
    for _ in range(26):                                   # dry-wipe swirl smears
        x, y = rr.uniform(120, 960), rr.uniform(380, 1300); r = rr.uniform(60, 150)
        a0 = rr.uniform(0, 360); sd.arc([x - r, y - r * 0.6, x + r, y + r * 0.6], a0, a0 + rr.uniform(120, 260), fill=rr.randint(120, 200), width=rr.randint(8, 16))
    for _ in range(9):                                    # fingerprints
        x, y = rr.uniform(140, 900), rr.uniform(900, 1290)
        for j in range(5): sd.ellipse([x - 10 - j * 6, y - 14 - j * 8, x + 10 + j * 6, y + 14 + j * 8], outline=150, width=3)
    smear = np.array(sm.filter(ImageFilter.GaussianBlur(3))).astype(np.float32) / 255 * gm
    ds = Image.new("L", (W, H), 0); dd = ImageDraw.Draw(ds)
    for _ in range(700):
        x, y, s = rr.uniform(0, W), rr.uniform(GTOP, GBOT), rr.uniform(1.5, 4)
        dd.ellipse([x - s, y - s, x + s, y + s], fill=rr.randint(140, 255))
    dust = np.array(ds.filter(ImageFilter.GaussianBlur(0.8))).astype(np.float32) / 255 * gm
    WHITE = np.full((H, W, 3), 248, np.float32); DUSTC = np.array([200, 196, 186], np.float32)
    nodust = blend(out, [(HAZE, haze_a), (WHITE, smear * 0.55)])
    dirty = blend(nodust, [(DUSTC, dust * 0.9)])
    st = Image.new("L", (W, H), 0); s2 = ImageDraw.Draw(st); rr = random.Random(23)
    for _ in range(60):                                   # wet wipe streaks
        y = rr.uniform(340, 1310); x = rr.uniform(40, 900); L = rr.uniform(120, 420)
        s2.line([(x, y), (x + L, y + rr.uniform(-12, 12))], fill=rr.randint(110, 200), width=rr.randint(3, 7))
    streaks = np.array(st.filter(ImageFilter.GaussianBlur(1.6))).astype(np.float32) / 255 * gm
    wet = blend(out, [(HAZE, gm * 0.10), (WHITE, streaks * 0.6)])
    cm = np.exp(-(((XF - CORNER[0]) / 120) ** 2 + ((YF - CORNER[1]) / 90) ** 2)) * gm
    cs = Image.new("L", (W, H), 0); c2 = ImageDraw.Draw(cs)
    for j in range(7):
        y = CORNER[1] - 70 + j * 22; c2.line([(CORNER[0] - 130, y), (CORNER[0] + 110, y + 8)], fill=200, width=5)
    cstreak = np.array(cs.filter(ImageFilter.GaussianBlur(1.6))).astype(np.float32) / 255 * cm
    corner = blend(out, [(HAZE, cm * 0.45), (WHITE, cstreak * 0.8)])
    return fin(dirty), fin(nodust), fin(wet), fin(corner), fin(out), gm

DIRTY, NODUST, WET, CORNER_ST, CLEAN, GM = make_bgs()
TOPZONE = (YF < 720).astype(np.float32)

def frame_base(arr): return to_img(arr)

# ---------- props ----------
MF1 = dict(col=(80, 150, 230), stripe=(150, 200, 245))   # cleaning towel
MF2 = dict(col=(255, 196, 40), stripe=(255, 226, 140))    # dry buffing towel
def dash_towel(img, p=1.0):
    if p <= 0: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    y = 1336 + (1 - p) * 300
    d.polygon([(620, y + 6), (1000, y + 22), (1010, y + 110), (600, y + 96)], fill=(176, 182, 192, 255), outline=INK + (255,))
    d.line([(640, y + 40), (985, y + 54)], fill=(206, 210, 218, 255), width=8)
    img.alpha_composite(lay)

def zigzag(rows, xa, xb):
    pts = []
    for i, y in enumerate(rows):
        a, b = (xa, xb) if i % 2 == 0 else (xb, xa)
        pts += [(a, y), (b, y)]
    return pts

def verts(xs, ya, yb):
    pts = []
    for i, x in enumerate(xs):
        a, b = (yb, ya) if i % 2 == 0 else (ya, yb)
        pts += [(x, a), (x, b)]
    return pts

# ---------- scenes ----------
TOTAL = 5
HOOK = make_hook(DIRTY, CLEAN,
                 [("HAZY WINDSHIELD?", 90, (255, 255, 255)), ("THE 2-TOWEL", 140, YELLOW), ("TRICK", 160, YELLOW)],
                 "5 STEPS  ·  ZERO STREAKS", mark_xy=(250, 1080), check_xy=(800, 1020), split_to=0.5)

SAFETY = make_safety(lambda t: frame_base(DIRTY), [
    ("ok", "Park in the shade, engine off, doors open"),
    ("ok", "Ammonia-free auto glass cleaner (tint-safe)"),
    ("no", "No spraying near the dash or screens"),
    ("never", "NEVER mix cleaners together"),
], title="Before you start", label="SAFETY FIRST")

P1 = zigzag([760, 880, 1000, 1120, 1240], 110, 980)
C1 = make_card(1, "Dust it dry", "Wipe the glass with a dry microfiber towel to lift grit first.", TOTAL)
def x_dust(t, D):
    p = ease_io(seg(t, 0.25, D - 0.3)) * (len(P1) - 1)
    m = np.maximum(trail_mask(P1, p, radius=100, blur=16), TOPZONE * ease(seg(t, 0.25, D - 0.3))) * GM if t > 0.25 else 0
    base = frame_base(blend(DIRTY, [(NODUST, m)]))
    if 0.2 < t < D - 0.15:
        x, y = path_point(P1, p); towel(base, x, y + math.sin(t * 26) * 6, ang=math.sin(t * 9) * 8, **MF1)
    pill(base, W // 2, 1520, "DRY TOWEL FIRST", F("Bold", 48), ACC2, INK, ease(seg(t, 0.4, 0.7)))
    return base

C2 = make_card(2, "Spray the towel", "Ammonia-free glass cleaner on the towel, not the glass. Lay a towel on the dash.", TOTAL)
def x_spray(t, D):
    base = frame_base(NODUST)
    dash_towel(base, ease(seg(t, 0.1, 0.5)))
    q = back(seg(t, 0.2, 0.6))
    towel(base, 420, 930 + (1 - q) * 500, ang=-6, **MF1)
    bq = ease(seg(t, 0.35, 0.75))
    sq = 1.0 if 0.9 < t < 2.6 and (t * 4) % 1 < 0.5 else 0.0
    nx, ny = spray_bottle(base, 860 + (1 - bq) * 400, 990, s=0.9, squeeze=sq, label="GLASS")
    if 0.9 < t < 2.8:
        ml = Image.new("RGBA", (W, H), (0, 0, 0, 0)); mist(ml, nx, ny, t, dirn=-1, strength=0.9); base.alpha_composite(ml)
    d = ImageDraw.Draw(base)
    c = back(seg(t, 1.6, 2.0))
    if c > 0: check_badge(d, 600, 1040, int(48 * c))
    pill(base, W // 2, 1520, "SPRAY THE TOWEL, NOT THE GLASS", F("Bold", 42), ACC2, INK, ease(seg(t, 0.5, 0.8)))
    return base

LEFT = zigzag([760, 880, 1000, 1120, 1240], 90, 500) + verts([150, 300, 450], 740, 1270)
RIGHT = zigzag([760, 880, 1000, 1120, 1240], 580, 1000) + verts([640, 800, 960], 740, 1270)
HALF_L = (XF < 540).astype(np.float32); HALF_R = 1 - HALF_L
C3 = make_card(3, "Wipe in halves", "One half at a time: side to side, then top to bottom.", TOTAL)
def x_halves(t, D):
    mid = D / 2
    pl = ease_io(seg(t, 0.2, mid)) * (len(LEFT) - 1); pr = ease_io(seg(t, mid, D - 0.2)) * (len(RIGHT) - 1)
    m = np.zeros((H, W), np.float32)
    if t > 0.2: m = np.maximum(m, np.maximum(trail_mask(LEFT, pl, 95, 16), TOPZONE * seg(t, 0.2, mid)) * HALF_L)
    if t > mid: m = np.maximum(m, np.maximum(trail_mask(RIGHT, pr, 95, 16), TOPZONE * seg(t, mid, D - 0.2)) * HALF_R)
    base = frame_base(blend(NODUST, [(WET, m * GM)]))
    dash_towel(base)
    d = ImageDraw.Draw(base)
    for y in range(700, 1320, 44): d.line([(540, y), (540, y + 24)], fill=(255, 255, 255), width=6)
    if 0.15 < t < D - 0.1:
        x, y = path_point(LEFT, pl) if t < mid else path_point(RIGHT, pr)
        towel(base, x, y, ang=math.sin(t * 10) * 8, **MF1)
    pill(base, W // 2, 1520, "HALF 1  >  HALF 2", F("Bold", 48), ACC2, INK, ease(seg(t, 0.4, 0.7)))
    return base

P4 = zigzag([1240, 1120, 1000, 880, 760], 330, 1000)[:2] + zigzag([1120, 1000, 880, 760], 1000, 110)
C4 = make_card(4, "Buff it dry", "Grab a second clean, dry towel and buff right away.", TOTAL)
def x_buff(t, D):
    p = ease_io(seg(t, 0.25, D - 0.3)) * (len(P4) - 1)
    m = np.maximum(trail_mask(P4, p, radius=105, blur=16), TOPZONE * ease(seg(t, 0.25, D - 0.3))) * GM if t > 0.25 else 0
    base = frame_base(blend(WET, [(CORNER_ST, m)]))
    dash_towel(base)
    if 0.2 < t < D - 0.15:
        x, y = path_point(P4, p); towel(base, x, y + math.sin(t * 30) * 6, ang=math.sin(t * 12) * 10, **MF2)
    pill(base, W // 2, 1520, "2ND TOWEL = NO STREAKS", F("Bold", 48), ACC2, INK, ease(seg(t, 0.4, 0.7)))
    return base

C5 = make_card(5, "Check the corners", "Look from a low angle. Re-buff the bottom corners and the top edge.", TOTAL)
BAND_A = ((XF - 0.55 * YF)).astype(np.float32)
def x_check(t, D):
    r = ease(seg(t, 1.9, 2.9))
    disc = np.exp(-(((XF - CORNER[0]) / (60 + 200 * r)) ** 2 + ((YF - CORNER[1]) / (50 + 170 * r)) ** 2)) * r * 1.4
    base_arr = blend(CORNER_ST, [(CLEAN, np.clip(disc, 0, 1) * GM)])
    bx = -700 + 2000 * ease_io(seg(t, 0.15, 1.5))
    band = np.exp(-((BAND_A - bx) / 70) ** 2) * GM * 0.35 * (t < 1.6)
    base = frame_base(blend(base_arr, [(np.full((H, W, 3), 255, np.float32), band)]) if t < 1.6 else base_arr)
    d = ImageDraw.Draw(base)
    if t < 2.1: ring(d, CORNER[0], CORNER[1], 120, ease(seg(t, 1.0, 1.5)))
    if 1.8 < t < 3.0:
        a = (t - 1.8) * 9
        towel(base, CORNER[0] + 40 + math.cos(a) * 50, CORNER[1] + math.sin(a) * 34, ang=math.sin(a) * 12, **MF2)
    if t > 2.9: sparkles(base, t, 2.9, 0.8, [(CORNER[0] + 10, CORNER[1] - 30), (CORNER[0] + 140, CORNER[1] + 20), (CORNER[0] - 60, CORNER[1] + 40)])
    pill(base, W // 2, 1520, "CHECK FROM A LOW ANGLE", F("Bold", 48), ACC2, INK, ease(seg(t, 0.4, 0.7)))
    return base

SP_WS = [(220, 820), (760, 760), (480, 1000), (300, 1180), (860, 1120), (640, 880), (140, 980), (960, 940)]
_BA = make_ba(DIRTY, CLEAN, y_label=470, handle_y=1100, spark_pts=SP_WS)
def BA(t, D): return _BA(t, D)
BA.impact_at = _BA.impact_at
_OUT = make_outro(CLEAN)
def OUTRO(t, D): return _OUT(t, D)
def HOOK_F(t, D): return HOOK(t, D)
HOOK_F.headline_until = HOOK.headline_until

SCENES = [
    ("01_hook", HOOK_F, 3.3),
    ("02_safety", SAFETY, 4.4),
    ("03_dust", with_card(C1, x_dust), 3.5),
    ("04_spray", with_card(C2, x_spray), 3.6),
    ("05_halves", with_card(C3, x_halves), 4.2),
    ("06_buff", with_card(C4, x_buff), 3.6),
    ("07_check", with_card(C5, x_check), 3.8),
    ("08_ba", BA, 4.0),
    ("09_outro", OUTRO, 3.4),
]

def music(dur, cuts, impacts, path):
    style, seed = pick_style(SLUG)
    print("music style", style, seed)
    make_track(dur, cuts, impacts, path, style=style, seed=seed)

if __name__ == "__main__":
    mode, work = sys.argv[1], sys.argv[2]
    if mode == "stills":
        only = sys.argv[3].split(",") if len(sys.argv) > 3 else None
        print("\n".join(stills(SCENES, os.path.join(work, "stills"), (0.05, 0.55, 0.95), only)))
    else:
        print("total", build(SCENES, work, sys.argv[3], music, limit=0.5))
