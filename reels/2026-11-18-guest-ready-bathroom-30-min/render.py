"""2026-11-18 — Guest-ready bathroom in 30 minutes (home). lib/engine.py + lib/music_upbeat.py (clean style, upbeat=True).
Hook: "GUEST-READY IN 30 MIN" (time promise) -> split screen messy vanity | guest-ready vanity.
    python3 render.py stills [scene,scene] [fracs]      -> stills/*.jpg
    python3 render.py render                            -> guest-ready-bathroom-30-min.mp4 (+ work/)
Sources checked: Homes & Gardens 30-minute bathroom routine (declutter into a basket, spray and let products sit
2-3 min, toilet bowl first, work top to bottom, floor last, run the extractor fan), Merry Maids mirror guide (spray the
cloth, not the mirror, so liquid doesn't reach the edges / backing), Blue Cross Blue Shield of Michigan "cleaning
products not to mix" (bleach + ammonia -> chloramine, bleach + acidic cleaners incl. toilet bowl cleaners -> chlorine
gas; use in a well-ventilated space).
"""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from lib.engine import *
from lib.music_upbeat import make_track
from lib.music_styles import pick_style

SLUG = "2026-11-18-guest-ready-bathroom-30-min"
NAME = "guest-ready-bathroom-30-min"
PILL_Y = 1290

# layout
MIR = (210, 640, 870, 990)          # mirror interior box
CT_Y0, CT_Y1 = 1030, 1112           # counter top (seen slightly from above)
SINK = (540, 1072, 190, 30)         # cx, cy, rx, ry
CAB_Y1 = 1395                       # cabinet bottom / floor starts
TWL = (905, 735, 1045, 1005)        # towel area

def lmask(draw_fn, blur=2):
    m = Image.new("L", (W, H), 0); draw_fn(ImageDraw.Draw(m))
    m = m.filter(ImageFilter.GaussianBlur(blur)) if blur else m
    return np.array(m).astype(np.float32) / 255

def to_arr(img): return np.array(img.convert("RGB")).astype(np.float32)
def layer(): return Image.new("RGBA", (W, H), (0, 0, 0, 0))

def sink_box(pad=0):
    cx, cy, rx, ry = SINK; return [cx - rx - pad, cy - ry - pad, cx + rx + pad, cy + ry + pad]

def draw_room(clean=True):
    """flat illustrated vanity: tiled wall, mirror, faucet, counter + sink, cabinet, floor, towel ring."""
    rng = random.Random(1118)
    im = Image.new("RGBA", (W, H), (232, 240, 242, 255)); d = ImageDraw.Draw(im)
    # subway tiles
    for r, y in enumerate(range(0, CT_Y0, 70)):
        off = 0 if r % 2 == 0 else 80
        for x in range(-160 + off, W, 160):
            d.rectangle([x + 3, y + 3, x + 157, y + 67], fill=(238, 245, 247), outline=(205, 218, 222), width=3)
    # sconce glow above mirror
    # mirror frame + interior
    x0, y0, x1, y1 = MIR
    rrect(d, [x0 - 22, y0 - 22, x1 + 22, y1 + 22], 46, fill=(196, 160, 110), outline=INK, width=8)
    mi = Image.new("RGBA", (x1 - x0, y1 - y0)); md = ImageDraw.Draw(mi)
    for k in range(y1 - y0):
        g = k / (y1 - y0)
        md.line([(0, k), (x1 - x0, k)], fill=(int(198 - 30 * g), int(222 - 26 * g), int(232 - 22 * g), 255))
    md.rectangle([60, 120, 230, 350], fill=(214, 228, 234, 255))                 # reflected door frame
    md.rectangle([80, 140, 210, 350], fill=(190, 208, 216, 255))
    for k, a in ((130, 120), (210, 70)):                                            # gloss streaks
        md.polygon([(k + 260, 0), (k + 330, 0), (k + 120, y1 - y0), (k + 50, y1 - y0)], fill=(255, 255, 255, a))
    m = Image.new("L", mi.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, mi.width - 1, mi.height - 1], 30, fill=255)
    im.paste(mi, (x0, y0), m)
    # towel ring
    d.ellipse([945, 655, 1005, 715], outline=(160, 166, 172), width=10)
    d.rectangle([965, 640, 985, 660], fill=(140, 146, 152))
    # counter (top + front edge) and cabinet
    d.rectangle([60, CT_Y0, 1020, CT_Y1], fill=(246, 243, 236), outline=INK, width=6)
    d.rectangle([60, CT_Y1, 1020, CT_Y1 + 26], fill=(226, 221, 210), outline=INK, width=6)
    d.rectangle([90, CT_Y1 + 26, 990, CAB_Y1], fill=(46, 78, 108), outline=INK, width=6)
    for bx in (110, 550):
        rrect(d, [bx, CT_Y1 + 50, bx + 420, CAB_Y1 - 22], 14, fill=(56, 92, 126), outline=INK, width=5)
        rrect(d, [bx + 30, CT_Y1 + 75, bx + 390, CAB_Y1 - 47], 10, outline=(40, 68, 96), width=4)
    for hx in (500, 580):
        rrect(d, [hx - 9, CT_Y1 + 110, hx + 9, CT_Y1 + 200], 9, fill=(205, 175, 120), outline=INK, width=4)
    # sink basin + faucet
    cx, cy, rx, ry = SINK
    d.ellipse(sink_box(10), fill=(250, 250, 248), outline=INK, width=6)
    d.ellipse(sink_box(0), fill=(214, 222, 228))
    d.ellipse([cx - rx + 18, cy - ry + 10, cx + rx - 18, cy + ry - 2], fill=(232, 238, 242))
    d.ellipse([cx - 12, cy + 4, cx + 12, cy + 14], fill=(150, 156, 162))
    rrect(d, [cx - 38, 1008, cx + 38, 1040], 10, fill=(196, 204, 212), outline=INK, width=5)
    d.line([(cx, 1010), (cx, 960), (cx + 70, 960), (cx + 70, 985)], fill=INK, width=28, joint="curve")
    d.line([(cx, 1010), (cx, 960), (cx + 70, 960), (cx + 70, 985)], fill=(205, 212, 220), width=16, joint="curve")
    d.line([(cx - 4, 1000), (cx - 4, 968)], fill=(255, 255, 255), width=5)
    for hx in (cx - 110, cx + 110):
        rrect(d, [hx - 18, 1004, hx + 18, 1040], 8, fill=(205, 212, 220), outline=INK, width=4)
    # soap dispenser + small plant (always there)
    rrect(d, [250, 950, 320, 1050], 18, fill=(150, 205, 200), outline=INK, width=6)
    rrect(d, [272, 918, 298, 952], 6, fill=(205, 212, 220), outline=INK, width=4)
    d.line([(285, 922), (318, 922)], fill=INK, width=8)
    rrect(d, [140, 990, 210, 1050], 10, fill=(236, 230, 220), outline=INK, width=6)
    for a in (-50, -20, 10, 40):
        r_ = math.radians(a - 90)
        d.ellipse([175 + math.cos(r_) * 45 - 18, 985 + math.sin(r_) * 45 - 26, 175 + math.cos(r_) * 45 + 18, 985 + math.sin(r_) * 45 + 26],
                  fill=(70, 160, 110), outline=INK, width=4)
    # floor tiles
    d.rectangle([0, CAB_Y1, W, H], fill=(214, 218, 220))
    for y in range(CAB_Y1, H, 150):
        d.line([(0, y), (W, y)], fill=(188, 194, 198), width=4)
    for x in range(-60, W + 60, 180):
        d.line([(x, CAB_Y1), (x - 90, H)], fill=(188, 194, 198), width=4)
    d.rectangle([0, CAB_Y1 - 6, W, CAB_Y1 + 10], fill=(36, 58, 80))
    # towel
    if clean:
        rrect(d, [TWL[0] + 10, TWL[1], TWL[2] - 10, TWL[3] - 20], 14, fill=(250, 250, 250), outline=INK, width=6)
        d.rectangle([TWL[0] + 16, TWL[3] - 90, TWL[2] - 16, TWL[3] - 66], fill=ACCENT)
        d.line([(TWL[0] + 30, TWL[1] + 30), (TWL[0] + 30, TWL[3] - 110)], fill=(225, 230, 232), width=6)
    else:
        pts = [(TWL[0] + 20, TWL[1]), (TWL[2] - 15, TWL[1] + 8), (TWL[2] - 5, TWL[3] - 60), (TWL[2] - 40, TWL[3] - 20),
               (TWL[0] + 60, TWL[3] - 2), (TWL[0] + 5, TWL[3] - 70)]
        d.polygon(pts, fill=(170, 172, 168), outline=INK, width=6)
        for k in range(4):
            d.line([(TWL[0] + 30 + k * 26, TWL[1] + 30), (TWL[0] + 20 + k * 30, TWL[3] - 40)], fill=(140, 142, 138), width=5)
    return im

# ---------- dirt (drawn as RGBA layers, flattened into arrays) ----------
def dirt_mirror():
    lay = layer(); d = ImageDraw.Draw(lay); rr = random.Random(7)
    x0, y0, x1, y1 = MIR
    for _ in range(170):                                    # toothpaste splatter, mostly low/center
        x = rr.gauss(540, 170); y = y1 - abs(rr.gauss(0, 120)) - 10
        if not (x0 + 15 < x < x1 - 15 and y0 + 15 < y < y1 - 10): continue
        r = rr.uniform(3, 10)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(250, 252, 252, 235), outline=(170, 196, 204, 255), width=2)
    for _ in range(40):                                     # water spot rings
        x, y = rr.uniform(x0 + 30, x1 - 30), rr.uniform(y0 + 30, y1 - 30); r = rr.uniform(8, 18)
        d.ellipse([x - r, y - r, x + r, y + r], outline=(236, 236, 226, 200), width=3)
    sm = layer(); sd = ImageDraw.Draw(sm)
    for x, y in ((330, 760), (360, 800), (700, 700), (735, 745)):   # finger smudges
        sd.ellipse([x - 40, y - 55, x + 40, y + 55], fill=(225, 222, 205, 150))
    lay.alpha_composite(sm.filter(ImageFilter.GaussianBlur(12)))
    return lay

def dirt_sink():
    lay = layer(); d = ImageDraw.Draw(lay); rr = random.Random(11)
    cx, cy, rx, ry = SINK
    d.ellipse([cx - rx + 6, cy - ry + 4, cx + rx - 6, cy + ry], outline=(150, 132, 108, 220), width=10)   # grime ring
    for x, y, r in ((470, 1072, 16), (600, 1080, 12), (520, 1060, 9), (640, 1066, 10)):                  # toothpaste globs
        d.ellipse([x - r * 1.6, y - r, x + r * 1.6, y + r], fill=(120, 200, 210, 255), outline=(60, 140, 150, 255), width=3)
    for _ in range(6):                                                                                  # hairs
        x, y = rr.uniform(400, 680), rr.uniform(1055, 1095)
        d.arc([x - 40, y - 12, x + 40, y + 12], rr.uniform(0, 90), rr.uniform(180, 300), fill=(50, 40, 30, 255), width=3)
    for _ in range(26):                                                                                 # counter water spots
        x, y = rr.uniform(120, 960), rr.uniform(CT_Y0 + 10, CT_Y1 - 10); r = rr.uniform(6, 13)
        d.ellipse([x - r * 1.5, y - r * 0.6, x + r * 1.5, y + r * 0.6], outline=(205, 205, 192, 230), width=3)
    for x in (510, 560, 425, 655):                                                                      # limescale on faucet
        d.ellipse([x - 8, 1022, x + 8, 1036], fill=(240, 240, 228, 255))
    return lay

def dirt_floor():
    lay = layer(); d = ImageDraw.Draw(lay); rr = random.Random(23)
    for _ in range(70):
        x, y = rr.uniform(30, 1050), rr.uniform(CAB_Y1 + 30, 1580); r = rr.uniform(3, 8)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(120, 112, 100, 230))
    for _ in range(12):
        x, y = rr.uniform(60, 1000), rr.uniform(CAB_Y1 + 40, 1570)
        d.arc([x - 50, y - 16, x + 50, y + 16], rr.uniform(0, 90), rr.uniform(180, 320), fill=(60, 50, 40, 255), width=3)
    sm = layer(); sd = ImageDraw.Draw(sm)
    for x, y in ((250, 1480), (380, 1530), (760, 1460), (880, 1520)):        # footprint smudges
        sd.ellipse([x - 45, y - 26, x + 45, y + 26], fill=(150, 140, 125, 120))
    lay.alpha_composite(sm.filter(ImageFilter.GaussianBlur(10)))
    # crumpled tissue
    d.polygon([(640, 1450), (700, 1430), (740, 1468), (712, 1505), (650, 1498)], fill=(250, 250, 250, 255), outline=INK, width=5)
    d.line([(660, 1462), (700, 1480), (720, 1458)], fill=(200, 205, 210, 255), width=4)
    return lay

# ---------- clutter items (animated off the counter in step 1) ----------
def it_tube(d, x, y):        # toothpaste tube lying on counter
    d.polygon([(x - 90, y - 18), (x + 60, y - 22), (x + 60, y + 22), (x - 90, y + 18)], fill=(255, 255, 255), outline=INK)
    d.line([(x - 90, y - 18), (x + 60, y - 22), (x + 60, y + 22), (x - 90, y + 18), (x - 90, y - 18)], fill=INK, width=5)
    d.rectangle([x - 40, y - 20, x + 10, y + 20], fill=RED)
    rrect(d, [x + 58, y - 12, x + 84, y + 12], 5, fill=ACCENT, outline=INK, width=4)
def it_cup(d, x, y):         # cup with toothbrushes
    d.line([(x - 18, y - 70), (x - 30, y - 150)], fill=BLUE, width=12); d.line([(x + 14, y - 70), (x + 30, y - 145)], fill=(255, 140, 120), width=12)
    rrect(d, [x - 40, y - 155, x - 20, y - 130], 5, fill=(255, 255, 255), outline=INK, width=3)
    rrect(d, [x + 22, y - 150, x + 42, y - 125], 5, fill=(255, 255, 255), outline=INK, width=3)
    d.polygon([(x - 48, y - 80), (x + 48, y - 80), (x + 38, y), (x - 38, y)], fill=(255, 212, 70), outline=INK)
    d.line([(x - 48, y - 80), (x + 48, y - 80), (x + 38, y), (x - 38, y), (x - 48, y - 80)], fill=INK, width=5)
def it_bottle(d, x, y):      # lotion bottle tipped over
    rrect(d, [x - 70, y - 30, x + 60, y + 18], 18, fill=(255, 170, 190), outline=INK, width=5)
    rrect(d, [x + 58, y - 16, x + 90, y + 6], 6, fill=(240, 240, 240), outline=INK, width=4)
def it_core(d, x, y):        # empty toilet-paper tube
    d.rectangle([x - 40, y - 60, x + 40, y], fill=(196, 160, 110), outline=INK, width=5)
    d.ellipse([x - 40, y - 74, x + 40, y - 46], fill=(170, 135, 90), outline=INK, width=5)
    d.ellipse([x - 26, y - 68, x + 26, y - 52], fill=(110, 84, 54))
def it_tissue(d, x, y):
    d.polygon([(x - 40, y), (x - 30, y - 40), (x + 5, y - 52), (x + 40, y - 30), (x + 34, y)], fill=(250, 250, 250), outline=INK)
    d.line([(x - 40, y), (x - 30, y - 40), (x + 5, y - 52), (x + 40, y - 30), (x + 34, y), (x - 40, y)], fill=INK, width=5)

CLUTTER = [(it_tube, 410, 1062), (it_cup, 720, 1075), (it_bottle, 860, 1068), (it_core, 360, 1085), (it_tissue, 640, 1100)]

def draw_clutter(img, t=None, t0=0.25, step=0.17, fly=0.4, target=(1180, 1250)):
    """t=None: all items in place. Otherwise item i flies off toward `target` (a basket off-screen) from t0 + i*step."""
    for i, (fn, x, y) in enumerate(CLUTTER):
        if t is None: p = 0
        else: p = ease_io(seg(t, t0 + i * step, t0 + i * step + fly))
        if p >= 1: continue
        lay = Image.new("RGBA", (400, 400), (0, 0, 0, 0)); fn(ImageDraw.Draw(lay), 200, 260)
        s = 1 - 0.5 * p
        if s != 1: lay = lay.resize((int(400 * s), int(400 * s)), Image.BICUBIC)
        lay = lay.rotate(-40 * p, resample=Image.BICUBIC)
        px = x + (target[0] - x) * p; py = y + (target[1] - y) * p - math.sin(p * math.pi) * 260
        img.alpha_composite(lay, (int(px - lay.width / 2), int(py - 260 * s)))

def tp_roll(img, x, y, p=1.0):
    if p <= 0: return
    lay = Image.new("RGBA", (300, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    rrect(d, [90, 90, 210, 230], 20, fill=(252, 252, 252), outline=INK, width=6)
    d.ellipse([90, 70, 210, 110], fill=(255, 255, 255), outline=INK, width=6)
    d.ellipse([132, 80, 168, 100], fill=(196, 160, 110), outline=INK, width=4)
    d.line([(100, 200), (200, 200)], fill=(225, 230, 232), width=6)
    s = max(0.05, p)
    lay = lay.resize((int(300 * s), int(300 * s)), Image.BICUBIC)
    img.alpha_composite(lay, (int(x - lay.width / 2), int(y - 230 * s)))

def make_bgs():
    clean = draw_room(True); dirty_room = draw_room(False)
    for L in (dirt_mirror(), dirt_sink(), dirt_floor()): dirty_room.alpha_composite(L)
    DIRTYB = to_arr(dirty_room)                              # dirty, no clutter
    dc = dirty_room.copy(); draw_clutter(dc); DIRTY = to_arr(dc)
    CLEANB = to_arr(clean)
    cc = clean.copy(); tp_roll(cc, 820, 1080); CLEAN = to_arr(cc)
    return DIRTYB, DIRTY, CLEANB, CLEAN

DIRTYB, DIRTY, CLEANB, CLEAN = make_bgs()
x0, y0, x1, y1 = MIR
M_MIR = lmask(lambda d: d.rectangle([x0 - 4, y0 - 4, x1 + 4, y1 + 4], fill=255), 2)
M_CT = lmask(lambda d: d.rectangle([60, 940, 1020, CT_Y1 + 4], fill=255), 2) * (1 - M_MIR)
M_FL = lmask(lambda d: d.rectangle([0, CAB_Y1 + 12, W, H], fill=255), 2)
M_TW = lmask(lambda d: d.rectangle([TWL[0] - 4, TWL[1] - 6, TWL[2] + 4, TWL[3] + 4], fill=255), 2)
NOISE = lowfreq(41, 30)

def fb(arr): return to_img(arr)

def zigzag(rows, x0_, x1_, y0_, y1_):
    pts = []
    for i in range(rows):
        y = y0_ + (y1_ - y0_) * i / max(1, rows - 1)
        pts += [(x0_, y), (x1_, y)] if i % 2 == 0 else [(x1_, y), (x0_, y)]
    return pts

# ---------- scenes ----------
TOTAL = 3
HOOK = make_hook(DIRTY, CLEAN, [("GUEST-READY", 150, YELLOW), ("IN 30 MIN", 170, YELLOW)],
                 "BATHROOM IN 3 STEPS", mark_xy=(360, 1045), check_xy=(770, 860), split_to=0.5, labels=True)
HOOK_D = 2.4

SAFETY = make_safety(lambda t: fb(DIRTY), [
    ("ok", "Run the fan or crack a window"),
    ("never", "Never mix bleach with ammonia or acids"),
], title="Safety first", label="BEFORE YOU START")

C1 = make_card(1, "Clear + spray", "Clutter in a basket. Let cleaner sit.", TOTAL)
def x_clear(t, D):
    base = fb(DIRTYB)
    draw_clutter(base, t)
    if t > 1.15:                                           # spray onto the sink, foam stays
        sq = 1.0 if (int(t * 6) % 2 == 0 and t < 2.2) else 0.0
        q = ease(seg(t, 1.15, 1.4))
        spray_bottle(base, 905 + (1 - q) * 300, 1130, s=0.78, squeeze=sq, label="")
        if t < 2.25: mist(base, 760 + (1 - q) * 300, 1016, t, -1, 0.9)
        bubbles(base, t, 1.45, [(450, 1070), (500, 1060), (560, 1080), (610, 1066), (660, 1078), (420, 1082), (530, 1090)], rise=18, rmax=10)
    pill(base, W // 2, PILL_Y, "LET IT SIT 2-3 MIN", F("Bold", 46), ACC2, INK, ease(seg(t, 1.3, 1.6)))
    return base

WIPE = zigzag(5, 290, 800, 690, 950) + [(820, 1070), (260, 1070)]
def x_wipe(t, D):
    t0 = 0.2
    p = ease_io(seg(t, t0, D - 0.4)) * (len(WIPE) - 1)
    m = trail_mask(WIPE, p, radius=95, blur=14) * (M_MIR + M_CT) if t > t0 else 0
    base = fb(blend(DIRTYB, [(CLEANB, m)]))
    if t0 - 0.05 < t < D - 0.3:
        x, y = path_point(WIPE, p)
        towel(base, x, y, ang=math.sin(t * 9) * 8, col=(255, 196, 40), stripe=(255, 226, 140))
    else:
        if t >= D - 0.3: sparkles(base, t, D - 0.3, 0.8, [(330, 720), (720, 780), (520, 900)])
    pill(base, W // 2, PILL_Y, "TOP TO BOTTOM", F("Bold", 46), ACC2, INK, ease(seg(t, 0.25, 0.55)))
    return base
C2 = make_card(2, "Wipe top to bottom", "Spray the cloth, not the mirror.", TOTAL)

MOP = [(110, 1465), (970, 1465), (970, 1530), (110, 1530)]
def x_floor(t, D):
    p = ease_io(seg(t, 0.1, 1.75)) * (len(MOP) - 1)
    m = trail_mask(MOP, p, radius=115, blur=16) * M_FL
    k = dissolve(ease(seg(t, 1.2, 1.9)), NOISE) * M_TW
    base = fb(blend(DIRTYB, [(CLEANB, M_MIR + M_CT), (CLEANB, m), (CLEANB, k)]))
    if t < 1.9:
        x, y = path_point(MOP, p)
        flat_mop(base, x, y, handle_to=(x + 260, 1180), wobble=math.sin(t * 9))
    tp_roll(base, 820, 1080, back(seg(t, 1.6, 2.0)))
    if t > 2.0: sparkles(base, t, 2.0, 0.7, [(975, 800), (820, 960), (300, 1470), (700, 1500)])
    pill(base, W // 2, PILL_Y, "SPARE ROLL IN SIGHT", F("Bold", 46), ACC2, INK, ease(seg(t, 1.6, 1.9)))
    return base
C3 = make_card(3, "Floor + fresh towel", "New hand towel + a spare roll.", TOTAL)

SP = [(330, 720), (720, 800), (540, 1070), (975, 820), (300, 1480), (820, 1520), (820, 1000)]
_BA = make_ba(DIRTY, CLEAN, y_label=SAFE_TOP + 120, handle_y=1250, spark_pts=SP)
def BA(t, D): return _BA(t, D)
BA.impact_at = _BA.impact_at

_OUT = make_loop_outro(CLEAN, HOOK(0.0, HOOK_D), ask="Hosting this year?")
def OUTRO(t, D): return _OUT(t, D)

SCENES = [
    ("01_hook", HOOK, HOOK_D),
    ("02_safety", SAFETY, 2.3),
    ("03_clear", with_card(C1, x_clear), 2.7),
    ("04_wipe", with_card(C2, x_wipe), 2.7),
    ("05_floor", with_card(C3, x_floor), 2.6),
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
