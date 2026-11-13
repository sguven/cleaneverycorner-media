"""2026-11-13 — Streak-free stainless steel appliances (home). Uses lib/engine.py + lib/music_upbeat.py (+ clean style rotation).
python3 tools/render_stainless_steel_streak_free.py stills|render WORKDIR [OUT_MP4]
"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.engine import *
from lib.music_upbeat import make_track
from lib.music_styles import pick_style

SLUG = "2026-11-13-stainless-steel-streak-free"
DX0, DX1, DY0, DY1 = 70, 1010, 120, 1880          # fridge door
ZY0, ZY1 = 780, 1690                              # grime zone (below the step card)

def upsample(a):
    return np.array(Image.fromarray(a.astype(np.float32), "F").resize((W, H), Image.BILINEAR))

def rect_mask(box, r=40, blur=2):
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rounded_rectangle(box, r, fill=255)
    return np.array(m.filter(ImageFilter.GaussianBlur(blur))).astype(np.float32) / 255

def lmask(draw_fn, blur=2):
    m = Image.new("L", (W, H), 0); draw_fn(ImageDraw.Draw(m))
    return np.array(m.filter(ImageFilter.GaussianBlur(blur))).astype(np.float32) / 255 if blur else np.array(m).astype(np.float32) / 255

def make_bgs():
    rng = np.random.default_rng(13)
    k = (YF / H)[..., None]
    wall = np.array([228, 216, 198], np.float32) * (1 - k) + np.array([192, 178, 160], np.float32) * k
    door = rect_mask([DX0, DY0, DX1, DY1], 44, 2)
    # brushed steel: vertical grain (long streaks) + soft reflection bands
    long = upsample(rng.normal(0, 1, (H // 60 + 2, W)))
    fine = rng.normal(0, 1, W).astype(np.float32)[None, :]
    band = np.exp(-((XF * 0.55 + YF * 0.32 - 820) / 150) ** 2) * 30 + np.exp(-((XF * 0.55 + YF * 0.32 - 1260) / 90) ** 2) * 18
    lum = 186 + 12 * np.cos((XF - 540) / 700) - (YF / H) * 16 + band + long * 5 + fine * 3.5
    steel = lum[..., None] * np.array([0.985, 1.0, 1.03], np.float32)
    a = blend(wall, [(steel, door)])
    a -= (np.exp(-((YF - 1720) / 6) ** 2) * 90 * door)[..., None]      # door / drawer gap
    a += (np.exp(-((YF - 1732) / 4) ** 2) * 40 * door)[..., None]
    im = to_img(a); d = ImageDraw.Draw(im)
    d.rounded_rectangle([DX0, DY0, DX1, DY1], 44, outline=(90, 96, 104), width=6)
    # handle with stand-offs
    for y in (700, 1560):
        rrect(d, [912, y - 26, 950, y + 26], 8, fill=(120, 126, 134), outline=(70, 76, 84), width=3)
    for i, x in enumerate(range(940, 992)):
        v = 150 + 85 * math.sin((x - 940) / 52 * math.pi)
        d.line([(x, 640), (x, 1620)], fill=(int(v * 0.98), int(v), int(min(255, v * 1.03))))
    d.rounded_rectangle([940, 636, 991, 1624], 22, outline=(70, 76, 84), width=4)
    CLEANA = np.array(im.convert("RGB")).astype(np.float32)
    zone = door * np.clip((YF - ZY0) / 30, 0, 1) * np.clip((ZY1 - YF) / 30, 0, 1) * (XF < 905)

    # ---- fingerprints (oily ridged ovals) ----
    pr = np.zeros((H, W), np.float32)
    rr = random.Random(7)
    prints = [(250, 1150), (330, 1240), (200, 1300), (300, 1390), (420, 1180), (180, 1480), (380, 1520),
              (760, 1050), (830, 1130), (770, 1240), (850, 1330), (700, 1420), (820, 1520), (640, 1270)]
    for (px, py) in prints:
        ang = math.radians(rr.uniform(-30, 30)); s = rr.uniform(0.85, 1.15)
        y0, y1, x0, x1 = py - 75, py + 75, px - 75, px + 75
        u0 = XF[y0:y1, x0:x1] - px; v0 = YF[y0:y1, x0:x1] - py
        u = (u0 * math.cos(ang) + v0 * math.sin(ang)) / s; v = (-u0 * math.sin(ang) + v0 * math.cos(ang)) / s
        e = (u / 36) ** 2 + (v / 50) ** 2
        inside = np.clip((1 - e) / 0.25, 0, 1)
        r = np.sqrt(u ** 2 + (v * 0.72) ** 2) + np.sin(u * 0.08) * 2
        ridges = 0.5 + 0.5 * np.sin(r * 0.95)
        pr[y0:y1, x0:x1] = np.maximum(pr[y0:y1, x0:x1], inside * (0.35 + 0.65 * ridges))
    # ---- circular swirl streaks (from wiping in circles) ----
    def sw(dr):
        for cx, cy in [(330, 1330), (600, 1500), (690, 1110)]:
            for k_ in range(6):
                R = 70 + k_ * 26; a0 = rr.uniform(0, 360)
                dr.arc([cx - R, cy - R * 0.9, cx + R, cy + R * 0.9], a0, a0 + rr.uniform(160, 300), fill=255, width=12)
    swirl = lmask(sw, 5)
    # ---- water spots ----
    def sp(dr):
        for _ in range(55):
            x, y = rr.uniform(100, 880), rr.uniform(ZY0 + 20, ZY1 - 20); r = rr.uniform(5, 12)
            dr.ellipse([x - r, y - r, x + r, y + r], outline=255, width=3)
    spots = lmask(sp, 1)
    # ---- dried juice drip ----
    def dp(dr):
        dr.line([(560, 1080), (563, 1250), (568, 1400)], fill=255, width=16, joint="curve")
        dr.ellipse([552, 1385, 586, 1428], fill=255); dr.ellipse([548, 1060, 576, 1092], fill=255)
    drip = lmask(dp, 3)
    PRINT_C = np.array([96, 94, 90], np.float32)
    HAZE_C = np.array([238, 238, 234], np.float32)
    DRIP_C = np.array([176, 124, 66], np.float32)
    # ---- soap film (vertical milky streaks) ----
    film = upsample(np.random.default_rng(21).random((H // 90 + 2, W // 14 + 2)))
    film = np.array(Image.fromarray(film.astype(np.float32), "F").resize((W, H), Image.BILINEAR))
    film = np.array(Image.fromarray((np.clip((film - 0.35) / 0.4, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6))).astype(np.float32) / 255 * zone
    # ---- water droplets after the rinse ----
    def wd(dr):
        for _ in range(70):
            x, y = rr.uniform(100, 880), rr.uniform(ZY0 + 20, ZY1 - 30); r = rr.uniform(6, 15)
            dr.ellipse([x - r * 0.8, y - r, x + r * 0.8, y + r], fill=255)
    drops = lmask(wd, 1)
    DROP_C = np.array([150, 156, 164], np.float32)

    def state(dirt=0.0, film_k=0.0, wet=0.0):
        a = CLEANA
        if dirt > 0:
            a = blend(a, [(HAZE_C, swirl * zone * 0.6 * dirt), (PRINT_C, pr * zone * 0.78 * dirt),
                          (HAZE_C, spots * zone * 0.75 * dirt), (DRIP_C, drip * zone * 0.6 * dirt)])
        if film_k > 0:
            a = blend(a, [(HAZE_C, film * 0.3 * film_k)])
        if wet > 0:
            a = a * (1 - (zone * 0.06 * wet)[..., None])
            a = blend(a, [(DROP_C, drops * zone * 0.55 * wet)])
        return a
    return state, CLEANA, zone

STATE, CLEAN, ZONE = make_bgs()
DIRTY = STATE(1.0)
FILM = STATE(0.0, 1.0)
WET = STATE(0.0, 0.0, 1.0)

def fb(arr): return to_img(arr)
def layer(): return Image.new("RGBA", (W, H), (0, 0, 0, 0))
PILL_Y = 1540

# ---------- props ----------
def _lens_content():
    rng = np.random.default_rng(5); n = 380
    cols = np.cumsum(rng.random(n) < 0.18)                 # stripes of random width
    v = 150 + (cols % 3) * 22 + rng.normal(0, 6, n)
    a = np.tile(v[None, :], (n, 1))[..., None] * np.array([0.985, 1.0, 1.03])
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    m = Image.new("L", (n, n), 0); ImageDraw.Draw(m).ellipse([0, 0, n - 1, n - 1], fill=255)
    im.putalpha(m); return im
LENS = _lens_content()

def magnifier(img, cx, cy, s):
    R = int(190 * s)
    if R < 4: return
    l = LENS.resize((2 * R, 2 * R), Image.BICUBIC)
    img.alpha_composite(l, (int(cx - R), int(cy - R)))
    d = ImageDraw.Draw(img)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(255, 255, 255), width=max(1, int(10 * s)))
    d.ellipse([cx - R - 8 * s, cy - R - 8 * s, cx + R + 8 * s, cy + R + 8 * s], outline=INK, width=max(1, int(10 * s)))
    a = math.radians(45); x0, y0 = cx + math.cos(a) * (R + 10 * s), cy + math.sin(a) * (R + 10 * s)
    x1, y1 = cx + math.cos(a) * (R + 130 * s), cy + math.sin(a) * (R + 130 * s)
    d.line([(x0, y0), (x1, y1)], fill=INK, width=max(1, int(46 * s)))
    d.line([(x0, y0), (x1, y1)], fill=ACCENT, width=max(1, int(28 * s)))

def v_arrow(img, x, y0, y1, p):
    if p <= 0: return
    d = ImageDraw.Draw(img); ym = (y0 + y1) / 2; h = (y1 - y0) / 2 * p
    a, b = ym - h, ym + h
    d.line([(x, a + 30), (x, b - 30)], fill=INK, width=34); d.line([(x, a + 30), (x, b - 30)], fill=ACC2, width=20)
    for yy_, s_ in ((a, 1), (b, -1)):
        d.polygon([(x, yy_), (x - 48, yy_ + s_ * 62), (x + 48, yy_ + s_ * 62)], fill=ACC2, outline=INK, width=6)

def soap_bottle(img, x, y, ang=170):
    """dish-soap squeeze bottle, no label; nozzle ends up near (x, y + 175) when ang≈180."""
    lay = Image.new("RGBA", (420, 420), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    rrect(d, [140, 130, 280, 370], 44, fill=(120, 205, 160), outline=INK, width=8)
    rrect(d, [165, 180, 255, 300], 18, fill=(170, 230, 195))
    rrect(d, [170, 90, 250, 135], 10, fill=ACC2, outline=INK, width=7)
    d.polygon([(195, 92), (225, 92), (215, 40), (205, 40)], fill=ACC2, outline=INK, width=6)
    img.alpha_composite(lay.rotate(ang, resample=Image.BICUBIC), (int(x - 210), int(y - 210)))

def zig_v(xs, ya, yb):
    pts = []
    for i, x in enumerate(xs):
        a, b = (ya, yb) if i % 2 == 0 else (yb, ya)
        pts += [(x, a), (x, b)]
    return pts

PATH = zig_v([190, 400, 610, 800], ZY0 + 40, ZY1 - 40)

def wipe_scene(src, dst, col, stripe, t0, D, label):
    def f(t, D_):
        p = ease_io(seg(t, t0, D_ - 0.35)) * (len(PATH) - 1)
        m = trail_mask(PATH, p, radius=118, blur=16) if t > t0 else 0
        base = fb(blend(src, [(dst, m)]))
        if t0 - 0.1 < t < D_ - 0.2:
            x, y = path_point(PATH, p)
            towel(base, x, y + math.sin(t * 26) * 5, ang=90, col=col, stripe=stripe)
        pill(base, W // 2, PILL_Y, label(t) if callable(label) else label, F("Bold", 46), ACC2, INK, ease(seg(t, 0.4, 0.7)))
        return base
    return f

# ---------- scenes ----------
TOTAL = 5
HOOK = make_hook(DIRTY, CLEAN,
                 [("STREAKY FRIDGE?", 100, (255, 255, 255)), ("STOP", 170, YELLOW), ("WIPING IN CIRCLES", 120, YELLOW)],
                 "5 STEPS  ·  JUST DISH SOAP", mark_xy=(290, 1300), check_xy=(800, 1150), split_to=0.5)

SAFETY = make_safety(lambda t: fb(DIRTY), [
    ("ok", "Coated finish? Check the manual first"),
    ("no", "No steel wool, scouring pads or paper towels"),
    ("no", "No vinegar, ammonia or window spray"),
    ("never", "NEVER use bleach on stainless steel"),
], title="Before you start", label="SURFACE CHECK")

C1 = make_card(1, "Find the grain", "Look closely: those faint lines show which way to wipe.", TOTAL)
def x_grain(t, D):
    base = fb(DIRTY)
    magnifier(base, 430, 1180, back(seg(t, 0.25, 0.75)))
    v_arrow(base, 800, 900, 1460, ease(seg(t, 1.0, 1.6)))
    pill(base, W // 2, PILL_Y, "FOLLOW THE LINES", F("Bold", 48), ACC2, INK, ease(seg(t, 0.4, 0.7)))
    return base

C2 = make_card(2, "Soapy microfiber", "Warm water + a few drops of dish soap. Wring it out well.", TOTAL)
BX, BY = 540, 1300
SUDS = [(BX - 260 + i * 47, BY - 20 + (i % 3) * 18) for i in range(12)]
def x_soap(t, D):
    base = fb(DIRTY); dim(base, 40)
    pb = ease(seg(t, 0.0, 0.4))
    by = BY + (1 - pb) * 500
    basin_back(base, BX, by)
    fl = layer()
    if t > 1.2: bubbles(fl, t, 1.2, SUDS, rise=24, rmax=12, speed=1.3)
    base.alpha_composite(fl)
    # towel dips in, then lifts and wrings
    if t > 1.9:
        q = seg(t, 1.9, 2.5); up = ease(seg(t, 2.7, 3.2))
        ty = by - 260 + ease(q) * 260 - up * 330
        towel(base, BX + 40, ty, ang=6 * math.sin(t * 14) * up, col=(80, 150, 230), stripe=(150, 200, 245))
        if up > 0.3:
            d = ImageDraw.Draw(base)
            for i in range(3):
                fy = ty + 110 + ((t * 2.4 + i / 3) % 1) * (by - ty - 110)
                d.ellipse([BX + 10 + i * 30 - 9, fy - 13, BX + 10 + i * 30 + 9, fy + 13], fill=(150, 205, 245), outline=INK, width=3)
    basin_front(base, BX, by)
    # soap bottle pours drops
    pbt = ease(seg(t, 0.3, 0.7)) * (1 - ease(seg(t, 1.6, 1.9)))
    if pbt > 0:
        bx_, byy = 760 + (1 - pbt) * 400, 930
        soap_bottle(base, bx_, byy, ang=165)
        d = ImageDraw.Draw(base)
        if 0.7 < t < 1.7:
            nx, ny = bx_ - 40, byy + 170
            for i in range(3):
                ph = ((t - 0.7) * 2.2 + i / 3) % 1
                fy = ny + ph * (by - 40 - ny)
                d.ellipse([nx - 12, fy - 16, nx + 12, fy + 16], fill=(120, 205, 160), outline=INK, width=4)
    pill(base, W // 2, PILL_Y, "WARM WATER + DISH SOAP", F("Bold", 46), ACC2, INK, ease(seg(t, 0.4, 0.7)))
    return base

C3 = make_card(3, "Wipe with the grain", "Long strokes along the lines, never in circles.", TOTAL)
x_wipe = wipe_scene(DIRTY, FILM, (80, 150, 230), (150, 200, 245), 0.3, 4.4,
                    "WITH THE GRAIN, NOT CIRCLES")

C4 = make_card(4, "Rinse-wipe", "Plain water on a clean cloth lifts the soap film.", TOTAL)
x_rinse = wipe_scene(FILM, WET, (60, 175, 160), (150, 225, 210), 0.25, 3.6, "PLAIN WATER, CLEAN CLOTH")

C5 = make_card(5, "Dry and buff", "Dry microfiber, with the grain. No water spots, no streaks.", TOTAL)
_dry = wipe_scene(WET, CLEAN, (235, 110, 150), (250, 185, 205), 0.25, 4.2, "BUFF DRY, WITH THE GRAIN")
def x_dry(t, D):
    base = _dry(t, D)
    if t > D - 0.8:
        sparkles(base, t, D - 0.8, 0.9, [(200, 950), (640, 1060), (420, 1300), (760, 1380), (260, 1500), (560, 1620)])
    return base

SP = [(220, 1000), (760, 960), (480, 1200), (300, 1420), (860, 1380), (640, 1100), (140, 1260), (960, 1240)]
_BA = make_ba(DIRTY, CLEAN, y_label=900, handle_y=1250, spark_pts=SP)
def BA(t, D): return _BA(t, D)
BA.impact_at = _BA.impact_at
_OUT = make_outro(CLEAN)
def OUTRO(t, D): return _OUT(t, D)
def HOOK_F(t, D): return HOOK(t, D)
HOOK_F.headline_until = HOOK.headline_until

SCENES = [
    ("01_hook", HOOK_F, 3.3),
    ("02_safety", SAFETY, 4.6),
    ("03_grain", with_card(C1, x_grain), 3.6),
    ("04_soap", with_card(C2, x_soap), 4.0),
    ("05_wipe", with_card(C3, x_wipe), 4.4),
    ("06_rinse", with_card(C4, x_rinse), 3.6),
    ("07_dry", with_card(C5, x_dry), 4.2),
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
