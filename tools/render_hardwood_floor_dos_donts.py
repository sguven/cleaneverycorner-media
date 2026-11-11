"""2026-11-11 — Hardwood floors: do's and don'ts (home). Uses lib/engine.py + lib/music_upbeat.py (+ style rotation).
python3 tools/render_hardwood_floor_dos_donts.py stills|render WORKDIR [OUT_MP4]
"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.engine import *
from lib.music_upbeat import make_track
from lib.music_styles import pick_style

SLUG = "2026-11-11-hardwood-floor-dos-donts"
PW, PL = 180, 900                          # plank width / length (boards run vertically = grain direction)
PUD_MARK = (270, 1130)                      # puddle ringed in the hook
SPILL = (560, 1180)                         # spill blotted in step 4

def blobs(mask_draw, cx, cy, r, rr, n=7, fill=255):
    for _ in range(n):
        a, k = rr.uniform(0, 6.28), rr.uniform(0.2, 0.75)
        x, y = cx + math.cos(a) * r * k, cy + math.sin(a) * r * k * 0.7
        s = r * rr.uniform(0.45, 0.8)
        mask_draw.ellipse([x - s, y - s * 0.7, x + s, y + s * 0.7], fill=fill)

def puddle_mask(spots, seed):
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m); rr = random.Random(seed)
    for cx, cy, r in spots: blobs(d, cx, cy, r, rr)
    m = m.filter(ImageFilter.GaussianBlur(14)).point(lambda v: 255 if v > 120 else 0).filter(ImageFilter.GaussianBlur(2))
    return np.array(m).astype(np.float32) / 255

def make_bgs():
    rng = np.random.default_rng(11); rr = random.Random(11)
    grain = rng.normal(0, 1, (H, W)).astype(np.float32)
    pid = (XF // PW).astype(int)
    offs = np.array([rr.uniform(0, PL) for _ in range(W // PW + 1)], np.float32)
    segi = np.floor((YF - offs[pid]) / PL).astype(int)
    seg_rand = ((pid * 73 + segi * 151) % 97) / 97.0
    small = rng.random((H // 260 + 3, W // 10 + 3)).astype(np.float32)
    n1 = np.array(Image.fromarray((small * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)).astype(np.float32) / 255
    g = 0.5 + 0.5 * np.sin((XF * 1.0 + n1 * 70 + seg_rand * 400) / 4.5)
    g2 = 0.5 + 0.5 * np.sin((XF * 0.37 + n1 * 40 + seg_rand * 900) / 9.0)
    base = np.array([186, 124, 72], np.float32)[None, None, :] * np.ones((H, W, 1), np.float32)
    base += ((seg_rand - 0.5) * 34)[..., None] * np.array([1.0, 0.8, 0.6], np.float32)
    base -= (g ** 3 * 18 + g2 * 10)[..., None] * np.array([1.0, 0.85, 0.7], np.float32)
    base += ((lowfreq(3, 90) - 0.5) * 12 + grain * 2.0)[..., None]
    seam_v = (np.abs(XF - (pid * PW)) < 2.2)
    seam_h = (np.abs((YF - offs[pid]) % PL) < 2.2)
    seams = (seam_v | seam_h).astype(np.float32)
    base = blend(base, [(np.array([70, 42, 24], np.float32) * np.ones((H, W, 1), np.float32), seams * 0.85)])
    # clean: glossy finish with a soft window reflection
    win = Image.new("L", (W, H), 0); wd = ImageDraw.Draw(win)
    for x0 in (110, 330):
        wd.rectangle([x0, 330, x0 + 190, 1000], fill=255)
    win = np.array(win.filter(ImageFilter.GaussianBlur(40))).astype(np.float32) / 255
    sheen = np.clip(1 - YF / 1900, 0, 1) * 0.25
    clean = base + (win * 60 + sheen * 40)[..., None] * np.array([1.0, 0.95, 0.85], np.float32)
    # dull: grey film, patchy
    patch = 0.30 + 0.20 * lowfreq(21, 80)
    dull = blend(base, [(np.array([172, 156, 140], np.float32) * np.ones((H, W, 1), np.float32), patch)])
    # footprints
    fp = Image.new("L", (W, H), 0); fd = ImageDraw.Draw(fp)
    for i in range(7):
        x = 160 + i * 130 + (40 if i % 2 else -40); y = 1480 - i * 170
        fd.ellipse([x - 40, y - 70, x + 40, y + 30], fill=150)
        fd.ellipse([x - 32, y + 50, x + 32, y + 110], fill=150)
        for k in range(4): fd.line([(x - 34, y - 50 + k * 22), (x + 34, y - 50 + k * 22)], fill=60, width=6)
    fpm = np.array(fp.filter(ImageFilter.GaussianBlur(4))).astype(np.float32) / 255
    dull = blend(dull, [(np.array([110, 92, 76], np.float32) * np.ones((H, W, 1), np.float32), fpm * 0.6)])
    # dust, crumbs, hair
    ds = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(ds)
    for _ in range(1100):
        x, y, s = rr.uniform(0, W), rr.uniform(0, H), rr.uniform(1.5, 4)
        dd.ellipse([x - s, y - s, x + s, y + s], fill=(225, 220, 210, rr.randint(150, 240)))
    for _ in range(70):
        x, y, s = rr.uniform(20, W - 20), rr.uniform(300, H - 100), rr.uniform(5, 12)
        pts = [(x + math.cos(a) * s * rr.uniform(0.6, 1.2), y + math.sin(a) * s * rr.uniform(0.6, 1.2)) for a in np.linspace(0, 6.2, 7)]
        dd.polygon(pts, fill=rr.choice([(214, 170, 90, 255), (150, 100, 60, 255), (240, 214, 150, 255)]), outline=(90, 60, 40, 255))
    for _ in range(10):
        x, y = rr.uniform(60, W - 60), rr.uniform(400, H - 200)
        pts = [(x + k * 9, y + math.sin(k / 3 + x) * 14) for k in range(16)]
        dd.line(pts, fill=(60, 50, 44, 200), width=3, joint="curve")
    dust_img = ds
    a = np.array(dust_img).astype(np.float32)
    dmask = a[..., 3] / 255; dcol = a[..., :3]
    dull_dirty = blend(dull, [(dcol, dmask)])
    # puddles (hook / before only)
    pm = puddle_mask([(PUD_MARK[0], PUD_MARK[1], 120), (760, 1380, 95), (380, 1560, 80), (880, 860, 70)], 5)
    wetwood = dull * 0.78 + np.array([30, 40, 50], np.float32) * 0.1
    edge = np.clip(pm - np.array(Image.fromarray((pm * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(9))).astype(np.float32) / 255, 0, 1) * 3
    dirty = blend(dull_dirty, [(wetwood, pm), (np.full((H, W, 3), 245, np.float32), np.clip(edge, 0, 1) * 0.8)])
    # damp: clean but with mop-stroke sheen
    st = Image.new("L", (W, H), 0); s2 = ImageDraw.Draw(st)
    for _ in range(90):
        x = rr.uniform(0, W); y = rr.uniform(250, H); L = rr.uniform(150, 500)
        s2.line([(x, y), (x + rr.uniform(-10, 10), y + L)], fill=rr.randint(90, 180), width=rr.randint(6, 16))
    streak = np.array(st.filter(ImageFilter.GaussianBlur(5))).astype(np.float32) / 255
    damp = blend(base * 0.93, [(np.full((H, W, 3), 236, np.float32), streak * 0.32)])
    sm = puddle_mask([(SPILL[0], SPILL[1], 110)], 9)
    sedge = np.clip(sm - np.array(Image.fromarray((sm * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(9))).astype(np.float32) / 255, 0, 1) * 3
    spill = blend(damp, [(damp * 0.72, sm), (np.full((H, W, 3), 248, np.float32), np.clip(sedge, 0, 1) * 0.85)])
    return clean, dull_dirty, dull, damp, spill, dirty

CLEAN, DULL_DIRTY, DULL, DAMP, SPILL_ST, DIRTY = make_bgs()
TOPZONE = (YF < 720).astype(np.float32)

def verts(xs, ya, yb):
    pts = []
    for i, x in enumerate(xs):
        a, b = (yb, ya) if i % 2 == 0 else (ya, yb)
        pts += [(x, a), (x, b)]
    return pts

PASSES = verts([170, 470, 770, 1000], 760, 1500)
def reveal(t, D, a, b, pts, radius):
    p = ease_io(seg(t, a, D - b)) * (len(pts) - 1)
    if t <= a: return 0, p
    return np.maximum(trail_mask(pts, p, radius=radius, blur=18), TOPZONE * ease(seg(t, a, D - b))), p

PILL_Y = 1520
def tag(base, t, text, size=48):
    pill(base, W // 2, PILL_Y, text, F("Bold", size), ACC2, INK, ease(seg(t, 0.4, 0.7)))

# ---------- scenes ----------
TOTAL = 5
HOOK = make_hook(DIRTY, CLEAN,
                 [("STOP SOAKING", 120, (255, 255, 255)), ("YOUR WOOD", 150, YELLOW), ("FLOORS", 170, YELLOW)],
                 "DO THIS INSTEAD  ·  5 STEPS", mark_xy=PUD_MARK, check_xy=(800, 1060), split_to=0.5)

SAFETY = make_safety(lambda t: to_img(DIRTY), [
    ("no", "No steam mops: heat and moisture harm wood"),
    ("no", "No vinegar, ammonia or bleach"),
    ("no", "No soaking-wet mop or bucket"),
    ("never", "NEVER mix cleaners together"),
], title="The don'ts", label="BEFORE YOU START")

C1 = make_card(1, "Dry clean first", "Sweep, dust mop or vacuum on the hard-floor setting so grit can't scratch.", TOTAL)
def x_vac(t, D):
    m, p = reveal(t, D, 0.25, 0.3, PASSES, 160)
    base = to_img(blend(DULL_DIRTY, [(DULL, m)]))
    if 0.2 < t < D - 0.15:
        x, y = path_point(PASSES, p); vac_nozzle(base, x, y + math.sin(t * 30) * 4, wand_to=(x + 420, y - 900))
    tag(base, t, "GRIT OFF BEFORE ANY LIQUID", 44)
    return base

C2 = make_card(2, "Pick a pH-neutral cleaner", "Made for wood floors. Test a hidden spot, then mist lightly.", TOTAL)
def x_spray(t, D):
    base = to_img(DULL)
    d = ImageDraw.Draw(base)
    sp = ease(seg(t, 1.4, 1.8))
    if sp > 0:                                           # "small section" dashed frame
        for x in range(150, 600, 40): d.line([(x, 860), (x + 20, 860)], fill=(255, 255, 255), width=7); d.line([(x, 1260), (x + 20, 1260)], fill=(255, 255, 255), width=7)
        for y in range(860, 1260, 40): d.line([(150, y), (150, y + 20)], fill=(255, 255, 255), width=7); d.line([(600, y), (600, y + 20)], fill=(255, 255, 255), width=7)
    bq = ease(seg(t, 0.15, 0.6))
    sq = 1.0 if 0.8 < t < 2.4 and (t * 4) % 1 < 0.5 else 0.0
    nx, ny = spray_bottle(base, 860 + (1 - bq) * 400, 1080, s=0.95, squeeze=sq, label="WOOD")
    if 0.8 < t < 2.6:
        ml = Image.new("RGBA", (W, H), (0, 0, 0, 0)); mist(ml, nx, ny, t, dirn=-1, strength=0.85); base.alpha_composite(ml)
    q = back(seg(t, 1.0, 1.4))
    if q > 0:
        d = ImageDraw.Draw(base); r = int(92 * q); cx, cy = 300, 1350
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GREEN, outline="white", width=8)
        if q > 0.6: d.text((cx, cy), "pH 7", font=F("Bold", int(56 * q)), fill="white", anchor="mm")
    tag(base, t, "MADE FOR WOOD  ·  pH-NEUTRAL", 44)
    return base

C3 = make_card(3, "Damp, never wet", "Wring the mop well. Small sections, mop with the grain.", TOTAL)
def x_mop(t, D):
    m, p = reveal(t, D, 0.25, 0.3, PASSES, 170)
    base = to_img(blend(DULL, [(DAMP, m)]))
    if 0.2 < t < D - 0.15:
        x, y = path_point(PASSES, p); flat_mop(base, x, y, handle_to=(x + 380, y - 1000), wobble=math.sin(t * 14))
    tag(base, t, "DAMP, NOT DRIPPING")
    return base

P4 = [(SPILL[0], SPILL[1])] + verts([1000, 770, 470, 170], 760, 1500)
C4 = make_card(4, "Dry as you go", "No standing water. Blot spills and buff damp spots right away.", TOTAL)
def x_dry(t, D):
    sa = ease(seg(t, 0.0, 0.25))
    under = blend(DAMP, [(SPILL_ST, sa)])
    p = ease_io(seg(t, 1.3, D - 0.3)) * (len(P4) - 1)
    m = 0
    if t > 0.75:
        blot = ease(seg(t, 0.75, 1.3))
        m = np.exp(-(((XF - SPILL[0]) / (40 + 150 * blot)) ** 2 + ((YF - SPILL[1]) / (30 + 120 * blot)) ** 2)) * min(1, blot * 1.6)
        if t > 1.3: m = np.maximum(m, np.maximum(trail_mask(P4, p, 150, 18), TOPZONE * ease(seg(t, 1.3, D - 0.3))))
    base = to_img(blend(under, [(CLEAN, m)]) if not np.isscalar(m) else under)
    d = ImageDraw.Draw(base)
    if t < 1.1: ring(d, SPILL[0], SPILL[1], 150, ease(seg(t, 0.2, 0.7)))
    if 0.7 < t < D - 0.15:
        if t < 1.3:
            a = (t - 0.7) * 12; x, y = SPILL[0] + math.cos(a) * 40, SPILL[1] + math.sin(a) * 28
        else:
            x, y = path_point(P4, p)
        towel(base, x, y, ang=math.sin(t * 11) * 10, col=(255, 196, 40), stripe=(255, 226, 140))
    tag(base, t, "NO STANDING WATER")
    return base

SCR = Image.new("L", (W, H), 0); _sd = ImageDraw.Draw(SCR); _r = random.Random(3)
for _ in range(9):
    y = _r.uniform(1225, 1320); x = _r.uniform(640, 740)
    _sd.line([(x, y), (x + _r.uniform(130, 260), y + _r.uniform(-14, 14))], fill=255, width=_r.randint(3, 6))
SCR = np.array(SCR.filter(ImageFilter.GaussianBlur(1))).astype(np.float32) / 255
C5 = make_card(5, "Protect the finish", "Felt pads under furniture and mats at every door.", TOTAL)
def x_protect(t, D):
    sc = ease(seg(t, 0.2, 1.0)) * (1 - ease(seg(t, 1.5, 2.0)))
    base = to_img(blend(CLEAN, [(np.full((H, W, 3), 238, np.float32), SCR * sc * 0.9)]))
    d = ImageDraw.Draw(base)
    lx = 800 - 90 * ease_io(seg(t, 0.2, 1.0)) * (1 - ease_io(seg(t, 1.0, 1.4)))
    # chair (side view): seat + leg
    rrect(d, [lx - 230, 740, lx + 120, 800], 16, fill=(214, 150, 90), outline=INK, width=7)
    rrect(d, [lx - 30, 790, lx + 30, 1215], 12, fill=(196, 132, 76), outline=INK, width=7)
    rrect(d, [lx - 200, 790, lx - 150, 1080], 12, fill=(176, 116, 66), outline=INK, width=6)
    pq = back(seg(t, 1.3, 1.65))
    if pq > 0:
        ph = int(26 * pq); rrect(d, [lx - 44, 1212, lx + 44, 1212 + ph], 10, fill=(236, 226, 196), outline=INK, width=5)
    if t < 1.5: ring(d, 700, 1280, 150, ease(seg(t, 0.6, 1.1)))
    c = back(seg(t, 1.8, 2.15))
    if c > 0: check_badge(d, 930, 1120, int(52 * c))
    # door mat slides in
    mq = ease(seg(t, 2.0, 2.6))
    if mq > 0:
        mx = -460 + 520 * mq
        rrect(d, [mx, 1060, mx + 420, 1400], 34, fill=TEAL, outline=INK, width=8)
        for k in range(7): d.line([(mx + 40 + k * 56, 1095), (mx + 40 + k * 56, 1365)], fill=(10, 112, 128), width=14)
        c2 = back(seg(t, 2.6, 2.95))
        if c2 > 0: check_badge(d, mx + 380, 1080, int(52 * c2))
    tag(base, t, "FELT PADS + DOOR MATS")
    return base

SP_FL = [(220, 820), (760, 760), (480, 1000), (300, 1180), (860, 1120), (640, 880), (140, 980), (960, 940)]
_BA = make_ba(DIRTY, CLEAN, y_label=470, handle_y=1100, spark_pts=SP_FL)
def BA(t, D): return _BA(t, D)
BA.impact_at = _BA.impact_at
_OUT = make_outro(CLEAN)
def OUTRO(t, D): return _OUT(t, D)
def HOOK_F(t, D): return HOOK(t, D)
HOOK_F.headline_until = HOOK.headline_until

SCENES = [
    ("01_hook", HOOK_F, 3.3),
    ("02_safety", SAFETY, 4.6),
    ("03_vac", with_card(C1, x_vac), 3.6),
    ("04_spray", with_card(C2, x_spray), 3.6),
    ("05_mop", with_card(C3, x_mop), 3.8),
    ("06_dry", with_card(C4, x_dry), 4.0),
    ("07_protect", with_card(C5, x_protect), 3.8),
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
        fr = tuple(float(v) for v in sys.argv[4].split(",")) if len(sys.argv) > 4 else (0.05, 0.55, 0.95)
        print("\n".join(stills(SCENES, os.path.join(work, "stills"), fr, only)))
    else:
        print("total", build(SCENES, work, sys.argv[3], music, limit=0.5))
