"""2026-11-08 — Fix a stinky washing machine (home). Uses lib/engine.py + lib/music_upbeat.py.
python3 tools/render_stinky_washing_machine.py stills|render WORKDIR OUT_MP4
"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.engine import *
from lib.music_upbeat import make_track

# ---------- front-loader, door open, looking into the drum ----------
CX, CY = 540, 1190
R_BEZ, R_GO, R_GI, R_BACK = 455, 425, 300, 175
RR = np.sqrt((XF - CX) ** 2 + (YF - CY) ** 2)
AA = np.arctan2(YF - CY, XF - CX)                       # +pi/2 = bottom of the ring
GMASK = np.clip((RR - R_GI + 3) / 6, 0, 1) * np.clip((R_GO - RR + 3) / 6, 0, 1)
DMASK = np.clip((R_GI - RR + 3) / 6, 0, 1)
TWO_PI = 2 * math.pi

def polar(r, a): return CX + r * math.cos(a), CY + r * math.sin(a)

def make_bgs():
    rng = np.random.default_rng(3)
    grain = rng.normal(0, 1, (H, W)).astype(np.float32)
    low = lowfreq(5, 70)
    # white machine front
    panel = np.array([232, 236, 240], np.float32) + ((low - 0.5) * 8 + grain * 2)[..., None]
    panel *= (1.02 - 0.06 * YF / H)[..., None]
    top = (YF < 230).astype(np.float32)
    panel = panel * (1 - top[..., None]) + np.array([206, 213, 220], np.float32) * top[..., None]
    panel -= (np.clip(1 - np.abs(YF - 230) / 4, 0, 1) * 70)[..., None]
    # bezel ring
    bez = np.clip((R_BEZ - RR) / 3, 0, 1) * np.clip((RR - R_GO) / 3, 0, 1)
    base = panel * (1 - bez[..., None]) + np.array([246, 248, 250], np.float32) * bez[..., None]
    base -= (np.clip(1 - np.abs(RR - R_BEZ) / 6, 0, 1) * 90)[..., None]
    base -= (np.clip(1 - np.abs(RR - R_BEZ - 12) / 14, 0, 1) * 25)[..., None]
    # rubber gasket
    tg = np.clip((RR - R_GI) / (R_GO - R_GI), 0, 1)
    light = 1 + 0.10 * (-np.sin(AA))
    rub = 132 * light - 38 * np.exp(-((tg - 0.28) / 0.07) ** 2) + 18 * np.exp(-((tg - 0.08) / 0.06) ** 2) \
          - 14 * np.exp(-((tg - 0.95) / 0.05) ** 2)
    rub_c = np.stack([rub, rub + 5, rub + 12], -1) + grain[..., None] * 2
    base = base * (1 - GMASK[..., None]) + rub_c * GMASK[..., None]
    # stainless drum: wall + perforations + lifters, back wall
    u = np.clip((RR - R_BACK) / (R_GI - R_BACK), 0, 1)
    steel = 168 + 34 * (-np.sin(AA)) * (0.4 + 0.6 * u) - 20 * (1 - u)
    row = u * 5
    stag = np.floor(row) % 2 * 0.5
    du = (row % 1 - 0.5) * (R_GI - R_BACK) / 5
    da = ((AA / TWO_PI * 56 + stag) % 1 - 0.5) * (TWO_PI * np.maximum(RR, 1) / 56)
    hole = np.clip((5 + 4 * u - np.sqrt(du ** 2 + da ** 2)) / 1.5, 0, 1) * (RR > R_BACK + 8) * (RR < R_GI - 8)
    back = (RR <= R_BACK).astype(np.float32)
    bx, by = ((XF - CX) % 36) - 18, ((YF - CY) % 36) - 18
    bhole = np.clip((5 - np.sqrt(bx ** 2 + by ** 2)) / 1.5, 0, 1) * (RR < R_BACK - 14) * (RR > 46)
    steel = steel * (1 - back) + (146 + 10 * (-np.sin(AA)) * RR / R_BACK) * back
    steel -= hole * 70 + bhole * 50
    steel -= np.clip(1 - np.abs(RR - R_BACK) / 4, 0, 1) * 40
    hub = np.clip((44 - RR) / 2, 0, 1); steel = steel * (1 - hub) + 120 * hub
    lift = np.zeros((H, W), np.float32)
    for la in (-math.pi / 2, math.pi / 6, 5 * math.pi / 6):
        dd = np.abs(((AA - la + math.pi) % TWO_PI) - math.pi)
        lift = np.maximum(lift, np.clip((0.11 * (0.6 + 0.4 * u) - dd) / 0.02, 0, 1) * (u > 0.08) * (u < 0.97))
    steel = steel * (1 - lift) + (196 + 20 * (-np.sin(AA))) * lift
    steel_c = np.stack([steel, steel + 4, steel + 9], -1)
    clean = base * (1 - DMASK[..., None]) + steel_c * DMASK[..., None]
    # gloss for the clean state
    gloss_g = np.exp(-((((AA + 2.25 + math.pi) % TWO_PI) - math.pi) / 0.32) ** 2) * np.exp(-((tg - 0.6) / 0.16) ** 2) * GMASK
    gloss_d = np.exp(-((((AA + 2.3 + math.pi) % TWO_PI) - math.pi) / 0.22) ** 2) * np.clip(1 - np.abs(u - 0.6) / 0.3, 0, 1) * DMASK * (RR > R_BACK)
    clean = clean + (gloss_g * 45 + gloss_d * 55)[..., None]

    # ---- dirt ----
    bottom = np.clip(np.sin(AA) * 1.3 + 0.35, 0, 1)
    sp1, sp2 = lowfreq(19, 16), lowfreq(29, 9)
    mold = np.clip((sp1 * 0.55 + sp2 * 0.45 - (0.62 - 0.22 * bottom)) / 0.06, 0, 1) * GMASK * (0.25 + 0.75 * bottom)
    k = Image.new("L", (W, H), 0); kd = ImageDraw.Draw(k); rr = random.Random(9)
    for _ in range(900):
        a = rr.uniform(0.05, math.pi - 0.05) if rr.random() < 0.8 else rr.uniform(-math.pi, math.pi)
        r = rr.uniform(R_GI + 8, R_GO - 6); x, y = polar(r, a); s = rr.uniform(2, 7)
        kd.ellipse([x - s, y - s, x + s, y + s], fill=255)
    dots = np.array(k.filter(ImageFilter.GaussianBlur(0.8))).astype(np.float32) / 255 * GMASK
    mold = np.maximum(mold, dots * 0.9)
    grime = np.clip(1 - tg / 0.22, 0, 1) * GMASK * (0.35 + 0.45 * lowfreq(33, 25)) \
            + np.exp(-((tg - 0.28) / 0.08) ** 2) * GMASK * 0.55 * bottom
    film = DMASK * (0.25 + 0.35 * lowfreq(41, 45))
    pud = DMASK * np.clip((np.sin(AA) - 0.55) / 0.15, 0, 1) * np.clip((RR - R_BACK - 10) / 20, 0, 1)
    MOLD = np.array([34, 40, 34], np.float32); BROWN = np.array([128, 106, 74], np.float32)
    FILM = np.array([136, 126, 104], np.float32); PUD = np.array([104, 108, 88], np.float32)

    def dirty_drum(b): return blend(b, [(FILM, film), (PUD, pud * 0.8)])
    def dirty_gasket(b): return blend(b, [(BROWN, grime * 0.75), (MOLD, mold)])
    clean_noglo = clean - (gloss_g * 45 + gloss_d * 55)[..., None]
    picked = dirty_drum(dirty_gasket(clean_noglo))
    scrubg = dirty_drum(clean_noglo + (gloss_g * 25)[..., None])
    # wet after the cycle: beads of water on drum and seal
    b = Image.new("L", (W, H), 0); bd = ImageDraw.Draw(b); rr = random.Random(4)
    for _ in range(260):
        a = rr.uniform(-math.pi, math.pi); r = rr.uniform(R_BACK + 12, R_GO - 10); x, y = polar(r, a); s = rr.uniform(4, 10)
        bd.ellipse([x - s, y - s * 1.2, x + s, y + s * 1.2], fill=255)
    beads = np.array(b.filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255
    wet = clean * (1 - 0.10 * (GMASK + DMASK))[..., None] + (beads * 70)[..., None]
    return picked, scrubg, wet, clean

PICKED, SCRUBG, WET, CLEAN = make_bgs()
N1, N2 = lowfreq(51, 40), lowfreq(61, 30)

# hair, lint and a coin hiding in the fold
ITEMS = [("hair", 1.25), ("lint", 1.62), ("coin", 1.98), ("lint", 2.35), ("hair", 0.85), ("sock", 2.7)]
def draw_item(img, kind, x, y, a=1.0, s=1.0):
    lay = Image.new("RGBA", (260, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    if kind == "hair":
        pts = [(30 + i * 10, 130 + math.sin(i * 0.7) * 26 * s) for i in range(21)]
        d.line(pts, fill=(52, 40, 32, 255), width=5, joint="curve")
        d.line([(p[0], p[1] + 14) for p in pts[3:18]], fill=(70, 56, 44, 255), width=4, joint="curve")
    elif kind == "lint":
        for j, (ox, oy, r) in enumerate([(130, 130, 34), (102, 140, 24), (158, 140, 22), (128, 108, 20)]):
            d.ellipse([ox - r, oy - r, ox + r, oy + r], fill=(176, 172, 178, 255), outline=(120, 118, 126, 255), width=4)
    elif kind == "coin":
        d.ellipse([88, 88, 172, 172], fill=(214, 176, 70, 255), outline=INK, width=6)
        d.ellipse([106, 106, 154, 154], outline=(170, 130, 40, 255), width=5)
    elif kind == "sock":
        d.polygon([(90, 70), (140, 70), (140, 150), (190, 170), (180, 205), (100, 190)], fill=(70, 150, 230, 255), outline=INK)
        d.line([(90, 70), (140, 70), (140, 150), (190, 170), (180, 205), (100, 190), (90, 70)], fill=INK, width=6)
        d.rectangle([92, 70, 140, 92], fill=(255, 255, 255, 255))
    if a < 1: lay = with_alpha(lay, a)
    img.alpha_composite(lay, (int(x - 130), int(y - 130)))

def item_pos(i):
    kind, ang = ITEMS[i]; x, y = polar(372, ang); return kind, x, y

def _bake_items(arr):
    im = to_img(arr)
    for i in range(len(ITEMS)):
        kind, x, y = item_pos(i); draw_item(im, kind, x, y)
    return np.array(im.convert("RGB")).astype(np.float32)
DIRTY = _bake_items(PICKED)

def stink(img, t, xmax=W, n=3, x0=200, gap=150, y0=1120, col=(120, 176, 60)):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for i in range(n):
        x = x0 + i * gap
        if x > xmax - 30: continue
        ph = (t * 0.9 + i * 0.33) % 1
        pts = [(x + math.sin(v / 40 + t * 5 + i) * 26, y0 - v - ph * 120) for v in range(0, 320, 10)]
        a = int(220 * math.sin(ph * math.pi))
        d.line(pts, fill=col + (a,), width=14, joint="curve")
    img.alpha_composite(lay)

def sweep(p, a0=-math.pi / 2, soft=0.18):
    ang = (AA - a0) % TWO_PI
    return np.clip((p * (TWO_PI + soft) - ang) / soft, 0, 1)

# ---------- props ----------
def sponge(img, x, y, ang=0):
    lay = Image.new("RGBA", (340, 340), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    rrect(d, [70, 120, 270, 240], 26, fill=(255, 212, 70), outline=INK, width=8)
    rrect(d, [70, 100, 270, 150], 18, fill=(60, 160, 100), outline=INK, width=8)
    for k in range(6): d.ellipse([95 + k * 30, 180, 107 + k * 30, 192], fill=(230, 180, 40))
    img.alpha_composite(lay.rotate(ang, resample=Image.BICUBIC), (int(x - 170), int(y - 170)))

def drawer(img, x, y, gunk=1.0):
    d = ImageDraw.Draw(img)
    rrect(d, [x - 270, y - 105, x + 270, y + 105], 26, fill=(250, 251, 252), outline=INK, width=9)
    for cx_ in (x - 170, x + 15, x + 185):
        w_ = 80 if cx_ != x + 15 else 95
        rrect(d, [cx_ - w_, y - 70, cx_ + w_, y + 70], 16, fill=(222, 228, 234), outline=(150, 160, 170), width=5)
    rrect(d, [x + 250, y - 60, x + 300, y + 60], 14, fill=(236, 240, 244), outline=INK, width=8)
    if gunk > 0:
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(lay); rr = random.Random(2)
        for cx_ in (x - 170, x + 15, x + 185):
            for _ in range(14):
                gx, gy, r = cx_ + rr.uniform(-60, 60), y + rr.uniform(10, 62), rr.uniform(8, 22)
                col = (60, 130, 200) if rr.random() < 0.4 else (40, 48, 40)
                ld.ellipse([gx - r, gy - r * 0.7, gx + r, gy + r * 0.7], fill=col + (int(220 * gunk),))
        img.alpha_composite(lay)

def basin_back(img, x, y, p):
    d = ImageDraw.Draw(img)
    d.ellipse([x - 400, y - 90, x + 400, y + 90], fill=(70, 150, 230), outline=INK, width=9)
    d.ellipse([x - 370, y - 70, x + 370, y + 70], fill=(150, 205, 245))

def basin_front(img, x, y):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rectangle([x - 370, y, x + 370, y + 70], fill=(150, 205, 245, 175))
    d.pieslice([x - 370, y - 70, x + 370, y + 70], 0, 180, fill=(150, 205, 245, 175))
    d.chord([x - 400, y - 90, x + 400, y + 260], 0, 180, fill=(70, 150, 230, 255), outline=INK, width=9)
    d.rectangle([x - 404, y - 4, x + 404, y + 4], fill=(70, 150, 230, 255))
    d.line([(x - 400, y), (x + 400, y)], fill=INK, width=9)
    img.alpha_composite(lay)

def door(img, cxd, half_w, R=445):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.ellipse([cxd - half_w, CY - R, cxd + half_w, CY + R], fill=(248, 250, 252, 255), outline=INK, width=9)
    gw = max(2, half_w * 0.78)
    d.ellipse([cxd - gw, CY - R * 0.78, cxd + gw, CY + R * 0.78], fill=(110, 160, 200, 150), outline=(80, 96, 110, 255), width=6)
    img.alpha_composite(lay)

# ---------- scenes ----------
TOTAL = 6
HOOK = make_hook(DIRTY, CLEAN,
                 [("WASHER SMELLS?", 100, (255, 255, 255)), ("IT'S HIDING", 160, YELLOW), ("IN THE SEAL", 160, YELLOW)],
                 "6 STEPS  ·  NO MORE MUSTY SMELL", mark_xy=(224, 1372), check_xy=(856, 1372),
                 extra=lambda base, t, D, sx: stink(base, t, xmax=sx, x0=150, gap=150, y0=1080))

SAFETY = make_safety(DIRTY, [
    ("ok", "Gloves on, room ventilated"),
    ("ok", "Follow your washer's manual and the cleaner's label"),
    ("no", "No undiluted bleach on the rubber seal"),
    ("never", "NEVER mix bleach with vinegar or ammonia"),
])

C1 = make_card(1, "Check the seal", "Pull back the rubber fold. Pick out hair, lint and lost items.", TOTAL)
def x_pick(t, D):
    base = to_img(PICKED)
    d = ImageDraw.Draw(base)
    pulse = 0.5 + 0.5 * math.sin(t * 9)
    if t < 1.2:
        a = int(255 * (0.55 + 0.45 * pulse) * (1 - seg(t, 0.9, 1.2)))
        d.arc([CX - 372, CY - 372, CX + 372, CY + 372], 15, 165, fill=ACC2 + (a,), width=16)
    for i in range(len(ITEMS)):
        kind, x, y = item_pos(i)
        q = ease(seg(t, 0.5 + i * 0.36, 1.0 + i * 0.36))
        if q >= 1: continue
        draw_item(base, kind, x + (540 - x) * q * 0.3, y - q * 330, a=1 - q * q, s=1 + q)
    if t < 1.6: stink(base, t, n=3, x0=330, gap=200, y0=1100)
    q = back(seg(t, D - 1.1, D - 0.7))
    if q > 0: pill(base, W // 2, CY, "HIDDEN IN THE FOLD", F("Bold", int(50 * max(q, 0.3))), ACC2, INK, min(1, q))
    return base

C2 = make_card(2, "Scrub the seal", "Diluted bleach solution on a sponge, mixed per the label. Wipe the folds.", TOTAL)
def x_scrub(t, D):
    p = ease_io(seg(t, 0.25, D - 0.35))
    m = sweep(p) * GMASK
    base = to_img(blend(PICKED, [(SCRUBG, m)]))
    a = -math.pi / 2 + p * TWO_PI
    pts = [polar(360 + 25 * math.sin(k * 1.7), a - 0.12 - k * 0.11) for k in range(9)]
    if 0.2 < t < D - 0.2:
        bubbles(base, t, 0.2, pts, col=(255, 255, 255), rise=14, rmax=12, speed=2.2)
        x, y = polar(362 + 14 * math.sin(t * 24), a)
        sponge(base, x, y, ang=-math.degrees(a) - 90 + math.sin(t * 24) * 8)
    return base

C3 = make_card(3, "Clean the drawer", "Pull it out, soak in hot soapy water, brush and rinse.", TOTAL)
def x_drawer(t, D):
    base = to_img(PICKED); dim(base, 110)
    bx, by = W // 2, 1330
    pb = ease(seg(t, 0.25, 0.7))
    if pb > 0: basin_back(base, bx, by + (1 - pb) * 500, pb)
    sl = back(seg(t, 0.1, 0.6))
    down = ease_io(seg(t, 0.85, 1.25)) - ease_io(seg(t, D - 0.85, D - 0.4))
    dx = -700 * (1 - sl); dy = 1020 + down * 300
    g = 1 - ease(seg(t, 1.3, D - 1.0))
    drawer(base, bx + dx, dy, gunk=g)
    if pb > 0: basin_front(base, bx, by + (1 - pb) * 500)
    if 1.2 < t < D - 0.8:
        bubbles(base, t, 1.2, [(bx - 300 + k * 85, by - 20 - (k % 3) * 18) for k in range(8)], rise=60, rmax=16, speed=1.6)
        scrub_brush(base, bx - 150 + math.sin(t * 20) * 140, by - 120, ang=math.sin(t * 20) * 10)
    if t > D - 0.5: sparkles(base, t, D - 0.5, 0.8, [(bx - 230, dy - 80), (bx + 220, dy - 90), (bx, dy - 130)])
    pill(base, W // 2, 1520, "HOT SOAPY WATER", F("Bold", 46), ACC2, INK, ease(seg(t, 0.6, 0.9)))
    return base

C4 = make_card(4, "Run a hot empty cycle", "Clean Washer or hottest cycle with washer cleaner or bleach, per your manual.", TOTAL)
def x_cycle(t, D):
    p = ease_io(seg(t, 0.5, D - 0.4))
    m = dissolve(p, N1) * DMASK
    base = to_img(blend(SCRUBG, [(WET, m)]))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.ellipse([CX - R_GI + 6, CY - R_GI + 6, CX + R_GI - 6, CY + R_GI - 6], fill=(120, 190, 240, 90))
    for k in range(6):
        r = 70 + k * 38; a0 = t * 380 + k * 55
        d.arc([CX - r, CY - r, CX + r, CY + r], a0, a0 + 110, fill=(255, 255, 255, 170), width=10)
    base.alpha_composite(lay)
    bubbles(base, t, 0.0, [polar(80 + (k * 47) % 200, k * 1.3 + t * 1.5) for k in range(10)], rise=30, rmax=12, speed=1.8)
    f = F("Bold", 46)
    pill(base, 300, 1520, "EMPTY DRUM", f, ACC2, INK, ease(seg(t, 0.3, 0.6)))
    pill(base, 790, 1520, "HOT", f, RED, (255, 255, 255), ease(seg(t, 0.6, 0.9)))
    return base

C5 = make_card(5, "Wipe it dry", "Towel off the seal, the door glass and the drum.", TOTAL)
def x_dry(t, D):
    p = ease_io(seg(t, 0.25, D - 0.35))
    base = to_img(blend(WET, [(CLEAN, sweep(p))]))
    if 0.2 < t < D - 0.2:
        a = -math.pi / 2 + p * TWO_PI
        x, y = polar(330 + 30 * math.sin(t * 20), a)
        towel(base, x, y, ang=-math.degrees(a) + math.sin(t * 20) * 10, col=(120, 200, 230), stripe=(190, 230, 245))
    return base

C6 = make_card(6, "Leave it open", "Door and drawer open after every load. Unload wet laundry right away.", TOTAL)
def x_open(t, D):
    base = to_img(CLEAN)
    q = ease_io(seg(t, 0.2, 1.0))
    if q < 1: door(base, CX + q * 470, 445 * (1 - q) + 40 * q)
    else: door(base, CX + 470, 40)
    if t > 0.9: airflow(base, t, 160, 900, [1050, 1130, 1210, 1290, 1370], speed=1000)
    if t > 1.4: sparkles(base, t, 1.4, 0.9)
    pill(base, W // 2, 1520, "AFTER EVERY LOAD", F("Bold", 50), ACC2, INK, ease(seg(t, 1.0, 1.3)))
    return base

BA = make_ba(DIRTY, CLEAN, y_label=700, handle_y=CY)
OUTRO = make_outro(CLEAN)

SCENES = [
    ("01_hook", HOOK, 3.3),
    ("02_safety", SAFETY, 4.8),
    ("03_pick", with_card(C1, x_pick), 3.6),
    ("04_scrub", with_card(C2, x_scrub), 3.4),
    ("05_drawer", with_card(C3, x_drawer), 3.8),
    ("06_cycle", with_card(C4, x_cycle), 3.6),
    ("07_dry", with_card(C5, x_dry), 3.2),
    ("08_open", with_card(C6, x_open), 3.4),
    ("09_ba", BA, 4.0),
    ("10_outro", OUTRO, 3.4),
]

def music(dur, cuts, impacts, path): make_track(dur, cuts, impacts, path, bpm=124, seed=13)

if __name__ == "__main__":
    mode, work = sys.argv[1], sys.argv[2]
    if mode == "stills":
        only = sys.argv[3].split(",") if len(sys.argv) > 3 else None
        print("\n".join(stills(SCENES, os.path.join(work, "stills"), (0.15, 0.55, 0.95), only)))
    else:
        print("total", build(SCENES, work, sys.argv[3], music))
