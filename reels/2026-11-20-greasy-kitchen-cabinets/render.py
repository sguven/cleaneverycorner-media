"""2026-11-20 — Remove grease from kitchen cabinets (home). lib/engine.py + lib/music_upbeat.py (clean style, upbeat=True).
Hook (contrarian): "THAT'S NOT DIRT. IT'S GREASE." -> split screen greasy wood door | clean wood door, pill "WAIT FOR IT".
    python3 render.py stills [scene,scene] [fracs]      -> stills/*.jpg
    python3 render.py render                            -> greasy-kitchen-cabinets.mp4 (+ work/)
Sources checked: Family Handyman "How to clean sticky grease off kitchen cabinets" (squirt of dish soap in warm water,
soft side of sponge only, rinse with a clean damp cloth; stubborn spots: let cleaner sit ~1 min, old toothbrush; test
vinegar/baking soda on exteriors first), Bob Vila "How to remove grease from kitchen cabinets" (few drops of dish soap,
not dishwasher detergent; sponge not dripping wet; test in an inconspicuous spot; dry thoroughly - leftover moisture can
get into the finish), Apartment Therapy 5-method test (warm water + dish soap won; vinegar soak weakest).
"""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from lib.engine import *
from lib.music_upbeat import make_track
from lib.music_styles import pick_style

SLUG = "2026-11-20-greasy-kitchen-cabinets"
NAME = "greasy-kitchen-cabinets"
PILL_Y = 1515
SL, SR = 230, 850            # recessed panel between the stiles (x)
RT, RB = 300, 1760           # recessed panel between the rails (y)
KNOB = (118, 1080)

def lmask(draw_fn, blur=2):
    m = Image.new("L", (W, H), 0); draw_fn(ImageDraw.Draw(m))
    m = m.filter(ImageFilter.GaussianBlur(blur)) if blur else m
    return np.array(m).astype(np.float32) / 255

def make_bgs():
    rng = np.random.default_rng(1120)
    # ---- wood grain: vertical on stiles + panel, horizontal on rails ----
    wob = lowfreq(5, 140) * 60 + lowfreq(6, 30) * 14
    gv = 0.5 + 0.5 * np.sin((XF + wob) / 7.5) * (0.6 + 0.4 * np.sin((XF + wob * 2) / 41))
    gh = 0.5 + 0.5 * np.sin((YF + wob) / 7.5) * (0.6 + 0.4 * np.sin((YF + wob * 2) / 41))
    rail = ((YF < RT - 40) | (YF > RB + 40)) & (XF > SL - 40) & (XF < SR + 40)
    g = np.where(rail, gh, gv)
    tone = 0.88 + 0.16 * lowfreq(9, 90)
    shade = np.ones((H, W), np.float32)
    # panel bevel: a 40 px frame around the recessed panel, light from top-left
    inb = (XF > SL - 40) & (XF < SR + 40) & (YF > RT - 40) & (YF < RB + 40)
    pan = (XF > SL) & (XF < SR) & (YF > RT) & (YF < RB)
    bev = inb & ~pan
    left = bev & (XF <= SL); top = bev & (YF <= RT); right = bev & (XF >= SR); bot = bev & (YF >= RB)
    shade = np.where(left | top, 0.72, shade); shade = np.where(right | bot, 1.12, shade)
    shade = np.where(pan, 0.96 - 0.05 * (YF - RT) / (RB - RT), shade)
    shade *= 1 - 0.10 * ((XF - W / 2) / (W / 2)) ** 2
    shade = np.array(Image.fromarray(np.clip(shade * 200, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2))).astype(np.float32) / 200
    base_col = np.array([206, 150, 92], np.float32)              # honey oak
    wood = base_col * (tone * (0.86 + 0.18 * g) * shade)[..., None]
    # door edges: dark gaps at the very left/right (neighbour doors)
    gap = lmask(lambda d: [d.rectangle([0, 0, 10, H], fill=255), d.rectangle([W - 10, 0, W, H], fill=255)], 3)
    wood = blend(wood, [(np.zeros_like(wood) + np.array([40, 26, 16]), gap)])
    # ---- CLEAN: warm satin sheen ----
    sheen = np.exp(-((XF - YF * 0.35 - 420) / 120) ** 2) * 0.35 + np.exp(-((XF - YF * 0.35 + 60) / 60) ** 2) * 0.22
    clean = blend(wood * 1.04 + 4, [(np.zeros_like(wood) + np.array([255, 236, 205]), np.clip(sheen, 0, 1))])
    # ---- WET (after rinse, before drying): darker damp streaks along the grain ----
    streak = np.clip((lowfreq(71, 18)[..., ] - 0.45) * 3, 0, 1) * np.clip(np.sin(XF / 55 + lowfreq(72, 120) * 4) * 1.4, 0, 1)
    wet = blend(clean, [(clean * 0.80, streak * 0.6), (np.zeros_like(wood) + np.array([255, 250, 240]), np.clip(streak - 0.75, 0, 1) * 0.9)])
    # ---- grease field: heavy near the knob + top edge (rising cooking vapour), drips, fingerprints ----
    gf = lowfreq(31, 120) * 0.55 + lowfreq(32, 40) * 0.2
    gf += np.exp(-(((XF - KNOB[0]) ** 2) / 260 ** 2 + ((YF - KNOB[1]) ** 2) / 420 ** 2)) * 0.65
    gf += np.clip(1 - YF / 900, 0, 1) * 0.35
    gf += np.exp(-(((XF - 360) ** 2) + (YF - 1180) ** 2) / 170 ** 2) * 0.55      # the marked splatter zone
    film = np.clip((gf - 0.30) / 0.45, 0, 1) ** 0.8
    edge = np.clip(1 - np.abs(gf - 0.55) / 0.03, 0, 1)                             # darker sticky rim of the film
    drips = lmask(lambda d: [d.line([(x, y0), (x + random.Random(x).uniform(-6, 6), y0 + ln)], fill=255, width=int(w * 1.6))
                             for x, y0, ln, w in [(330, 520, 380, 16), (560, 430, 520, 12), (760, 600, 300, 18), (430, 900, 460, 12),
                                                 (690, 1050, 380, 14), (300, 1300, 300, 12), (520, 1450, 260, 16), (380, 1100, 330, 20), (250, 1150, 240, 14)]], 4)
    tips = lmask(lambda d: [d.ellipse([x - w * 1.5, y0 + ln - w * 1.4, x + w * 1.5, y0 + ln + w * 1.9], fill=255)
                            for x, y0, ln, w in [(330, 520, 380, 13), (560, 430, 520, 10), (760, 600, 300, 15), (430, 900, 460, 10),
                                                (690, 1050, 380, 12), (300, 1300, 300, 10), (520, 1450, 260, 13), (380, 1100, 330, 17), (250, 1150, 240, 12)]], 2)
    prints = lmask(lambda d: [d.ellipse([KNOB[0] + dx - 34, KNOB[1] + dy - 46, KNOB[0] + dx + 34, KNOB[1] + dy + 46], fill=255)
                              for dx, dy in [(70, -120), (95, -40), (100, 60), (60, 150), (150, -10), (20, 230), (140, 120)]], 6)
    ridges = 0.5 + 0.5 * np.sin(((XF - KNOB[0]) ** 2 + (YF - KNOB[1]) ** 2) ** 0.5 / 4.0)
    speck = (rng.random((H, W)).astype(np.float32) > 0.975).astype(np.float32)
    speck = np.array(Image.fromarray((speck * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255
    amber = np.array([96, 56, 14], np.float32)
    dull = wood * 0.74 + np.array([10, 8, 0])
    grease_m = np.clip(film * 0.80 + edge * 0.5 + drips * 0.75 + tips * 0.85 + prints * (0.45 + 0.35 * ridges), 0, 0.92)
    hl = lmask(lambda d: [d.line([(x - w * 0.35, y0 + 10), (x - w * 0.35, y0 + ln - 10)], fill=255, width=max(3, w // 5))
                          for x, y0, ln, w in [(330, 520, 380, 16), (560, 430, 520, 12), (760, 600, 300, 18), (430, 900, 460, 12),
                                              (690, 1050, 380, 14), (300, 1300, 300, 12), (520, 1450, 260, 16), (380, 1100, 330, 20), (250, 1150, 240, 14)]]
                          + [d.ellipse([x - w * 0.6, y0 + ln - w * 0.5, x - w * 0.1, y0 + ln], fill=255)
                             for x, y0, ln, w in [(330, 520, 380, 13), (560, 430, 520, 10), (760, 600, 300, 15), (380, 1100, 330, 17), (250, 1150, 240, 12)]], 1.5)
    gloss = np.clip(film - 0.5, 0, 1) * np.clip(np.sin((XF * 0.6 + YF) / 90 + lowfreq(77, 80) * 5) - 0.6, 0, 1) * 2.5
    dirty = blend(dull, [(dull * 0.35 + amber * 0.65, grease_m),
                         (np.zeros_like(wood) + np.array([255, 226, 160]), np.clip(gloss, 0, 1) * 0.35),
                         (np.zeros_like(wood) + np.array([74, 40, 8]), np.clip(drips * 0.55 + tips * 0.7, 0, 0.75)),
                         (np.zeros_like(wood) + np.array([255, 236, 190]), hl * 0.5),
                         (np.zeros_like(wood) + np.array([70, 62, 52]), speck * np.clip(film + 0.3, 0, 1) * 0.95)])
    # MOSTLY: after soap wipe - only the stubborn ring around the knob is left (plus slight wetness)
    stub = np.clip(prints * 1.2 + np.exp(-(((XF - KNOB[0] - 80) ** 2) + (YF - KNOB[1]) ** 2) / 170 ** 2) * 0.9, 0, 1)
    mostly = blend(wet, [(dirty, stub)])
    return dirty, mostly, wet, clean, stub

DIRTY, MOSTLY, WET, CLEAN, STUB = make_bgs()
def fb(arr): return to_img(arr)

def knob(img, x=KNOB[0], y=KNOB[1], greasy=0.0):
    d = ImageDraw.Draw(img)
    d.ellipse([x - 44, y - 44, x + 50, y + 50], fill=(30, 22, 14, 120))               # shadow
    c = tuple(int(a * (1 - greasy) + b * greasy) for a, b in zip((214, 216, 220), (150, 128, 90)))
    d.ellipse([x - 46, y - 46, x + 46, y + 46], fill=c, outline=INK, width=6)
    d.ellipse([x - 22, y - 30, x + 6, y - 8], fill=(255, 255, 255, int(220 * (1 - greasy * 0.7))))

def vstrokes(cols, y0=420, y1=1700):
    pts = []
    for i, x in enumerate(cols): pts += [(x, y0), (x, y1)] if i % 2 == 0 else [(x, y1), (x, y0)]
    return pts

def bg_with_knob(arr, greasy):
    def f(t):
        im = fb(arr); knob(im, greasy=greasy); return im
    return f

# ---------- scenes ----------
TOTAL = 3
def hook_extra(base, t, D, sx):
    knob(base, greasy=1.0)          # knob sits on the greasy (left) side
HOOK = make_hook(DIRTY, CLEAN, [("THAT'S NOT DIRT.", 140, YELLOW), ("IT'S GREASE.", 170, YELLOW)],
                 "WAIT FOR IT", mark_xy=(360, 1180), check_xy=(830, 1090), split_to=0.5, labels=True, extra=hook_extra)
HOOK_D = 2.2

SAFETY = make_safety(bg_with_knob(DIRTY, 1.0), [
    ("ok", "Test a hidden spot first"),
    ("never", "Never mix cleaners"),
], title="Safety first", label="BEFORE YOU START")

# step 1: warm soapy sponge, wrung out, wipes with the grain
SP_PATH = vstrokes([300, 440, 580, 720, 860, 1000, 160])
C1 = make_card(1, "Dish soap + warm water", "A few drops. Sponge damp, not dripping.", TOTAL)
FOAM1 = [(x, y) for y in range(460, 1700, 110) for x in range(120, 1040, 120)]
def x_soap(t, D):
    t0 = 0.2
    p = ease_io(seg(t, t0, D - 0.2)) * (len(SP_PATH) - 1)
    m = trail_mask(SP_PATH, p, radius=105, blur=16) if t > t0 else 0
    base = fb(blend(DIRTY, [(MOSTLY, m)]))
    knob(base, greasy=0.8)
    if t > t0 - 0.05:
        x, y = path_point(SP_PATH, p)
        bubbles(base, t, t0, [(fx, fy) for fx, fy in FOAM1 if abs(fx - x) < 150 and abs(fy - y) < 260], rise=26, rmax=10, speed=2.2)
        sponge(base, x, y, ang=90 + math.sin(t * 30) * 5)
    pill(base, W // 2, PILL_Y, "WIPE WITH THE GRAIN", F("Bold", 46), ACC2, INK, ease(seg(t, 0.3, 0.6)))
    return base

# step 2: stubborn ring by the knob - let it sit a minute, soft toothbrush
C2 = make_card(2, "Stubborn spot? Wait 1 min", "Then a soft toothbrush. Soft side only.", TOTAL)
BR = [(KNOB[0] + 90 + 70 * math.cos(k * 0.9), KNOB[1] + 150 * math.sin(k * 0.45)) for k in range(24)]
def x_brush(t, D):
    t0 = 0.35
    p = ease_io(seg(t, t0, D - 0.25))
    m = STUB * p
    base = fb(blend(MOSTLY, [(WET, m)]))
    knob(base, greasy=0.8 * (1 - p))
    if t < t0:
        ring(ImageDraw.Draw(base), KNOB[0] + 90, KNOB[1], 150, ease(seg(t, 0.0, t0)))
    else:
        x, y = path_point(BR, p * (len(BR) - 1))
        bubbles(base, t, t0, [(KNOB[0] + 60 + 40 * (i % 3), KNOB[1] - 160 + 70 * i) for i in range(6)], rise=22, rmax=9, speed=2.6)
        detail_brush(base, x + math.sin(t * 40) * 10, y, ang=-30 + math.sin(t * 40) * 6, col=ACCENT)
    pill(base, W // 2, PILL_Y, "NO SCOURING PADS", F("Bold", 46), ACC2, INK, ease(seg(t, 0.3, 0.6)))
    return base

# step 3: rinse with a clean damp cloth, then dry right away
TW_PATH = vstrokes([180, 360, 540, 720, 900], 440, 1700)
C3 = make_card(3, "Rinse, then dry fast", "Water left behind can dull the finish.", TOTAL)
SP3 = [(300, 900), (640, 860), (860, 1000), (420, 1250), (760, 1300), (560, 1100)]
def x_dry(t, D):
    t0 = 0.15
    p = ease_io(seg(t, t0, D - 0.55)) * (len(TW_PATH) - 1)
    m = trail_mask(TW_PATH, p, radius=130, blur=22) if t > t0 else 0
    base = fb(blend(WET, [(CLEAN, m)]))
    knob(base, greasy=0.0)
    if t < D - 0.5:
        x, y = path_point(TW_PATH, p)
        towel(base, x, y, ang=math.sin(t * 10) * 8, col=(120, 190, 240), stripe=(190, 225, 250))
    else:
        sparkles(base, t, D - 0.5, 1.0, SP3)
    pill(base, W // 2, PILL_Y, "DRY WITH MICROFIBER", F("Bold", 46), ACC2, INK, ease(seg(t, 0.3, 0.6)))
    return base

SP = [(260, 900), (620, 860), (880, 1000), (430, 1300), (760, 1250), (560, 1120), (900, 1400)]
_BA = make_ba(DIRTY, CLEAN, y_label=SAFE_TOP + 120, handle_y=1240, spark_pts=SP)
def BA(t, D):
    im = _BA(t, D)
    split = W - ease_io(seg(t, 0.4, 2.2)) * W * 0.5
    knob(im, greasy=1.0 if KNOB[0] < split else 0.0)
    return im
BA.impact_at = _BA.impact_at

_OUT = make_loop_outro(CLEAN, HOOK(0.0, HOOK_D), ask="Wood or painted cabinets?")
def OUTRO(t, D): return _OUT(t, D)

SCENES = [
    ("01_hook", HOOK, HOOK_D),
    ("02_safety", SAFETY, 2.0),
    ("03_soap", with_card(C1, x_soap), 2.6),
    ("04_brush", with_card(C2, x_brush), 2.4),
    ("05_dry", with_card(C3, x_dry), 2.4),
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
