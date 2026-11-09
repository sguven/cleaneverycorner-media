"""2026-11-09 — Clean your microwave with lemon steam (home). Uses lib/engine.py + lib/music_upbeat.py (+ style rotation).
python3 tools/render_microwave_5_minutes.py stills|render WORKDIR [OUT_MP4]
"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.engine import *
from lib.music_upbeat import make_track
from lib.music_styles import pick_style

SLUG = "2026-11-09-microwave-5-minutes"

# ---------- microwave, door open, front view ----------
BX0, BX1, BY0, BY1 = 40, 1040, 790, 1460          # body
OX0, OX1, OY0, OY1 = 80, 800, 830, 1420           # cavity opening
KX0, KX1, KY0, KY1 = 230, 650, 950, 1270          # back wall
PX0, PX1 = 830, 1010                              # control panel
TCX, TCY, TRX, TRY = 440, 1335, 285, 60           # turntable
BOWL_X, BOWL_Y = 440, 1300                        # bowl base centre

def lerp(a, b, k): return a + (b - a) * k

def make_bgs():
    rng = np.random.default_rng(7)
    grain = rng.normal(0, 1, (H, W)).astype(np.float32)
    low = lowfreq(3, 80)
    # kitchen: subway-tile backsplash + counter
    wall = np.array([236, 232, 222], np.float32) + ((low - 0.5) * 10 + grain * 2)[..., None]
    row = (YF // 70) % 2
    gx = ((XF + row * 70) % 140); gy = YF % 70
    grout = np.clip(1 - np.minimum(gx, 140 - gx) / 3, 0, 1) + np.clip(1 - np.minimum(gy, 70 - gy) / 3, 0, 1)
    wall -= (np.clip(grout, 0, 1) * 34)[..., None]
    counter = YF > 1430
    ctop = np.array([150, 112, 80], np.float32) + ((lowfreq(9, 30) - 0.5) * 30 + grain * 3)[..., None]
    ctop -= (np.clip((YF - 1430) / 500, 0, 1) * 30)[..., None]
    base = np.where(counter[..., None], ctop, wall)
    base -= (np.clip(1 - np.abs(YF - 1430) / 5, 0, 1) * 60)[..., None]
    # shadow under the body
    sh = np.clip(1 - np.abs(YF - 1468) / 26, 0, 1) * (XF > BX0 - 20) * (XF < BX1 + 20)
    base -= (sh * 50)[..., None]
    # body (stainless, rounded rect)
    bm = Image.new("L", (W, H), 0); ImageDraw.Draw(bm).rounded_rectangle([BX0, BY0, BX1, BY1], 38, fill=255)
    body_m = np.array(bm.filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255
    steel = 196 + 22 * np.sin(XF / 210.0) - 18 * (YF - BY0) / (BY1 - BY0) + grain * 2
    body = np.stack([steel, steel + 4, steel + 9], -1)
    base = blend(base, [(body, body_m)])
    edge = Image.new("L", (W, H), 0); ImageDraw.Draw(edge).rounded_rectangle([BX0, BY0, BX1, BY1], 38, outline=255, width=6)
    base -= (np.array(edge).astype(np.float32) / 255 * 120)[..., None]
    # control panel
    pm = ((XF >= PX0) & (XF <= PX1) & (YF >= OY0) & (YF <= OY1)).astype(np.float32)
    pan = np.array([52, 60, 70], np.float32) + (grain * 2)[..., None] + (12 * (1 - (YF - OY0) / 600))[..., None]
    base = blend(base, [(pan, pm)])
    # cavity faces
    yc = (YF - OY0) / (KY0 - OY0); yf = (YF - KY1) / (OY1 - KY1)
    xl = (XF - OX0) / (KX0 - OX0); xr = (OX1 - XF) / (OX1 - KX1)
    inside = (XF >= OX0) & (XF <= OX1) & (YF >= OY0) & (YF <= OY1)
    back = (XF >= KX0) & (XF <= KX1) & (YF >= KY0) & (YF <= KY1)
    ceil = inside & ~back & (YF < KY0) & (yc <= np.minimum(xl, xr))
    floor = inside & ~back & (YF > KY1) & ((1 - yf) <= np.minimum(xl, xr))
    lwall = inside & ~back & ~ceil & ~floor & (XF < KX0)
    rwall = inside & ~back & ~ceil & ~floor & (XF > KX1)
    g = grain[..., None] * 1.5
    face = np.zeros((H, W, 3), np.float32)
    face += back[..., None] * (np.array([226, 224, 214], np.float32) - ((YF - KY0) / 320 * 10)[..., None])
    face += ceil[..., None] * (np.array([206, 204, 194], np.float32) + (np.clip(yc, 0, 1) * 16)[..., None])
    face += lwall[..., None] * (np.array([204, 202, 192], np.float32) + (np.clip(xl, 0, 1) * 18)[..., None])
    face += rwall[..., None] * (np.array([214, 212, 202], np.float32) + (np.clip(xr, 0, 1) * 12)[..., None])
    face += floor[..., None] * (np.array([186, 184, 176], np.float32) + (np.clip(1 - yf, 0, 1) * 16)[..., None])
    face += g
    # lamp glow, top right of the ceiling
    glow = np.exp(-(((XF - 600) / 160) ** 2 + ((YF - 900) / 70) ** 2))
    face += (glow * 30)[..., None] * inside[..., None]
    base = np.where(inside[..., None], face, base)
    # crease lines
    ln = Image.new("L", (W, H), 0); ld = ImageDraw.Draw(ln)
    ld.rectangle([KX0, KY0, KX1, KY1], outline=255, width=3)
    for a, b in [((OX0, OY0), (KX0, KY0)), ((OX1, OY0), (KX1, KY0)), ((OX0, OY1), (KX0, KY1)), ((OX1, OY1), (KX1, KY1))]:
        ld.line([a, b], fill=255, width=3)
    ld.rectangle([OX0, OY0, OX1, OY1], outline=255, width=5)
    base -= (np.array(ln.filter(ImageFilter.GaussianBlur(0.8))).astype(np.float32) / 255 * 55)[..., None]
    # vent slots on the right wall
    for k in range(6):
        y = 1000 + k * 26
        vm = (np.abs(YF - y) < 4) & (XF > 700) & (XF < 760) & rwall
        base -= (vm * 40)[..., None]
    # turntable (glass) + roller ring
    tt = ((XF - TCX) / TRX) ** 2 + ((YF - TCY) / TRY) ** 2
    plate = np.clip((1 - tt) * 40, 0, 1)
    rim = np.clip(1 - np.abs(np.sqrt(tt) - 0.97) / 0.04, 0, 1)
    ring_ = np.clip(1 - np.abs(np.sqrt(((XF - TCX) / (TRX * 0.6)) ** 2 + ((YF - TCY) / (TRY * 0.6)) ** 2) - 1) / 0.08, 0, 1)
    empty = base.copy()
    empty -= (ring_ * 35 * floor)[..., None]
    glass = base * 0.75 + np.array([200, 222, 216], np.float32) * 0.25
    glass += (np.exp(-(((XF - TCX + 120) / 90) ** 2 + ((YF - TCY + 22) / 14) ** 2)) * 40)[..., None]
    withplate = blend(base - (ring_ * 20 * floor)[..., None], [(glass, plate)])
    withplate -= (rim * 70)[..., None]
    clean_floor_only = withplate

    # ---- dirt ----
    def splat_mask(seed, n, region, rmin, rmax, drip=False):
        m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m); rr = random.Random(seed)
        ys, xs = np.nonzero(region[::4, ::4]); idx = list(range(len(xs)))
        for _ in range(n):
            j = rr.choice(idx); x, y = xs[j] * 4, ys[j] * 4; r = rr.uniform(rmin, rmax)
            d.ellipse([x - r, y - r * rr.uniform(0.6, 1), x + r, y + r * rr.uniform(0.6, 1)], fill=255)
            for _k in range(rr.randint(0, 4)):
                a = rr.uniform(0, 2 * math.pi); dd = r + rr.uniform(4, 22); s = rr.uniform(2, 6)
                d.ellipse([x + dd * math.cos(a) - s, y + dd * math.sin(a) - s, x + dd * math.cos(a) + s, y + dd * math.sin(a) + s], fill=255)
            if drip and rr.random() < 0.15:
                L = rr.uniform(20, 70); d.line([(x, y), (x + rr.uniform(-3, 3), y + L)], fill=255, width=int(max(3, r * 0.35)))
        a = np.array(m.filter(ImageFilter.GaussianBlur(1.0))).astype(np.float32) / 255
        return a * region
    cav = (ceil | back | lwall | rwall | floor).astype(np.float32)
    hot = np.exp(-(((XF - 330) / 170) ** 2 + ((YF - 1080) / 140) ** 2))     # extra-dirty spot for the hook marker
    red = np.maximum(splat_mask(11, 110, ceil | back, 5, 18, drip=True), splat_mask(12, 45, lwall | rwall, 4, 14, drip=True))
    red = np.maximum(red, splat_mask(13, 55, back & (hot > 0.35), 8, 22, drip=True))
    brn = splat_mask(21, 90, ceil | back | lwall | rwall, 3, 10)
    film = cav * (0.20 + 0.25 * lowfreq(31, 50) + 0.25 * hot)
    pspots = splat_mask(41, 26, (tt < 0.75), 6, 20) * plate
    RED_C = np.array([198, 104, 46], np.float32); BRN = np.array([112, 84, 52], np.float32)
    FILM = np.array([190, 168, 120], np.float32); CRUST = np.array([120, 78, 44], np.float32)
    def dirt_cavity(b): return blend(b, [(FILM, film), (BRN, brn * 0.85), (RED_C, red * 0.85)])
    def dirt_plate(b): return blend(b, [(CRUST, pspots * 0.9)])
    clean = clean_floor_only
    dirty = dirt_plate(dirt_cavity(clean))
    clean_dp = dirt_plate(clean)                      # cavity wiped, plate still to wash
    noplate = blend(empty, [])
    # condensation after the steam
    bm2 = Image.new("L", (W, H), 0); bd = ImageDraw.Draw(bm2); rr = random.Random(5)
    for _ in range(700):
        x, y = rr.uniform(OX0, OX1), rr.uniform(OY0, KY1 + 40); s = rr.uniform(3, 8)
        bd.ellipse([x - s, y - s * 1.2, x + s, y + s * 1.2], fill=255)
    beads = np.array(bm2.filter(ImageFilter.GaussianBlur(1.0))).astype(np.float32) / 255 * cav
    soft = blend(dirty, [(clean, cav * 0.25)])        # steam softens the mess
    wet = soft + (beads * 60)[..., None]
    return dirty, clean, clean_dp, wet, noplate, cav

DIRTY, CLEAN, CLEAN_DP, WET, NOPLATE, CAV = make_bgs()
WET_BLUR = np.array(to_img(WET).filter(ImageFilter.GaussianBlur(14)).convert("RGB")).astype(np.float32)

# ---------- props ----------
def display(img, text, lit=True):
    d = ImageDraw.Draw(img)
    rrect(d, [PX0 + 16, OY0 + 30, PX1 - 16, OY0 + 110], 12, fill=(18, 28, 26), outline=(10, 14, 16), width=4)
    if text: d.text(((PX0 + PX1) / 2, OY0 + 70), text, font=F("Bold", 50), fill=(110, 240, 170) if lit else (60, 110, 90), anchor="mm")

def keypad(img):
    d = ImageDraw.Draw(img)
    for r_ in range(4):
        for c in range(3):
            x = PX0 + 30 + c * 44; y = OY0 + 150 + r_ * 54
            rrect(d, [x, y, x + 34, y + 38], 8, fill=(84, 94, 106), outline=(30, 36, 44), width=3)
    rrect(d, [PX0 + 26, OY0 + 400, PX1 - 26, OY0 + 470], 14, fill=(84, 94, 106), outline=(30, 36, 44), width=3)
    rrect(d, [PX0 + 26, OY0 + 490, PX1 - 26, OY0 + 560], 14, fill=TEAL, outline=(30, 36, 44), width=3)

def bowl(img, x, y, lemon=1.0, fill=1.0, s=1.0):
    """glass bowl (front view) with water and a lemon half; (x, y) = bottom centre."""
    lay = Image.new("RGBA", (420, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    cx, top, bot = 210, 110, 270
    d.polygon([(cx - 160, top), (cx + 160, top), (cx + 105, bot), (cx - 105, bot)], fill=(214, 236, 246, 210))
    if fill > 0:
        wy = bot - (bot - top - 26) * fill
        k = (wy - top) / (bot - top)
        hw = 160 - 55 * k
        d.polygon([(cx - hw, wy), (cx + hw, wy), (cx + 105, bot - 6), (cx - 105, bot - 6)], fill=(150, 205, 245, 230))
        d.ellipse([cx - hw, wy - 14, cx + hw, wy + 14], fill=(185, 225, 250, 240))
        if lemon > 0:
            lx, ly = cx + 30, wy - 4
            la = int(255 * lemon)
            d.pieslice([lx - 62, ly - 50, lx + 62, ly + 50], 180, 360, fill=(255, 212, 50, la), outline=INK + (la,), width=6)
            d.pieslice([lx - 46, ly - 36, lx + 46, ly + 36], 180, 360, fill=(255, 238, 150, la))
    d.ellipse([cx - 160, top - 22, cx + 160, top + 22], outline=INK, width=7)
    d.line([(cx - 160, top), (cx - 105, bot)], fill=INK, width=7); d.line([(cx + 160, top), (cx + 105, bot)], fill=INK, width=7)
    d.line([(cx - 105, bot), (cx + 105, bot)], fill=INK, width=7)
    d.line([(cx - 120, top + 40), (cx - 92, bot - 30)], fill=(255, 255, 255, 200), width=8)
    if s != 1: lay = lay.resize((int(420 * s), int(300 * s)), Image.BICUBIC)
    img.alpha_composite(lay, (int(x - lay.width / 2), int(y - 270 * s)))

def lemon_half(img, x, y, squeeze=0.0, ang=0):
    lay = Image.new("RGBA", (260, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    sq = 1 - 0.18 * squeeze
    d.chord([130 - 90 * sq, 60, 130 + 90 * sq, 230], 0, 180, fill=(255, 205, 40), outline=INK, width=7)
    d.ellipse([130 - 90 * sq, 120, 130 + 90 * sq, 160], fill=(255, 238, 150), outline=INK, width=6)
    for k in range(8):
        a = k * math.pi / 4
        d.line([(130, 140), (130 + 70 * sq * math.cos(a), 140 + 16 * math.sin(a))], fill=(250, 214, 90), width=3)
    img.alpha_composite(lay.rotate(180 + ang, resample=Image.BICUBIC), (int(x - 130), int(y - 130)))

def door(img, half, inner=None, fog=1.0):
    """door hinged on the left edge of the opening; half in [0,1] = how closed (1 = closed)."""
    if half <= 0.01: return
    w = (OX1 - OX0 + 30) * half
    x0, y0, y1 = OX0 - 15, OY0 - 15, OY1 + 15
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    rrect(d, [x0, y0, x0 + w, y1], 22, fill=(46, 54, 64, 255), outline=INK, width=8)
    if half > 0.6 and inner is not None:
        wx0, wy0, wx1, wy1 = x0 + 50 * half, y0 + 60, x0 + w - 50, y1 - 60
        win = inner.crop((int(OX0 + 40), int(OY0 + 40), int(OX0 + 40 + (wx1 - wx0)), int(OY0 + 40 + (wy1 - wy0))))
        win = win.resize((max(1, int(wx1 - wx0)), int(wy1 - wy0)))
        haze = Image.new("RGBA", win.size, (235, 240, 245, int(170 * fog)))
        win = Image.alpha_composite(win.convert("RGBA"), haze)
        mask = Image.new("L", win.size, 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, win.width - 1, win.height - 1], 18, fill=255)
        lay.paste(win, (int(wx0), int(wy0)), mask)
        d.rounded_rectangle([wx0, wy0, wx1, wy1], 18, outline=(20, 26, 32, 255), width=6)
        rr = random.Random(3)
        for _ in range(int(160 * fog)):
            x, y, s = rr.uniform(wx0 + 10, wx1 - 10), rr.uniform(wy0 + 10, wy1 - 10), rr.uniform(3, 7)
            d.ellipse([x - s, y - s * 1.2, x + s, y + s * 1.2], fill=(255, 255, 255, 120))
    img.alpha_composite(lay)

def haze(img, a, glow=0.0):
    if a > 0:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(lay).rectangle([OX0, OY0, OX1, OY1], fill=(255, 255, 255, int(a)))
        img.alpha_composite(lay)
    if glow > 0:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(lay).rectangle([OX0, OY0, OX1, OY1], fill=(255, 210, 90, int(glow)))
        img.alpha_composite(lay)

def _panel(arr):
    im = to_img(arr); display(im, ""); keypad(im); return np.array(im.convert("RGB")).astype(np.float32)
DIRTY, CLEAN, CLEAN_DP, WET, NOPLATE = map(_panel, (DIRTY, CLEAN, CLEAN_DP, WET, NOPLATE))

def frame_base(arr, disp="", lit=True):
    im = to_img(arr)
    if disp: display(im, disp, lit)
    return im

# ---------- scenes ----------
TOTAL = 5
HOOK = make_hook(DIRTY, CLEAN,
                 [("CRUSTY MICROWAVE?", 90, (255, 255, 255)), ("STOP", 150, YELLOW), ("SCRUBBING", 148, YELLOW)],
                 "1 LEMON  ·  5 STEPS  ·  NO SCRUBBING", mark_xy=(330, 1090), check_xy=(640, 1090), split_to=0.45)

SAFETY = make_safety(lambda t: frame_base(DIRTY), [
    ("ok", "Microwave-safe bowl only. Nothing metal."),
    ("ok", "Oven mitts: the bowl and steam get very hot"),
    ("no", "No steel wool or scouring pads inside"),
    ("never", "NEVER run the microwave empty"),
], title="Before you start", label="SAFETY FIRST")

C1 = make_card(1, "Lemon + water", "1 cup of water in a microwave-safe bowl. Squeeze in half a lemon, drop it in.", TOTAL)
def x_bowl(t, D):
    base = frame_base(DIRTY)
    q = back(seg(t, 0.15, 0.7))
    bowl(base, BOWL_X, BOWL_Y + (1 - q) * 700, lemon=ease(seg(t, 2.35, 2.6)), fill=1.0)
    if 0.8 < t < 2.5:
        sq = 0.5 + 0.5 * math.sin(t * 14)
        lx, ly = BOWL_X + 30, 980 + (1 - ease(seg(t, 0.8, 1.1))) * -300
        if t > 2.2: ly += ease(seg(t, 2.2, 2.45)) * 230
        lemon_half(base, lx, ly, squeeze=sq if t < 2.1 else 0)
        dd = ImageDraw.Draw(base)
        if 1.1 < t < 2.1:
            for k in range(4):
                f = ((t - 1.1) * 2.2 + k * 0.25) % 1
                y = ly + 40 + f * 170
                dd.ellipse([lx - 9 + (k % 2) * 14, y - 13, lx + 9 + (k % 2) * 14, y + 13], fill=(255, 226, 90), outline=INK, width=3)
    pill(base, W // 2, 1520, "1 CUP WATER + HALF A LEMON", F("Bold", 46), ACC2, INK, ease(seg(t, 0.5, 0.8)))
    return base

C2 = make_card(2, "Heat it on high", "3 to 5 minutes, until the water boils and the window fogs up.", TOTAL)
def x_heat(t, D):
    secs = int(180 * (1 - seg(t, 0.3, D - 0.2)))
    base = frame_base(DIRTY, f"{secs // 60}:{secs % 60:02d}")
    haze(base, 0, glow=55 + 20 * math.sin(t * 6))
    bowl(base, BOWL_X + math.sin(t * 2.4) * 70, BOWL_Y, lemon=1.0)
    if t > 0.5:
        wisps(base, t, [BOWL_X - 80 + math.sin(t * 2.4) * 70 + k * 80 for k in range(3)], BOWL_Y - 170, height=300,
              alpha=int(230 * ease(seg(t, 0.5, 1.2))), speed=1.1)
    haze(base, 120 * ease(seg(t, 1.0, D)))
    f = F("Bold", 48)
    pill(base, 300, 1520, "HIGH", f, RED, (255, 255, 255), ease(seg(t, 0.3, 0.6)))
    pill(base, 650, 1520, "3-5 MIN", f, ACC2, INK, ease(seg(t, 0.55, 0.85)))
    return base

C3 = make_card(3, "Let it steam", "Keep the door closed for 5 minutes. The steam loosens the splatter.", TOTAL)
def x_steam(t, D):
    base = frame_base(WET, "0:00", lit=True)
    inner = to_img(WET_BLUR); bowl(inner, BOWL_X, BOWL_Y, lemon=1.0)
    q = ease_io(seg(t, 0.1, 0.6))
    door(base, q, inner=inner, fog=1.0)
    if t > 0.6:
        timer(base, (OX0 + OX1) // 2, 1110, ease_io(seg(t, 0.8, D - 0.3)), "5", "min", R=150)
    pill(base, W // 2, 1520, "DOOR CLOSED", F("Bold", 48), ACC2, INK, ease(seg(t, 0.6, 0.9)))
    return base

WIPE = []
for k, y in enumerate([880, 960, 1040, 1120, 1200, 1280, 1370]):
    xs = (130, 760) if k % 2 == 0 else (760, 130)
    WIPE += [(xs[0], y), (xs[1], y)]
C4 = make_card(4, "Wipe it clean", "Mitts on, lift out the bowl. Wipe top, walls and door with a soft sponge.", TOTAL)
def x_wipe(t, D):
    p = ease_io(seg(t, 0.25, D - 0.3)) * (len(WIPE) - 1)
    m = trail_mask(WIPE, p, radius=95, blur=16) * CAV if t > 0.25 else 0
    base = frame_base(blend(WET, [(CLEAN_DP, m)]))
    if 0.2 < t < D - 0.15:
        x, y = path_point(WIPE, p)
        sponge(base, x, y + math.sin(t * 30) * 8, ang=math.sin(t * 22) * 10)
    pill(base, W // 2, 1520, "DIP IT IN THE LEMON WATER", F("Bold", 46), ACC2, INK, ease(seg(t, 0.4, 0.7)))
    return base

def plate(img, x, y, crust=1.0, s=1.0):
    lay = Image.new("RGBA", (700, 220), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.ellipse([20, 40, 680, 180], fill=(205, 228, 222, 235), outline=INK, width=8)
    d.ellipse([90, 64, 610, 156], outline=(160, 190, 184, 255), width=5)
    d.ellipse([140, 70, 300, 100], fill=(255, 255, 255, 120))
    if crust > 0:
        rr = random.Random(8)
        for _ in range(16):
            cx_, cy_, r = rr.uniform(120, 580), rr.uniform(75, 150), rr.uniform(10, 26)
            d.ellipse([cx_ - r, cy_ - r * 0.5, cx_ + r, cy_ + r * 0.5], fill=(120, 78, 44, int(235 * crust)))
    if s != 1: lay = lay.resize((int(700 * s), int(220 * s)), Image.BICUBIC)
    img.alpha_composite(lay, (int(x - lay.width / 2), int(y - lay.height / 2)))

C5 = make_card(5, "Wash the turntable", "Warm soapy water, rinse, dry it and put it back.", TOTAL)
def x_plate(t, D):
    base = frame_base(blend(NOPLATE, [(CLEAN, 0)])); dim(base, 110)
    bx, by = W // 2, 1300
    pb = ease(seg(t, 0.2, 0.6))
    if pb > 0: basin_back(base, bx, by + (1 - pb) * 500)
    lift = ease_io(seg(t, 0.0, 0.55))
    py = lerp(TCY, by - 10, lift)
    plate(base, lerp(TCX, bx, lift), py, crust=1 - ease(seg(t, 1.2, D - 0.8)), s=lerp(0.86, 1.0, lift))
    if pb > 0: basin_front(base, bx, by + (1 - pb) * 500)
    if 1.0 < t < D - 0.6:
        bubbles(base, t, 1.0, [(bx - 300 + k * 85, by - 20 - (k % 3) * 18) for k in range(8)], rise=60, rmax=16, speed=1.6)
        sponge(base, bx - 120 + math.sin(t * 18) * 160, by - 90, ang=math.sin(t * 18) * 10)
    if t > D - 0.6: sparkles(base, t, D - 0.6, 0.8, [(bx - 230, by - 60), (bx + 220, by - 70), (bx, by - 110)])
    pill(base, W // 2, 1520, "WARM SOAPY WATER", F("Bold", 48), ACC2, INK, ease(seg(t, 0.6, 0.9)))
    return base

SP_MW = [(180, 900), (700, 960), (440, 1060), (300, 1200), (640, 1250), (920, 1000), (160, 1330), (560, 880)]
_BA = make_ba(DIRTY, CLEAN, y_label=700, handle_y=1130, spark_pts=SP_MW)
def BA(t, D): return _BA(t, D)
BA.impact_at = _BA.impact_at
_OUT = make_outro(CLEAN)
def OUTRO(t, D): return _OUT(t, D)

def HOOK_F(t, D): return HOOK(t, D)
HOOK_F.headline_until = HOOK.headline_until

SCENES = [
    ("01_hook", HOOK_F, 3.3),
    ("02_safety", SAFETY, 4.4),
    ("03_bowl", with_card(C1, x_bowl), 3.6),
    ("04_heat", with_card(C2, x_heat), 3.4),
    ("05_steam", with_card(C3, x_steam), 3.4),
    ("06_wipe", with_card(C4, x_wipe), 3.8),
    ("07_plate", with_card(C5, x_plate), 3.6),
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
