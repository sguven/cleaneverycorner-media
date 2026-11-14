"""2026-11-14 — Sticky dashboard and cup holders (car). Uses lib/engine.py + lib/music_upbeat.py (+ clean style rotation).
python3 tools/render_sticky_dashboard_cup_holders.py stills|render WORKDIR [OUT_MP4]
"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.engine import *
from lib.music_upbeat import make_track
from lib.music_styles import pick_style

SLUG = "2026-11-14-sticky-dashboard-cup-holders"
CH = [(330, 1200), (750, 1200)]          # cup holder centres
RX, RY = 150, 118                         # cup holder opening radii (perspective)
BTN = [(300 + i * 160, 945) for i in range(4)]   # console buttons
LID = (190, 1440, 890, 1880)              # armrest / bin lid

def lmask(draw_fn, blur=2):
    m = Image.new("L", (W, H), 0); draw_fn(ImageDraw.Draw(m))
    return np.array(m.filter(ImageFilter.GaussianBlur(blur))).astype(np.float32) / 255 if blur else np.array(m).astype(np.float32) / 255

def make_bgs():
    rng = np.random.default_rng(14)
    grain = rng.normal(0, 1, (H, W)).astype(np.float32)
    # ---- cabin / seats either side ----
    k = (YF / H)[..., None]
    a = np.array([40, 42, 48], np.float32) * (1 - k) + np.array([22, 24, 28], np.float32) * k + (grain * 2)[..., None]
    # ---- dashboard (top) ----
    dash = np.clip((860 - YF) / 8, 0, 1)
    dcol = np.array([58, 62, 70], np.float32) - (YF / 860 * 14)[..., None] + (grain * 2.5)[..., None]
    a = blend(a, [(dcol, dash)])
    # ---- centre console (trapezoid, slight perspective) ----
    cons = lmask(lambda d: d.polygon([(140, 860), (940, 860), (1060, 1920), (20, 1920)], fill=255), 3)
    tex = (lowfreq(5, 8) - 0.5) * 8 + grain * 3.5
    ccol = np.array([74, 78, 86], np.float32) + (tex - (YF - 860) / 1060 * 16)[..., None]
    ccol += (np.exp(-((XF - 540) / 380) ** 2) * 10)[..., None]
    a = blend(a, [(ccol, cons)])
    im = to_img(a); d = ImageDraw.Draw(im)
    # screen (no UI brand, simple tiles)
    rrect(d, [190, 300, 890, 660], 34, fill=(16, 20, 26), outline=(110, 116, 124), width=6)
    for i, c in enumerate([(14, 150, 170), (70, 80, 92), (70, 80, 92), (255, 196, 40)]):
        x0 = 240 + (i % 2) * 310; y0 = 340 + (i // 2) * 150
        rrect(d, [x0, y0, x0 + 290, y0 + 130], 20, fill=tuple(int(v * 0.55) for v in c))
    # air vents
    for vx in (40, 920):
        rrect(d, [vx, 330, vx + 120, 630], 24, fill=(28, 30, 34), outline=(110, 116, 124), width=5)
        for y in range(360, 610, 34): d.line([(vx + 14, y), (vx + 106, y)], fill=(80, 86, 94), width=8)
    # trim strip between dash and console
    d.line([(140, 862), (940, 862)], fill=(150, 156, 164), width=8)
    # buttons
    for bx, by in BTN:
        rrect(d, [bx - 62, by - 40, bx + 62, by + 40], 20, fill=(48, 52, 58), outline=(26, 28, 32), width=5)
        rrect(d, [bx - 50, by - 30, bx + 50, by + 24], 14, fill=(62, 66, 74))
        d.ellipse([bx - 8, by - 10, bx + 8, by + 6], fill=(14, 150, 170))
    # cup holders: trim ring, dark wall, floor with rubber insert
    for cx, cy in CH:
        d.ellipse([cx - RX - 16, cy - RY - 14, cx + RX + 16, cy + RY + 14], fill=(120, 126, 134), outline=(30, 32, 36), width=5)
        d.ellipse([cx - RX, cy - RY, cx + RX, cy + RY], fill=(18, 19, 22))
        d.ellipse([cx - 112, cy - 30, cx + 112, cy + 92], fill=(34, 36, 40))
        d.ellipse([cx - 96, cy - 18, cx + 96, cy + 80], fill=(44, 46, 52))
    # lid
    rrect(d, LID, 46, fill=(64, 68, 76), outline=(28, 30, 34), width=7)
    rrect(d, [LID[0] + 24, LID[1] + 24, LID[2] - 24, LID[1] + 70], 20, fill=(84, 88, 96))
    im = im.filter(ImageFilter.GaussianBlur(0.6))
    # inner holder shading (soft)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    for cx, cy in CH: sd.ellipse([cx - RX + 6, cy - RY + 4, cx + RX - 6, cy - 10], fill=(0, 0, 0, 110))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    CLEANA = np.array(im.convert("RGB")).astype(np.float32)
    zone = np.clip((YF - 870) / 20, 0, 1) * cons

    rr = random.Random(9)
    # ---- sticky soda: puddles in the holders, drip, splatter, cup ring ----
    def sticky(dr):
        for cx, cy in CH:
            dr.ellipse([cx - 90, cy - 6, cx + 86, cy + 70], fill=255)
        dr.line([(250, 1312), (246, 1360), (252, 1405)], fill=255, width=22, joint="curve")
        dr.ellipse([232, 1390, 274, 1432], fill=255)
        for _ in range(16):
            x, y = rr.uniform(470, 620), rr.uniform(1080, 1360); r = rr.uniform(8, 20)
            dr.ellipse([x - r, y - r * 0.8, x + r, y + r * 0.8], fill=255)
        dr.ellipse([600, 1080, 680, 1130], fill=255)
    STK = lmask(sticky, 3)
    def ring_(dr):
        dr.ellipse([560, 1560, 740, 1700], outline=255, width=16)
        dr.ellipse([300, 1620, 440, 1730], outline=255, width=12)
    RING = lmask(ring_, 3)
    def gloss(dr):
        for cx, cy in CH: dr.arc([cx - 70, cy + 4, cx + 50, cy + 50], 200, 300, fill=255, width=8)
        for x, y in [(600, 1560), (310, 1625)]: dr.arc([x + 10, y + 6, x + 140, y + 110], 200, 260, fill=255, width=6)
    GLOSS = lmask(gloss, 2)
    SODA = np.array([112, 66, 30], np.float32)
    RINGC = np.array([128, 92, 56], np.float32)
    # ---- crumbs ----
    def crumbs(dr):
        for _ in range(150):
            x, y = rr.uniform(160, 920), rr.uniform(880, 1880); r = rr.uniform(3, 8)
            dr.polygon([(x - r, y), (x, y - r * 0.8), (x + r * 1.1, y + r * 0.2), (x + r * 0.2, y + r)], fill=255)
        for cx, cy in CH:
            for _ in range(22):
                x, y = cx + rr.uniform(-90, 90), cy + rr.uniform(10, 80); r = rr.uniform(4, 9)
                dr.ellipse([x - r, y - r, x + r, y + r], fill=255)
    CRUMB = lmask(crumbs, 1) * cons
    CRUMBC = np.array([206, 164, 96], np.float32)
    # ---- dust speckles + dull haze ----
    dust = (rng.random((H, W)) < 0.006).astype(np.float32)
    dust = np.array(Image.fromarray((dust * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(1))).astype(np.float32) / 255
    DUST = np.clip(dust * 1.6, 0, 1) * np.clip(cons + (YF < 860), 0, 1) * (1 - np.clip(((XF > 190) & (XF < 890) & (YF > 300) & (YF < 660)).astype(np.float32), 0, 1))
    HAZE = lowfreq(17, 120) * 0.22 * np.clip(cons + (YF < 860), 0, 1)
    DUSTC = np.array([168, 166, 160], np.float32)
    # ---- grime packed in seams ----
    def seams(dr):
        for bx, by in BTN: dr.rounded_rectangle([bx - 64, by - 42, bx + 64, by + 42], 22, outline=255, width=9)
        for cx, cy in CH: dr.ellipse([cx - RX - 18, cy - RY - 16, cx + RX + 18, cy + RY + 16], outline=255, width=10)
        dr.rounded_rectangle(LID, 46, outline=255, width=10)
    SEAM = lmask(seams, 2)
    SEAMC = np.array([150, 128, 96], np.float32)
    def wd(dr):
        for _ in range(60):
            x, y = rr.uniform(160, 920), rr.uniform(900, 1860); r = rr.uniform(5, 12)
            dr.ellipse([x - r * 0.8, y - r, x + r * 0.8, y + r], fill=255)
    DROPS = lmask(wd, 1) * cons
    DROPC = np.array([120, 126, 136], np.float32)

    def state(crumb=0.0, dustk=0.0, stick=0.0, seam=0.0, wet=0.0):
        a = CLEANA
        if dustk > 0: a = blend(a, [(DUSTC, HAZE * dustk), (DUSTC, DUST * 0.75 * dustk)])
        if seam > 0: a = blend(a, [(SEAMC, SEAM * 0.85 * seam)])
        if stick > 0:
            a = blend(a, [(SODA, STK * 0.82 * stick), (RINGC, RING * 0.7 * stick), (np.array([235, 205, 160], np.float32), GLOSS * 0.7 * stick)])
        if crumb > 0: a = blend(a, [(CRUMBC, CRUMB * 0.95 * crumb)])
        if wet > 0:
            a = a * (1 - (zone * 0.07 * wet)[..., None])
            a = blend(a, [(DROPC, DROPS * 0.6 * wet)])
        return a
    return state, CLEANA

STATE, CLEAN = make_bgs()
DIRTY = STATE(1, 1, 1, 1)
VAC = STATE(0, 0, 1, 1)
WIPED = STATE(0, 0, 0, 1, 1)      # damp after the towel, seams still dirty
WET = STATE(0, 0, 0, 0, 1)

def fb(arr): return to_img(arr)
def layer(): return Image.new("RGBA", (W, H), (0, 0, 0, 0))
PILL_Y = 1500

def zig_h(ys, xa, xb):
    pts = []
    for i, y in enumerate(ys):
        a, b = (xa, xb) if i % 2 == 0 else (xb, xa)
        pts += [(a, y), (b, y)]
    return pts

def tool_scene(src, dst, path, t0, draw_tool, label, radius=118, blur=16, pill_p=(0.4, 0.7)):
    def f(t, D):
        p = ease_io(seg(t, t0, D - 0.35)) * (len(path) - 1)
        m = trail_mask(path, p, radius=radius, blur=blur) if t > t0 else 0
        base = fb(blend(src, [(dst, m)]))
        if t0 - 0.1 < t < D - 0.2:
            x, y = path_point(path, p); draw_tool(base, x, y, t)
        pill(base, W // 2, PILL_Y, label, F("Bold", 46), ACC2, INK, ease(seg(t, *pill_p)))
        return base
    return f

def liners(img, p):
    """teal silicone liners pop into both holders."""
    if p <= 0.01: return
    d = ImageDraw.Draw(img)
    for cx, cy in CH:
        s = 0.6 + 0.4 * p
        rx, ry = 104 * s, 54 * s; yc = cy + 31
        d.ellipse([cx - rx - 8, yc - ry - 8, cx + rx + 8, yc + ry + 8], fill=(10, 110, 126), outline=INK, width=5)
        d.ellipse([cx - rx + 10, yc - ry + 8, cx + rx - 10, yc + ry - 8], fill=(20, 170, 190))
        for k in range(-2, 3): d.ellipse([cx + k * 34 * s - 6, yc - 6, cx + k * 34 * s + 6, yc + 6], fill=(10, 120, 136))

# ---------- scenes ----------
TOTAL = 5
HOOK = make_hook(DIRTY, CLEAN,
                 [("STICKY CUP HOLDERS?", 96, (255, 255, 255)), ("STOP", 170, YELLOW), ("SPRAYING YOUR DASH", 112, YELLOW)],
                 "5 STEPS  ·  10 MINUTES", mark_xy=CH[0], check_xy=(CH[1][0], CH[1][1] + 20), split_to=0.5)

SAFETY = make_safety(lambda t: fb(DIRTY), [
    ("ok", "Interior cleaner or warm soapy water, doors open"),
    ("no", "Never spray the screen, buttons or vents"),
    ("no", "Screen: soft dry cloth, no glass cleaner"),
    ("never", "NEVER use bleach or solvents on the dash"),
], title="Before you start", label="SURFACE CHECK")

C1 = make_card(1, "Empty and vacuum", "Clear the cup holders, then vacuum crumbs and dust.", TOTAL)
VPATH = zig_h([960, 1120, 1280, 1440, 1600, 1760], 200, 880)
def _crev(img, x, y, t): crevice_tool(img, x + math.sin(t * 20) * 6, y, wand_to=(1250, 2150))
x_vac = tool_scene(DIRTY, VAC, VPATH, 0.3, _crev, "CREVICE TOOL, TOP TO BOTTOM", radius=110)

C2 = make_card(2, "Soak the inserts", "Pop out rubber inserts. Warm soapy water, 10 minutes.", TOTAL)
BX, BY = 540, 1250
SUDS = [(BX - 260 + i * 47, BY - 20 + (i % 3) * 18) for i in range(12)]
def x_soak(t, D):
    base = fb(VAC); dim(base, 70)
    pb = ease(seg(t, 0.0, 0.4)); by = BY + (1 - pb) * 500
    basin_back(base, BX, by)
    d = ImageDraw.Draw(base)
    for i, ix in enumerate((BX - 150, BX + 150)):          # rubber inserts dropping in
        q = ease(seg(t, 0.5 + i * 0.25, 1.0 + i * 0.25))
        if q <= 0: continue
        iy = by - 380 * (1 - q) + 8
        d.ellipse([ix - 100, iy - 40, ix + 100, iy + 40], fill=(44, 46, 52), outline=INK, width=6)
        d.ellipse([ix - 70, iy - 24, ix + 70, iy + 24], fill=(70, 74, 82))
    fl = layer()
    if t > 1.2: bubbles(fl, t, 1.2, SUDS, rise=24, rmax=12, speed=1.3)
    base.alpha_composite(fl)
    basin_front(base, BX, by)
    if t > 1.4:
        q = back(seg(t, 1.4, 1.8))
        tm = layer(); timer(tm, 540, 960, ease(seg(t, 1.8, D - 0.3)), "10", "min", R=150)
        tm = tm.crop((370, 740, 710, 1130))
        if q > 0:
            tm = tm.resize((max(1, int(tm.width * q)), max(1, int(tm.height * q))), Image.BICUBIC)
            base.alpha_composite(tm, (int(540 - tm.width / 2), int(880 - tm.height / 2)))
    pill(base, W // 2, PILL_Y, "WARM WATER + DISH SOAP", F("Bold", 46), ACC2, INK, ease(seg(t, 0.4, 0.7)))
    return base

C3 = make_card(3, "Spray the towel", "Mist cleaner onto a microfiber, not onto the dash.", TOTAL)
WPATH = zig_h([1000, 1160, 1320, 1480, 1640, 1800], 200, 880)
def _towel(img, x, y, t): towel(img, x, y + math.sin(t * 26) * 5, ang=0, col=(80, 150, 230), stripe=(150, 200, 245))
_wipe = tool_scene(VAC, WIPED, WPATH, 1.6, _towel, "SPRAY THE TOWEL, NOT THE DASH", radius=120, pill_p=(0.2, 0.5))
def x_spray(t, D):
    if t >= 1.6: return _wipe(t, D)
    base = fb(VAC)
    tx, ty = 470, 1040
    towel(base, tx, ty, ang=-8, col=(80, 150, 230), stripe=(150, 200, 245))
    sq = 1.0 if (0.5 < t < 0.8 or 1.0 < t < 1.3) else 0.0
    nx, ny = spray_bottle(base, 880, 1080, s=0.85, squeeze=sq)
    if 0.5 < t < 1.45:
        ml = layer(); mist(ml, nx, ny, t, dirn=-1, strength=0.9); base.alpha_composite(ml)
    if t > 1.2:
        d = ImageDraw.Draw(base); q = back(seg(t, 1.2, 1.45)); check_badge(d, tx - 120, ty - 120, int(46 * q))
    pill(base, W // 2, PILL_Y, "SPRAY THE TOWEL, NOT THE DASH", F("Bold", 46), ACC2, INK, ease(seg(t, 0.2, 0.5)))
    return base

C4 = make_card(4, "Brush the seams", "Soft detail brush around buttons and cup-holder rims.", TOTAL)
def _ell(cx, cy, rx, ry, a0=200, n=16):
    return [(cx + rx * math.cos(math.radians(a0 + 360 * i / n)), cy + ry * math.sin(math.radians(a0 + 360 * i / n))) for i in range(n + 1)]
BPATH = [(220, 945), (870, 945)] + _ell(CH[0][0], CH[0][1], RX + 18, RY + 16) + _ell(CH[1][0], CH[1][1], RX + 18, RY + 16)[::-1] + \
        [(LID[2] - 40, LID[1]), (LID[0] + 40, LID[1])]
def x_brush(t, D):
    p = ease_io(seg(t, 0.3, D - 0.35)) * (len(BPATH) - 1)
    m = trail_mask(BPATH, p, radius=56, blur=8) if t > 0.3 else 0
    base = fb(blend(WIPED, [(WET, m)]))
    if 0.2 < t < D - 0.2:
        x, y = path_point(BPATH, p)
        detail_brush(base, x + math.sin(t * 30) * 5, y + math.cos(t * 30) * 4, ang=-30)
    pill(base, W // 2, PILL_Y, "SOFT BRISTLES, NO SCRATCHES", F("Bold", 46), ACC2, INK, ease(seg(t, 0.4, 0.7)))
    return base

C5 = make_card(5, "Dry and add liners", "Wipe dry, let inserts air-dry, then add silicone liners.", TOTAL)
DPATH = zig_h([1000, 1200, 1400, 1600, 1800], 200, 880)
def _dtowel(img, x, y, t): towel(img, x, y + math.sin(t * 26) * 5, ang=0, col=(235, 110, 150), stripe=(250, 185, 205))
_dry = tool_scene(WET, CLEAN, DPATH, 0.25, _dtowel, "DRY TOWEL, THEN LINERS", radius=130, pill_p=(0.4, 0.7))
def x_dry(t, D):
    base = _dry(t, 2.95) if t < 2.6 else fb(CLEAN)     # towel pass finishes right at 2.6 s
    if t >= 2.6:
        pill(base, W // 2, PILL_Y, "DRY TOWEL, THEN LINERS", F("Bold", 46), ACC2, INK, 1.0)
    liners(base, back(seg(t, 2.7, 3.1)))
    if t > 3.0: sparkles(base, t, 3.0, 0.9, [(200, 1000), (640, 1060), (420, 1300), (860, 1360), (260, 1680), (760, 1700)])
    return base

def CLEAN_LINERS():
    im = fb(CLEAN); liners(im, 1.0); return np.array(im.convert("RGB")).astype(np.float32)
CLEANL = CLEAN_LINERS()
SP = [(220, 1000), (760, 960), (480, 1200), (300, 1420), (860, 1380), (640, 1100), (140, 1260), (960, 1240)]
_BA = make_ba(DIRTY, CLEANL, y_label=1000, handle_y=1500, spark_pts=SP)
def BA(t, D): return _BA(t, D)
BA.impact_at = _BA.impact_at
_OUT = make_outro(CLEANL)
def OUTRO(t, D): return _OUT(t, D)
def HOOK_F(t, D): return HOOK(t, D)
HOOK_F.headline_until = HOOK.headline_until

SCENES = [
    ("01_hook", HOOK_F, 3.3),
    ("02_safety", SAFETY, 4.6),
    ("03_vacuum", with_card(C1, x_vac), 4.0),
    ("04_soak", with_card(C2, x_soak), 4.0),
    ("05_spray", with_card(C3, x_spray), 4.8),
    ("06_brush", with_card(C4, x_brush), 4.2),
    ("07_dry", with_card(C5, x_dry), 4.4),
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
