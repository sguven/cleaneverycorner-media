"""2026-11-15 — Refresh your mattress (home). Uses lib/engine.py + lib/music_upbeat.py (+ clean style rotation).
python3 tools/render_mattress_refresh.py stills|render WORKDIR [OUT_MP4]
"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.engine import *
from lib.music_upbeat import make_track
from lib.music_styles import pick_style

SLUG = "2026-11-15-mattress-refresh"
MAT = (80, 520, 1000, 1990)                        # mattress top-down (bottom runs off-screen)
STAINS = [(320, 1200, 150, 110), (730, 1520, 130, 95)]   # sweat stains (cx, cy, rx, ry)
COFFEE = (690, 1030, 62)

def lmask(draw_fn, blur=2):
    m = Image.new("L", (W, H), 0); draw_fn(ImageDraw.Draw(m))
    return np.array(m.filter(ImageFilter.GaussianBlur(blur))).astype(np.float32) / 255 if blur else np.array(m).astype(np.float32) / 255

def make_bgs():
    rng = np.random.default_rng(15)
    grain = rng.normal(0, 1, (H, W)).astype(np.float32)
    # ---- wood floor ----
    plank = (XF // 180).astype(np.int32)
    tone = (plank * 37 % 7) / 7.0
    a = np.stack([168 + tone * 22, 120 + tone * 16, 82 + tone * 10], -1).astype(np.float32)
    a += ((lowfreq(3, 30) - 0.5) * 16 + grain * 3)[..., None]
    a = a * (1 - ((XF % 180) < 4)[..., None] * 0.35)
    # ---- mattress body ----
    body = lmask(lambda d: d.rounded_rectangle(MAT, 60, fill=255), 4)
    shadow = lmask(lambda d: d.rounded_rectangle((MAT[0] + 14, MAT[1] + 22, MAT[2] + 14, MAT[3] + 22), 60, fill=255), 22)
    a = a * (1 - shadow[..., None] * 0.45)
    mcol = np.array([212, 222, 234], np.float32) + (grain * 1.5 + (lowfreq(8, 90) - 0.5) * 6)[..., None]
    a = blend(a, [(mcol, body)])
    im = to_img(a); d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = MAT
    rrect(d, (x0 + 34, y0 + 34, x1 - 34, y1 - 34), 40, outline=(170, 184, 202), width=6)    # piping
    # quilted diamonds + tufts
    q = Image.new("RGBA", (W, H), (0, 0, 0, 0)); qd = ImageDraw.Draw(q)
    step = 150
    for k in range(-12, 14):
        c = k * step
        qd.line([(x0 + c, y0), (x0 + c + (y1 - y0), y1)], fill=(184, 196, 212, 255), width=4)
        qd.line([(x1 - c, y0), (x1 - c - (y1 - y0), y1)], fill=(184, 196, 212, 255), width=4)
    for i in range(-2, 12):
        for j in range(-2, 16):
            tx = x0 + 75 + i * step; ty = y0 + j * step
            if (i + j) % 2 == 0: continue
            qd.ellipse([tx - 9, ty - 9, tx + 9, ty + 9], fill=(172, 186, 204, 255))
    qm = Image.new("L", (W, H), 0); ImageDraw.Draw(qm).rounded_rectangle((x0 + 44, y0 + 44, x1 - 44, y1 - 44), 34, fill=255)
    q.putalpha(Image.fromarray(np.minimum(np.array(q.getchannel("A")), np.array(qm))))
    im.alpha_composite(q.filter(ImageFilter.GaussianBlur(1.2)))
    # side shading on the mattress edge
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle(MAT, 60, outline=(120, 130, 146, 120), width=26)
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    CLEANA = np.array(im.convert("RGB")).astype(np.float32)
    inside = lmask(lambda d: d.rounded_rectangle((x0 + 20, y0 + 20, x1 - 20, y1 - 20), 50, fill=255), 6)

    rr = random.Random(15)
    # ---- sweat stains (soft yellow blobs with darker tide-line) + coffee spot ----
    def st(dr):
        for cx, cy, rx, ry in STAINS:
            for _ in range(7):
                ox, oy = rr.uniform(-0.35, 0.35) * rx, rr.uniform(-0.35, 0.35) * ry
                s = rr.uniform(0.55, 0.85)
                dr.ellipse([cx + ox - rx * s, cy + oy - ry * s, cx + ox + rx * s, cy + oy + ry * s], fill=255)
    STN = lmask(st, 22)
    EDGE = np.clip(STN * (1 - STN) * 4, 0, 1)
    def cf(dr):
        cx, cy, r = COFFEE
        dr.ellipse([cx - r, cy - r * 0.85, cx + r, cy + r * 0.85], fill=255)
        dr.ellipse([cx + r * 0.6, cy + r * 0.4, cx + r * 1.1, cy + r * 0.85], fill=255)
    CFE = lmask(cf, 5)
    YEL = np.array([206, 182, 110], np.float32); YELD = np.array([176, 146, 80], np.float32)
    COF = np.array([150, 104, 66], np.float32)
    # ---- dust haze, speckles and hairs ----
    dust = (rng.random((H, W)) < 0.005).astype(np.float32)
    dust = np.array(Image.fromarray((dust * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(1))).astype(np.float32) / 255
    DUST = np.clip(dust * 1.6, 0, 1) * inside
    HAZE = lowfreq(17, 140) * 0.28 * inside
    def hairs(dr):
        for _ in range(26):
            x, y = rr.uniform(140, 940), rr.uniform(620, 1880); L = rr.uniform(30, 70); an = rr.uniform(0, math.pi)
            dr.arc([x - L, y - L * 0.4, x + L, y + L * 0.4], math.degrees(an), math.degrees(an) + 110, fill=255, width=3)
        for _ in range(60):
            x, y = rr.uniform(140, 940), rr.uniform(620, 1880); r = rr.uniform(3, 6)
            dr.ellipse([x - r, y - r, x + r, y + r], fill=255)
    HAIR = lmask(hairs, 0.6) * inside
    DUSTC = np.array([170, 168, 160], np.float32); HAIRC = np.array([90, 76, 64], np.float32)
    # ---- damp blot marks (after spot-treating) ----
    def dm(dr):
        for cx, cy, rx, ry in STAINS: dr.ellipse([cx - rx * 0.95, cy - ry * 0.95, cx + rx * 0.95, cy + ry * 0.95], fill=255)
        cx, cy, r = COFFEE; dr.ellipse([cx - r * 1.3, cy - r * 1.2, cx + r * 1.4, cy + r * 1.3], fill=255)
    DAMP = lmask(dm, 26)
    # ---- baking soda layer ----
    soda = (rng.random((H, W)) < 0.16).astype(np.float32)
    soda = np.array(Image.fromarray((soda * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.8))).astype(np.float32) / 255
    SODA = np.clip(soda * 0.85 + 0.25 + lowfreq(21, 50) * 0.3, 0, 1) * inside
    SODAC = np.array([252, 252, 250], np.float32)

    def state(dust_k=0.0, stain=0.0, damp=0.0, soda_k=0.0):
        a = CLEANA
        if stain > 0: a = blend(a, [(YEL, STN * 0.55 * stain), (YELD, EDGE * 0.45 * stain), (COF, CFE * 0.8 * stain)])
        if damp > 0: a = a * (1 - (DAMP * 0.05 * damp)[..., None])
        if dust_k > 0: a = blend(a, [(DUSTC, HAZE * dust_k), (DUSTC, DUST * 0.7 * dust_k), (HAIRC, HAIR * 0.85 * dust_k)])
        if soda_k > 0: a = blend(a, [(SODAC, SODA * 0.82 * soda_k)])
        return a
    return state, CLEANA

STATE, CLEAN = make_bgs()
DIRTY = STATE(1, 1)
VAC = STATE(0, 1)
BLOTTED = STATE(0, 0, 1)
SODA_ON = STATE(0, 0, 0, 1)
STAIN_ONLY = [STATE(0, 1), STATE(0, 0, 1)]

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

# ---------- props ----------
def _sheet():
    lay = layer(); d = ImageDraw.Draw(lay)
    x0, y0, x1, y1 = MAT
    rrect(d, (x0 - 24, y0 - 24, x1 + 24, y1 + 60), 50, fill=(160, 200, 232), outline=(90, 130, 170), width=6)
    for k in range(x0 + 40, x1, 90): d.line([(k, y0), (k, y1 + 40)], fill=(178, 214, 240), width=22)
    rrect(d, (x0 - 24, y0 - 24, x1 + 24, y0 + 220), 50, fill=(246, 248, 252), outline=(150, 170, 190), width=6)
    for px in (x0 + 60, (x0 + x1) // 2 + 20):
        rrect(d, (px, y0 + 40, px + 380, y0 + 260), 70, fill=(255, 255, 255), outline=(170, 186, 204), width=6)
    return lay
SHEET = _sheet()

def shaker(img, x, y, ang=-35):
    lay = Image.new("RGBA", (360, 360), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    rrect(d, [110, 120, 250, 330], 30, fill=(255, 255, 255), outline=INK, width=8)
    rrect(d, [126, 190, 234, 270], 12, fill=(255, 196, 40))
    rrect(d, [100, 70, 260, 128], 16, fill=ACCENT, outline=INK, width=8)
    for k in range(4): d.ellipse([132 + k * 28, 88, 144 + k * 28, 100], fill=INK)
    r = lay.rotate(ang + 180, resample=Image.BICUBIC, expand=False)       # lid points down
    img.alpha_composite(r, (int(x - 180), int(y - 180)))

def falling(img, x, y, t):
    d = ImageDraw.Draw(img); rng = random.Random(int(t * 30))
    for _ in range(40):
        f = rng.random(); px = x + rng.uniform(-40, 40) + f * 30; py = y + f * 220
        r = rng.uniform(2.5, 5.5); d.ellipse([px - r, py - r, px + r, py + r], fill=(255, 255, 255, int(255 * (1 - f * 0.6))))

# ---------- scenes ----------
TOTAL = 5
HOOK = make_hook(DIRTY, CLEAN,
                 [("WHEN DID YOU LAST", 96, (255, 255, 255)), ("CLEAN", 170, YELLOW), ("YOUR MATTRESS?", 116, YELLOW)],
                 "5 STEPS  ·  NO SOAKING", mark_xy=STAINS[0][:2], check_xy=(780, 1180), split_to=0.5)

SAFETY = make_safety(lambda t: fb(DIRTY), [
    ("ok", "Read the care tag, open a window"),
    ("ok", "Mild dish soap suds or enzyme cleaner"),
    ("no", "Don't soak it, especially memory foam"),
    ("never", "NEVER mix cleaners or use bleach"),
], title="Before you start", label="CARE TAG CHECK")

C1 = make_card(1, "Strip the bed", "Wash sheets, covers and pads per the care label.", TOTAL)
def x_strip(t, D):
    base = fb(DIRTY)
    p = ease_io(seg(t, 0.5, 2.0))
    sh = SHEET.rotate(-8 * p, resample=Image.BICUBIC, center=(MAT[2], MAT[3]))
    base.alpha_composite(sh, (int(p * 1150), int(p * 260)))
    if t > 2.1:
        d = ImageDraw.Draw(base)
        ring(d, STAINS[0][0], STAINS[0][1], 150, ease(seg(t, 2.1, 2.6)))
        ring(d, COFFEE[0], COFFEE[1], 100, ease(seg(t, 2.3, 2.8)))
    pill(base, W // 2, PILL_Y + 120, "WASH BEDDING PER LABEL", F("Bold", 46), ACC2, INK, ease(seg(t, 0.4, 0.7)))
    return base

C2 = make_card(2, "Vacuum it all", "Upholstery tool over the top, sides and seams.", TOTAL)
VPATH = zig_h([760, 940, 1120, 1300, 1480, 1660, 1840], 230, 850)
def _vac(img, x, y, t): vac_nozzle(img, x + math.sin(t * 22) * 6, y, wand_to=(1300, 2300))
x_vac = tool_scene(DIRTY, VAC, VPATH, 0.3, _vac, "UPHOLSTERY TOOL, SLOW PASSES", radius=120)

C3 = make_card(3, "Blot the stains", "Soap suds on a cloth, then a damp cloth. Don't rub.", TOTAL)
SPOTS = [(STAINS[0][0], STAINS[0][1], STAINS[0][2]), (COFFEE[0], COFFEE[1], 90), (STAINS[1][0], STAINS[1][1], STAINS[1][2])]
def x_blot(t, D):
    seq = [(0.3, 1.6), (1.6, 2.8), (2.8, 4.0)]
    m = np.zeros((H, W), np.float32)
    for (cx, cy, r), (a, b) in zip(SPOTS, seq):
        k = ease(seg(t, a + 0.2, b - 0.1))
        if k > 0: m = np.maximum(m, k * np.exp(-(((XF - cx) / (r * 1.5)) ** 2 + ((YF - cy) / (r * 1.4)) ** 2) ** 2))
    base = fb(blend(VAC, [(BLOTTED, np.clip(m * 1.2, 0, 1))]))
    for (cx, cy, r), (a, b) in zip(SPOTS, seq):
        if a <= t < b:
            dab = abs(math.sin((t - a) * 10))
            towel(base, cx + 20, cy - 10 - dab * 40, ang=-10, col=(80, 150, 230), stripe=(150, 200, 245))
    if t >= 3.95:
        d = ImageDraw.Draw(base); q = back(seg(t, 3.95, 4.3))
        for cx, cy, r in SPOTS: check_badge(d, cx + r * 0.8, cy - r * 0.8, int(36 * q))
    pill(base, W // 2, PILL_Y + 120, "BLOT, DON'T RUB", F("Bold", 46), ACC2, INK, ease(seg(t, 0.4, 0.7)))
    return base

C4 = make_card(4, "Sprinkle baking soda", "Thin, even layer. Let it sit a few hours.", TOTAL)
SPATH = zig_h([760, 1000, 1240, 1480, 1720, 1900], 220, 860)
def x_soda(t, D):
    T1 = 2.5
    p = ease_io(seg(t, 0.2, T1)) * (len(SPATH) - 1)
    m = trail_mask(SPATH, p, radius=150, blur=24) if t > 0.2 else 0
    base = fb(blend(BLOTTED, [(SODA_ON, m)])) if t < T1 + 0.05 else fb(SODA_ON)
    if 0.1 < t < T1:
        x, y = path_point(SPATH, p)
        fl = layer(); falling(fl, x, y - 200, t); base.alpha_composite(fl)
        shaker(base, x - 30, y - 330, ang=-25 + math.sin(t * 24) * 8)
    if t > T1:
        dim(base, 60)
        q = back(seg(t, T1, T1 + 0.4))
        tm = layer(); timer(tm, 540, 1120, ease(seg(t, T1 + 0.3, D - 0.2)), "8", "hours", R=160)
        tm = tm.crop((350, 880, 730, 1320))
        if q > 0:
            tm = tm.resize((max(1, int(tm.width * q)), max(1, int(tm.height * q))), Image.BICUBIC)
            base.alpha_composite(tm, (int(540 - tm.width / 2), int(1100 - tm.height / 2)))
        pill(base, W // 2, PILL_Y + 20, "OVERNIGHT IS BEST, WINDOW OPEN", F("Bold", 44), ACC2, INK, ease(seg(t, T1 + 0.3, T1 + 0.6)))
    return base

C5 = make_card(5, "Vacuum and dry", "Vacuum it all up, air-dry, then add a protector.", TOTAL)
_vac2 = tool_scene(SODA_ON, CLEAN, VPATH, 0.25, _vac, "VACUUM UP EVERY GRAIN", radius=125, pill_p=(0.4, 0.7))
def x_vac2(t, D):
    base = _vac2(t, 3.3) if t < 3.3 else fb(CLEAN)
    if t >= 3.3:
        pill(base, W // 2, PILL_Y, "VACUUM UP EVERY GRAIN", F("Bold", 46), ACC2, INK, 1.0)
        sparkles(base, t, 3.3, 0.9, [(220, 900), (760, 840), (480, 1150), (300, 1400), (860, 1300), (640, 1700), (200, 1760)])
    return base

SP = [(220, 900), (760, 860), (480, 1180), (300, 1420), (860, 1380), (640, 1100), (160, 1260), (920, 1240)]
_BA = make_ba(DIRTY, CLEAN, y_label=960, handle_y=1480, spark_pts=SP)
def BA(t, D): return _BA(t, D)
BA.impact_at = _BA.impact_at
_OUT = make_outro(CLEAN)
def OUTRO(t, D): return _OUT(t, D)
def HOOK_F(t, D): return HOOK(t, D)
HOOK_F.headline_until = HOOK.headline_until

SCENES = [
    ("01_hook", HOOK_F, 3.3),
    ("02_safety", SAFETY, 4.6),
    ("03_strip", with_card(C1, x_strip), 3.6),
    ("04_vacuum", with_card(C2, x_vac), 4.0),
    ("05_blot", with_card(C3, x_blot), 4.6),
    ("06_soda", with_card(C4, x_soda), 4.6),
    ("07_vac2", with_card(C5, x_vac2), 4.4),
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
        fr = tuple(float(x) for x in sys.argv[4].split(",")) if len(sys.argv) > 4 else (0.05, 0.55, 0.95)
        print("\n".join(stills(SCENES, os.path.join(work, "stills"), fr, only)))
    else:
        print("total", build(SCENES, work, sys.argv[3], music, limit=0.5))
