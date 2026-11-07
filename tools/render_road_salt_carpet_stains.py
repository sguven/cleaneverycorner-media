"""2026-11-07 — Remove road salt stains from car carpets (car). Uses lib/engine.py + lib/music_upbeat.py.
python3 tools/render_road_salt_carpet_stains.py stills|render WORKDIR OUT_MP4
"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.engine import *
from lib.music_upbeat import make_track

# ---------- car floor carpet backgrounds ----------
SILL = 120                                            # door sill strip on the left
STAINS = [(330, 1230, 210), (690, 1060, 190), (560, 1460, 170), (850, 1380, 150), (420, 860, 150)]

def make_bgs():
    rng = np.random.default_rng(11)
    fine = rng.normal(0, 1, (H, W // 2)).astype(np.float32)
    fine = np.array(Image.fromarray(((fine * 40) + 128).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32) / 128 - 1
    grain = rng.normal(0, 1, (H, W)).astype(np.float32)
    low = lowfreq(3, 50)
    base = np.array([60, 63, 70], np.float32) + (fine * 12 + grain * 5 + (low - 0.5) * 14)[..., None]
    base *= (1.0 - 0.16 * np.abs(YF - 1100) / 1100)[..., None]
    # door sill strip
    sill = (XF < SILL).astype(np.float32)
    ridge = ((YF % 44) < 8).astype(np.float32) * (XF > 22) * (XF < SILL - 20)
    sill_col = np.array([34, 36, 42], np.float32) + (ridge * 26)[..., None]
    edge = np.clip(1 - np.abs(XF - SILL) / 5, 0, 1)
    base = base * (1 - sill[..., None]) + sill_col * sill[..., None]
    base += edge[..., None] * 60

    stripes = np.tanh(3 * np.sin((XF + YF * 0.35) / 75)) * (1 - sill)
    clean = base + stripes[..., None] * 7 + 4 * (1 - sill[..., None])

    # salt: irregular tide-line rings, crusty fill and loose crystals
    ring = np.zeros((H, W), np.float32); crust = np.zeros((H, W), np.float32)
    wob = lowfreq(17, 90) - 0.5; tex = lowfreq(23, 14)
    for cx, cy, r in STAINS:
        dk = np.sqrt((XF - cx) ** 2 + ((YF - cy) * 1.15) ** 2) / r + wob * 0.55
        ring = np.maximum(ring, np.clip(1 - np.abs(dk - 1) / 0.045, 0, 1))
        ring = np.maximum(ring, 0.55 * np.clip(1 - np.abs(dk - 0.72) / 0.03, 0, 1))
        crust = np.maximum(crust, np.clip((1.02 - dk) * 3, 0, 1) * (0.35 + 0.65 * tex))
    ring *= (1 - sill); crust *= (1 - sill)
    ring = np.array(Image.fromarray((ring * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.5))).astype(np.float32) / 255
    k = Image.new("L", (W, H), 0); kd = ImageDraw.Draw(k); rr = random.Random(5)
    for cx, cy, r in STAINS:
        for _ in range(int(r * 1.6)):
            a = rr.uniform(0, 6.283); d = r * rr.random() ** 0.6
            x, y = cx + math.cos(a) * d, cy + math.sin(a) * d / 1.15; s = rr.randint(2, 6)
            if x > SILL + 10: kd.ellipse([x - s, y - s, x + s, y + s], fill=255)
    cryst = np.array(k.filter(ImageFilter.GaussianBlur(0.8))).astype(np.float32) / 255
    WHITE = np.array([228, 226, 218], np.float32)

    def salted(b, a): return b * (1 - a[..., None]) + WHITE * a[..., None]
    dirty = salted(base, np.maximum.reduce([ring * 0.85, crust * 0.42, cryst * 0.95]))
    stain = salted(base, np.maximum(ring * 0.7, crust * 0.2))           # after vacuuming loose salt
    wetb = base * 0.72 * (1 - sill[..., None]) + base * sill[..., None]
    wet = salted(wetb, np.maximum(ring * 0.42, crust * 0.1))             # sprayed
    scrubbed = salted(wetb, ring * 0.12)                                 # scrubbed, salt dissolved
    damp = base * (0.86 * (1 - sill) + sill)[..., None]                  # blotted, still damp
    return dirty, clean, stain, wet, scrubbed, damp

DIRTY, CLEAN, STAIN, WET, SCRUB, DAMP = make_bgs()
N1, N2 = lowfreq(41, 40), lowfreq(57, 30)
CRYST_PTS = [(cx + math.cos(i * 2.4) * r * 0.6 * (i % 3 + 1) / 3, cy + math.sin(i * 2.4) * r * 0.5 * (i % 3 + 1) / 3)
             for cx, cy, r in STAINS for i in range(6)]

# ---------- props ----------
def drop(d, cx, cy, s, col):
    d.ellipse([cx - s, cy - s * 0.6, cx + s, cy + s * 1.2], fill=col)
    d.polygon([(cx - s * 0.75, cy), (cx, cy - s * 1.5), (cx + s * 0.75, cy)], fill=col)

def jug(img, x, y, label, col):
    d = ImageDraw.Draw(img)
    rrect(d, [x - 80, y - 120, x + 80, y + 130], 34, fill=col, outline=INK, width=8)
    rrect(d, [x - 30, y - 165, x + 30, y - 115], 10, fill=(255, 255, 255), outline=INK, width=7)
    rrect(d, [x - 62, y - 30, x + 62, y + 50], 12, fill=(255, 255, 255))
    f = F("Bold", 30)
    while f.getlength(label) > 112: f = F("Bold", f.size - 2)
    d.text((x, y + 10), label, font=f, fill=INK, anchor="mm")

# ---------- scenes ----------
TOTAL = 6
HOOK = make_hook(DIRTY, CLEAN,
                 [("ROAD SALT STAINS?", 96, (255, 255, 255)), ("THEY COME", 165, YELLOW), ("RIGHT OUT", 165, YELLOW)],
                 "VINEGAR + WATER  ·  6 STEPS", mark_xy=(330, 1230), check_xy=(800, 1230))

SAFETY = make_safety(DIRTY, [
    ("ok", "Test on a hidden spot first"),
    ("ok", "Gloves on, doors open for airflow"),
    ("no", "Don't soak the carpet (mold risk)"),
    ("no", "Keep spray off screens, switches and wiring"),
    ("never", "NEVER mix vinegar with bleach"),
])

C1 = make_card(1, "Vacuum first", "Loosen the crust with a stiff brush, then vacuum up the dry salt", TOTAL)
def x_vac(t, D):
    p = ease_io(seg(t, 0.3, D - 0.4))
    edge = -150 + p * (W + 300)
    m = np.clip((edge - XF) / 150, 0, 1)
    base = to_img(blend(DIRTY, [(STAIN, m)]))
    if 0.25 < t < D - 0.3:
        vy = 1250 + math.sin(t * 7) * 230
        vac_nozzle(base, edge, vy, wand_to=(edge + 600, -100))
    return base

C2 = make_card(2, "Mix 1:1", "Equal parts white vinegar and warm water in a spray bottle", TOTAL)
def x_mix(t, D):
    base = to_img(STAIN); dim(base, 80)
    soft_disc(base, W // 2, 1230, 300, 55)
    d = ImageDraw.Draw(base)
    pj = back(seg(t, 0.2, 0.6))
    if pj > 0:
        jug(base, int(200 + (1 - pj) * -250), 1000, "VINEGAR", (240, 236, 220))
        jug(base, int(880 + (1 - pj) * 250), 1000, "WARM H2O", (150, 210, 240))
    for k in range(4):                                 # alternating pours into the bottle
        tt = t - (0.8 + k * 0.4)
        if 0 <= tt < 0.4:
            src = 300 if k % 2 == 0 else 780
            x = src + (W // 2 - src) * tt / 0.4
            drop(d, x, 900 + tt / 0.4 * 260, 24, (238, 234, 214) if k % 2 == 0 else (120, 190, 240))
    sp = back(seg(t, 0.4, 0.8))
    if sp > 0: spray_bottle(base, W // 2, int(1240 + (1 - sp) * 400), 1.05, 0, "1 : 1", liquid=(190, 220, 236))
    fb = F("Bold", 42)
    pill(base, 280, 1600, "1 part vinegar", fb, ACC2, INK, ease(seg(t, 0.9, 1.2)))
    pill(base, 800, 1600, "1 part water", fb, BLUE, (255, 255, 255), ease(seg(t, 1.3, 1.6)))
    return base

C3 = make_card(3, "Mist and wait", "Spray just enough to dampen it. Let it sit 1 minute.", TOTAL)
def x_spray(t, D):
    p = ease_io(seg(t, 0.3, 2.3))
    sx = W + 60 - p * (W - 120)
    m = np.clip((XF - sx + 60) / 160, 0, 1) * (XF > SILL)
    base = to_img(blend(STAIN, [(WET, m)]))
    if 0.25 < t < 2.4:
        sy = 1150 + math.sin(t * 5) * 140
        sq = 1.0 if int(t * 6) % 2 == 0 else 0.0
        nx, ny = spray_bottle(base, sx + 200, sy - 120, 0.85, sq, "1 : 1", liquid=(190, 220, 236))
        mist(base, nx, ny, t, -1, 1.0, col=(220, 235, 250))
    q = back(seg(t, 2.3, 2.7))
    if q > 0: pill(base, W // 2, 1300, "WAIT 1 MIN", F("Bold", int(64 * max(q, 0.3))), ACC2, INK, min(1, q))
    return base

C4 = make_card(4, "Scrub gently", "Short, light strokes lift the salt. Don't grind it in.", TOTAL)
def x_scrub(t, D):
    p = ease_io(seg(t, 0.3, D - 0.4))
    base = to_img(blend(WET, [(SCRUB, dissolve(p, N1))]))
    if t > 0.3: bubbles(base, t, 0.3, CRYST_PTS, col=(255, 255, 255), rise=18, rmax=12, speed=2.0)
    if 0.25 < t < D - 0.25:
        k = int(t / 0.85) % len(STAINS)
        cx, cy, r = STAINS[k]
        scrub_brush(base, cx + math.sin(t * 22) * 70, cy + math.cos(t * 3) * 30, ang=math.sin(t * 22) * 8)
    return base

C5 = make_card(5, "Blot it dry", "Press with a dry towel or pull it out with a wet/dry vac", TOTAL)
PRESS = [(330, 1230), (690, 1080), (560, 1440), (860, 1380), (420, 880)]
def x_blot(t, D):
    m = np.zeros((H, W), np.float32)
    dt = (D - 0.8) / len(PRESS)
    for i, (px, py) in enumerate(PRESS):
        q = ease(seg(t, 0.3 + i * dt + 0.15, 0.3 + (i + 1) * dt))
        if q > 0: m = np.maximum(m, np.clip((290 * q - np.sqrt((XF - px) ** 2 + (YF - py) ** 2)) / 60, 0, 1))
    m = np.maximum(m, dissolve(seg(t, D - 0.8, D - 0.2), N2))
    base = to_img(blend(SCRUB, [(DAMP, m)]))
    i = int(clamp((t - 0.3) / dt, 0, len(PRESS) - 1))
    if 0.3 < t < D - 0.4:
        ph = ((t - 0.3) % dt) / dt
        px, py = PRESS[i]
        lift = abs(math.cos(ph * math.pi)) * 90
        towel(base, px, py - lift, ang=-8 + 16 * ph, col=(120, 200, 230), stripe=(190, 230, 245))
    return base

C6 = make_card(6, "Dry it fully", "Doors open or a fan on. Repeat if white rings come back.", TOTAL)
def x_dry(t, D):
    p = ease_io(seg(t, 0.4, D - 0.6))
    edge = -200 + p * (W + 400)
    m = np.clip((edge - XF + 100 * (N2 - 0.5)) / 200, 0, 1)
    base = to_img(blend(DAMP, [(CLEAN, m)]))
    fan(base, 230, 1230, 140, t * 900)
    airflow(base, t, 380, W, [1100, 1180, 1260, 1340, 1420], speed=1100)
    if t > D - 0.9: sparkles(base, t, D - 0.9)
    return base

BA = make_ba(DIRTY, CLEAN, y_label=720, handle_y=1100)
OUTRO = make_outro(CLEAN)

SCENES = [
    ("01_hook", HOOK, 3.3),
    ("02_safety", SAFETY, 5.2),
    ("03_vacuum", with_card(C1, x_vac), 3.4),
    ("04_mix", with_card(C2, x_mix), 3.4),
    ("05_spray", with_card(C3, x_spray), 3.6),
    ("06_scrub", with_card(C4, x_scrub), 3.4),
    ("07_blot", with_card(C5, x_blot), 3.6),
    ("08_dry", with_card(C6, x_dry), 3.6),
    ("09_ba", BA, 4.0),
    ("10_outro", OUTRO, 3.4),
]

def music(dur, cuts, impacts, path): make_track(dur, cuts, impacts, path, bpm=122, seed=7)

if __name__ == "__main__":
    mode, work = sys.argv[1], sys.argv[2]
    if mode == "stills":
        only = sys.argv[3].split(",") if len(sys.argv) > 3 else None
        print("\n".join(stills(SCENES, os.path.join(work, "stills"), (0.15, 0.55, 0.95), only)))
    else:
        print("total", build(SCENES, work, sys.argv[3], music))
