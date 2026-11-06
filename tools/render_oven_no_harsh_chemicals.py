"""2026-11-06 — Clean your oven without harsh chemicals (home). Uses lib/engine.py + lib/music_upbeat.py.
python3 tools/render_oven_no_harsh_chemicals.py stills|render WORKDIR OUT_MP4
"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.engine import *
from lib.music_upbeat import make_track

# ---------- oven interior backgrounds ----------
BX0, BX1, BY0, BY1 = 190, 890, 600, 1480
def poly_mask(pts, blur=0):
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).polygon(pts, fill=255)
    if blur: m = m.filter(ImageFilter.GaussianBlur(blur))
    return np.array(m).astype(np.float32) / 255

M_BACK = poly_mask([(BX0, BY0), (BX1, BY0), (BX1, BY1), (BX0, BY1)])
M_CEIL = poly_mask([(0, 0), (W, 0), (BX1, BY0), (BX0, BY0)])
M_LEFT = poly_mask([(0, 0), (BX0, BY0), (BX0, BY1), (0, H)])
M_RIGHT = poly_mask([(W, 0), (BX1, BY0), (BX1, BY1), (W, H)])
M_FLOOR = poly_mask([(0, H), (BX0, BY1), (BX1, BY1), (W, H)])
ELEM_BAND = poly_mask([(150, 330), (930, 330), (900, 540), (180, 540)], blur=12)

def make_bgs():
    rng = np.random.default_rng(5)
    noise = rng.normal(0, 1, (H, W)).astype(np.float32)
    enamel = np.zeros((H, W, 3), np.float32)
    for m, c in [(M_BACK, (52, 60, 78)), (M_CEIL, (30, 36, 50)), (M_LEFT, (40, 47, 63)), (M_RIGHT, (36, 43, 58)), (M_FLOOR, (60, 67, 84))]:
        enamel += m[..., None] * np.array(c, np.float32)
    # warm oven-light glow + vertical shading
    glow = np.exp(-(((XF - 330) / 420) ** 2 + ((YF - 700) / 380) ** 2))
    enamel += glow[..., None] * np.array([38, 30, 14], np.float32)
    enamel *= (1.0 - 0.18 * np.abs(YF - 1000) / 1000)[..., None]
    # enamel speckles
    sp = (rng.random((H, W)) > 0.985).astype(np.float32)
    enamel += sp[..., None] * 34 + noise[..., None] * 2.5
    # edge lines between walls
    edges = Image.new("L", (W, H), 0); ed = ImageDraw.Draw(edges)
    for a, b in [((0, 0), (BX0, BY0)), ((W, 0), (BX1, BY0)), ((0, H), (BX0, BY1)), ((W, H), (BX1, BY1))]:
        ed.line([a, b], fill=255, width=4)
    ed.rectangle([BX0, BY0, BX1, BY1], outline=255, width=4)
    # rack runners on side walls
    for yb in (820, 1060, 1300):
        ed.line([(BX0, yb), (0, yb + (yb - 960) * 0.95 + 0)], fill=160, width=6)
        ed.line([(BX1, yb), (W, yb + (yb - 960) * 0.95)], fill=160, width=6)
    E = np.array(edges.filter(ImageFilter.GaussianBlur(1.5))).astype(np.float32) / 255
    enamel = enamel * (1 - E[..., None] * 0.45)

    clean = enamel.copy()
    sheen = np.clip(1 - np.abs((XF - YF * 0.45) - 300) / 260, 0, 1) ** 2 * M_BACK
    clean += sheen[..., None] * 22

    # grease: blotches heavier low and on floor, drips on back wall
    blot = lowfreq(9, 70); blot2 = lowfreq(21, 26)
    heavy = np.clip((blot * 0.7 + blot2 * 0.5 - 0.62 + (YF / H) * 0.32) * 3.2, 0, 1)
    heavy = np.maximum(heavy, M_FLOOR * np.clip((blot2 - 0.3) * 2.5, 0, 1))
    g = Image.fromarray((heavy * 255).astype(np.uint8)); gd = ImageDraw.Draw(g)
    r = random.Random(4)
    for _ in range(46):          # drips
        x = r.randrange(BX0 + 20, BX1 - 20); y0 = r.randrange(BY0 + 20, 1150); L = r.randrange(80, 300)
        gd.line([(x, y0), (x + r.randint(-6, 6), y0 + L)], fill=230, width=r.randint(6, 14))
        gd.ellipse([x - 12, y0 + L - 10, x + 12, y0 + L + 14], fill=230)
    for cx, cy, rr in [(270, 1250, 95), (230, 1150, 60), (330, 1330, 70), (200, 1700, 140), (520, 1650, 110), (860, 1720, 120), (700, 1240, 70)]:
        gd.ellipse([cx - rr, cy - rr * 0.8, cx + rr, cy + rr * 0.8], fill=255)
    for _ in range(500):         # burnt specks
        x = r.randrange(W); y = r.randrange(500, H); rr = r.randint(3, 10)
        gd.ellipse([x - rr, y - rr, x + rr, y + rr], fill=255)
    heavy = np.array(g.filter(ImageFilter.GaussianBlur(3))).astype(np.float32) / 255
    heavy *= (1 - ELEM_BAND * 0.7)
    grease_col = np.array([78, 52, 28], np.float32) * (1 - blot2[..., None] * 0.6) + np.array([20, 14, 10], np.float32) * blot2[..., None] * 0.6
    film = enamel * 0.72 + np.array([92, 70, 36], np.float32) * 0.28
    dirty = film * (1 - heavy[..., None] * 0.92) + grease_col * heavy[..., None] * 0.92 + noise[..., None] * 3

    # baking soda paste coat
    tex = lowfreq(33, 18)
    paste = np.array([236, 232, 220], np.float32) - tex[..., None] * 22 + noise[..., None] * 4
    paste *= (1.0 - 0.10 * np.abs(YF - 1000) / 1000)[..., None]
    geo = M_BACK * 1.0 + M_FLOOR * 0.95 + M_LEFT * 0.84 + M_RIGHT * 0.80 + M_CEIL * 0.72
    paste = paste * (geo * (1 - E * 0.3))[..., None] * 0.9 + dirty * 0.1
    # streaky residue left after first wipe
    st = lowfreq(41, 22)
    res = np.clip((st - 0.70) * 6, 0, 1) * (1 - ELEM_BAND)
    resid = clean * (1 - res[..., None] * 0.55) + paste * res[..., None] * 0.55
    return dirty, clean, paste, resid, res

DIRTY, CLEAN, PASTE, RESID, RES_M = make_bgs()
PM = np.clip(1 - ELEM_BAND * 1.2, 0, 1)          # paste everywhere except the heating element band

ELEM = None
def element(img):
    d = ImageDraw.Draw(img)
    pts = []
    for i in range(7):
        x = 250 + i * 97
        pts += [(x, 380 + (i % 2) * 120), (x + 48, 380 + (i % 2) * 120)]
    d.line(pts, fill=(18, 20, 24), width=26, joint="curve")
    d.line(pts, fill=(122, 124, 130), width=16, joint="curve")
    d.line([(p[0], p[1] - 4) for p in pts], fill=(170, 172, 178), width=4)

def oven(arr):
    im = to_img(arr); element(im); return im

RES_PTS = []
rr = random.Random(8)
while len(RES_PTS) < 70:
    x, y = rr.randrange(40, W - 40), rr.randrange(780, 1560)
    if RES_M[y, x] > 0.4: RES_PTS.append((x, y))

# ---------- props ----------
def rack(img, p, alpha=1.0):
    """oven rack sliding out toward the viewer (p 0 -> 1)."""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    s = 1 + 0.9 * ease_io(p); dy = 420 * ease_io(p)
    def P(x, y): return (W / 2 + (x - W / 2) * s, 960 + (y - 960) * s + dy)
    back_y, front_y = 1060, 1240
    bl, br, fl, fr = P(BX0 + 10, back_y), P(BX1 - 10, back_y), P(30, front_y), P(W - 30, front_y)
    col = (150, 152, 158, int(255 * alpha)); hi = (205, 208, 214, int(255 * alpha)); dk = (20, 24, 30, int(200 * alpha))
    for k in range(15):
        u = k / 14
        a = (bl[0] + (br[0] - bl[0]) * u, bl[1]); b = (fl[0] + (fr[0] - fl[0]) * u, fl[1])
        d.line([a, b], fill=dk, width=int(12 * s)); d.line([a, b], fill=col, width=int(7 * s))
    for v in (0.0, 0.5, 1.0):
        y = bl[1] + (fl[1] - bl[1]) * v
        xl = bl[0] + (fl[0] - bl[0]) * v; xr = br[0] + (fr[0] - br[0]) * v
        d.line([(xl, y), (xr, y)], fill=dk, width=int(16 * s)); d.line([(xl, y), (xr, y)], fill=hi, width=int(10 * s))
    img.alpha_composite(lay)

def bowl(img, cx, cy, fill_kind, p_pile, p_mix, t):
    d = ImageDraw.Draw(img)
    R = 250
    # contents
    if p_pile > 0:
        h = 150 * back(p_pile)
        if p_mix < 1:
            d.ellipse([cx - 200, cy - h, cx + 200, cy + h * 0.55], fill=(250, 250, 248))
            for i in range(14):
                a = i * 0.9; x = cx + math.cos(a) * 120 * (i % 3) / 2; y = cy - h * 0.4 + math.sin(a) * 30
                d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=(225, 228, 232))
        if p_mix > 0:
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
            ld.ellipse([cx - 215, cy - 70, cx + 215, cy + 60], fill=(232, 226, 210, int(255 * p_mix)))
            for k in range(3):
                rr_ = 60 + k * 45
                ld.arc([cx - rr_, cy - rr_ * 0.28 - 5, cx + rr_, cy + rr_ * 0.28 - 5], (t * 300 + k * 90) % 360, (t * 300 + k * 90 + 200) % 360, fill=(205, 198, 180, int(255 * p_mix)), width=6)
            img.alpha_composite(lay); d = ImageDraw.Draw(img)
    # bowl body
    d.chord([cx - R, cy - R + 20, cx + R, cy + R + 20], 0, 180, fill=(255, 255, 255), outline=INK, width=10)
    d.chord([cx - R + 40, cy + 40, cx + R - 40, cy + R - 10], 20, 160, fill=(225, 240, 244))
    d.line([(cx - R, cy + 20), (cx + R, cy + 20)], fill=ACCENT, width=22)
    d.line([(cx - R, cy + 20), (cx + R, cy + 20)], fill=INK, width=4)
    rrect(d, [cx - 80, cy + R + 10, cx + 80, cy + R + 40], 12, fill=INK)

def spoon(img, x, y, ang):
    lay = Image.new("RGBA", (500, 500), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    rrect(d, [235, 40, 265, 330], 14, fill=ACC2, outline=INK, width=6)
    d.ellipse([200, 300, 300, 440], fill=(230, 235, 240), outline=INK, width=8)
    img.alpha_composite(lay.rotate(ang, resample=Image.BICUBIC), (int(x - 250), int(y - 380)))

def drop(d, cx, cy, s, col=(120, 190, 240)):
    d.ellipse([cx - s, cy - s * 0.6, cx + s, cy + s * 1.2], fill=col)
    d.polygon([(cx - s * 0.75, cy), (cx, cy - s * 1.5), (cx + s * 0.75, cy)], fill=col)

def spatula(img, x, y, ang=0):
    lay = Image.new("RGBA", (520, 520), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    rrect(d, [240, 40, 280, 300], 16, fill=INK)
    rrect(d, [170, 280, 350, 470], 40, fill=(255, 120, 110), outline=INK, width=8)
    rrect(d, [190, 430, 330, 462], 12, fill=(236, 232, 220))
    img.alpha_composite(lay.rotate(ang, resample=Image.BICUBIC), (int(x - 260), int(y - 460)))

def moon(d, cx, cy, r):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ACC2)
    d.ellipse([cx - r + r * 0.55, cy - r - r * 0.25, cx + r + r * 0.55, cy + r - r * 0.25], fill=(40, 52, 72))

# ---------- scenes ----------
TOTAL = 6
def hook_extra(base, t, D, sx): element(base)
HOOK = make_hook(DIRTY, CLEAN,
                 [("CLEAN YOUR OVEN", 100, (255, 255, 255)), ("NO HARSH", 175, YELLOW), ("CHEMICALS", 175, YELLOW)],
                 "2 PANTRY ITEMS  ·  6 STEPS", mark_xy=(270, 1250), check_xy=(810, 1250))

SAFETY = make_safety(oven(DIRTY), [
    ("ok", "Oven OFF and fully cool"),
    ("ok", "Wear gloves"),
    ("no", "Keep paste off heating elements and gas ports"),
    ("no", "Don't scrub the door gasket"),
    ("never", "NEVER mix with oven cleaner or bleach"),
])

C1 = make_card(1, "Empty it", "Take out the racks and wash them separately", TOTAL)
def x_empty(t, D):
    base = oven(DIRTY)
    p = seg(t, 0.6, D - 0.5)
    if p < 1: rack(base, p, 1 - ease(seg(t, D - 1.2, D - 0.5)))
    return base

C2 = make_card(2, "Make a paste", "1/2 cup baking soda + about 3 Tbsp water", TOTAL)
def x_paste(t, D):
    base = oven(DIRTY); dim(base, 70)
    soft_disc(base, W // 2, 1250, 340, 150)
    d = ImageDraw.Draw(base)
    p_pile = seg(t, 0.4, 0.9)
    for k in range(3):                             # water drops
        tt = t - (1.1 + k * 0.35)
        if 0 <= tt < 0.45: drop(d, W // 2 - 60 + k * 60, 820 + tt / 0.45 * 300, 26)
    p_mix = ease(seg(t, 2.0, 2.9))
    bowl(base, W // 2, 1230, None, p_pile, p_mix, t)
    if t > 1.9:
        spoon(base, W // 2 + math.cos(t * 9) * 90, 1215 + math.sin(t * 9) * 22, math.cos(t * 9) * 18)
    fb = F("Bold", 40)
    pill(base, 300, 900, "1/2 cup soda", fb, ACC2, INK, ease(seg(t, 0.5, 0.8)))
    pill(base, 800, 900, "+ 3 Tbsp water", fb, BLUE, (255, 255, 255), ease(seg(t, 1.1, 1.4)))
    return base

C3 = make_card(3, "Coat the grime", "Spread it on with a spatula. Skip the heating element!", TOTAL)
def x_coat(t, D):
    p = ease_io(seg(t, 0.4, D - 0.4))
    edge = -100 + p * 2800                          # diagonal sweep, bottom-left to top-right
    v = XF * 0.6 + (H - YF)
    m = np.clip((edge - v) / 90, 0, 1) * PM
    base = oven(blend(DIRTY, [(PASTE, m)]))
    sx = W / 2 + math.sin(t * 3.2) * 360
    sy = clamp(H - (edge - sx * 0.6), 900, 1600)
    if 0.35 < t < D - 0.35: spatula(base, sx + math.sin(t * 18) * 30, sy, -25 + math.sin(t * 18) * 8)
    return base

C4 = make_card(4, "Wait overnight", "Let it sit at least 12 hours", TOTAL)
def x_wait(t, D):
    base = oven(blend(DIRTY, [(PASTE, PM)]))
    soft_disc(base, W // 2, 1180, 280, 150)
    p = ease_io(seg(t, 0.4, D - 0.4))
    timer(base, W // 2, 1190, p, str(int(round(p * 12))), "hours")
    d = ImageDraw.Draw(base)
    q = back(seg(t, 0.6, 1.1))
    if q > 0: moon(d, W // 2 + 210, 960, int(60 * q))
    return base

C5 = make_card(5, "Wipe it out", "Damp cloth + a plastic scraper for stuck bits", TOTAL)
def x_wipe(t, D):
    p = ease_io(seg(t, 0.4, D - 0.5))
    edge = -150 + p * (W + 300)
    m = np.clip((edge - XF) / 150, 0, 1)
    pasted = blend(DIRTY, [(PASTE, PM)])
    base = oven(blend(pasted, [(RESID, m)]))
    if 0.3 < t < D - 0.4: towel(base, edge, 1250 + math.sin(t * 9) * 170, ang=math.sin(t * 9) * 10, col=(120, 200, 230), stripe=(190, 230, 245))
    return base

C6 = make_card(6, "Spray vinegar", "It fizzes up the leftover paste. Wipe until clean.", TOTAL)
def x_vinegar(t, D):
    sp = ease_io(seg(t, 0.3, 1.9))                 # spray pass right -> left
    wp = ease_io(seg(t, 2.1, D - 0.5))             # wipe pass left -> right
    edge = -150 + wp * (W + 300)
    m = np.clip((edge - XF) / 150, 0, 1) if t > 2.1 else None
    base = oven(blend(RESID, [(CLEAN, m)]))
    if 0.3 < t < 2.6:
        sx = W + 40 - sp * (W - 100)
        pts = [p_ for p_ in RES_PTS if p_[0] > sx - 120 and (t < 2.1 or p_[0] > edge)]
        bubbles(base, t, 0.3, pts, col=(255, 255, 255), rise=24, rmax=16, speed=2.2)
    if 0.25 < t < 2.0:
        sx = W + 40 - sp * (W - 100); sy = 1230 + math.sin(t * 5) * 90
        sq = 1.0 if int(t * 6) % 2 == 0 else 0.0
        nx, ny = spray_bottle(base, sx + 120, sy, 0.9, sq, "VINEGAR", liquid=(225, 235, 240))
        mist(base, nx, ny, t, -1, 1.0, col=(230, 240, 255))
    if 2.1 < t < D - 0.4:
        towel(base, edge, 1250 + math.sin(t * 9) * 170, ang=math.sin(t * 9) * 10, col=(120, 200, 230), stripe=(190, 230, 245))
    if t > D - 0.9: sparkles(base, t, D - 0.9)
    return base

BA = make_ba(np.array(oven(DIRTY).convert("RGB")).astype(np.float32), np.array(oven(CLEAN).convert("RGB")).astype(np.float32), y_label=700, handle_y=1100)
OUTRO = make_outro(np.array(oven(CLEAN).convert("RGB")).astype(np.float32))

SCENES = [
    ("01_hook", HOOK, 3.3),
    ("02_safety", SAFETY, 5.4),
    ("03_empty", with_card(C1, x_empty), 3.4),
    ("04_paste", with_card(C2, x_paste), 3.6),
    ("05_coat", with_card(C3, x_coat), 3.6),
    ("06_wait", with_card(C4, x_wait), 3.2),
    ("07_wipe", with_card(C5, x_wipe), 3.4),
    ("08_vinegar", with_card(C6, x_vinegar), 4.2),
    ("09_ba", BA, 4.0),
    ("10_outro", OUTRO, 3.4),
]

def music(dur, cuts, impacts, path): make_track(dur, cuts, impacts, path, bpm=124, seed=6)

if __name__ == "__main__":
    mode, work = sys.argv[1], sys.argv[2]
    if mode == "stills":
        only = sys.argv[3].split(",") if len(sys.argv) > 3 else None
        print("\n".join(stills(SCENES, os.path.join(work, "stills"), (0.15, 0.55, 0.95), only)))
    else:
        print("total", build(SCENES, work, sys.argv[3], music))
