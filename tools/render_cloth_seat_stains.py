"""2026-11-12 — Get stains out of cloth car seats (car). Uses lib/engine.py + lib/music_upbeat.py (+ clean style rotation).
python3 tools/render_cloth_seat_stains.py stills|render WORKDIR [OUT_MP4]
"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.engine import *
from lib.music_upbeat import make_track
from lib.music_styles import pick_style

SLUG = "2026-11-12-cloth-seat-stains"
ST = (390, 1235)                     # coffee stain centre (on the seat cushion)
HID = (230, 1470)                    # hidden test spot (lower side of the cushion)

def poly_mask(pts, blur=2):
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).polygon(pts, fill=255)
    return np.array(m.filter(ImageFilter.GaussianBlur(blur))).astype(np.float32) / 255

def make_bgs():
    rng = np.random.default_rng(12)
    grain = rng.normal(0, 1, (H, W)).astype(np.float32)
    # ---- cabin backdrop ----
    k = np.clip(YF / H, 0, 1)[..., None]
    bg = np.array([58, 66, 78], np.float32) * (1 - k) + np.array([28, 32, 40], np.float32) * k
    bg += (np.exp(-(((XF - 820) / 420) ** 2 + ((YF - 300) / 380) ** 2)) * 40)[..., None]     # window light
    bg += (grain * 2)[..., None]
    floor = np.clip((YF - 1700) / 6, 0, 1)
    bg = blend(bg, [(np.array([24, 26, 30], np.float32) + (grain * 4)[..., None], floor)])
    # ---- fabric ----
    weave = (np.sin(XF * 1.15) * np.sin(YF * 1.15)) * 5 + np.sin((XF + YF) * 0.35) * 3
    heather = (lowfreq(3, 6) - 0.5) * 14 + grain * 3
    ins_col = np.array([172, 170, 164], np.float32) + (weave + heather)[..., None]          # light grey insert
    bol_col = np.array([102, 106, 114], np.float32) + (grain * 3 + (lowfreq(4, 8) - 0.5) * 10)[..., None]
    # backrest (top part, mostly behind the step card) and cushion (front view, slight perspective)
    back_out = poly_mask([(150, 330), (930, 330), (960, 1010), (120, 1010)], 3)
    back_ins = poly_mask([(300, 360), (780, 360), (800, 990), (280, 990)], 2)
    cush_out = poly_mask([(110, 1000), (970, 1000), (1060, 1720), (20, 1720)], 3)
    cush_ins = poly_mask([(270, 1040), (810, 1040), (860, 1670), (220, 1670)], 2)
    seat = bg.copy()
    sh_b = np.clip((YF - 330) / 680, 0, 1)
    sh_c = np.clip((YF - 1000) / 720, 0, 1)
    seat = blend(seat, [(bol_col - (sh_b * 18)[..., None], back_out), (ins_col - (sh_b * 22)[..., None], back_ins)])
    seat = blend(seat, [(bol_col + (12 - sh_c * 30)[..., None], cush_out), (ins_col + (10 - sh_c * 34)[..., None], cush_ins)])
    # soft bolster roll highlight + gap shadow between backrest and cushion
    seat += (np.exp(-((YF - 1018) / 14) ** 2) * -48 * np.clip(cush_out + back_out, 0, 1))[..., None]
    for cx in (290, 790):
        seat += (np.exp(-((XF - cx) / 16) ** 2) * 30 * cush_out * (YF > 1040))[..., None]
    im = to_img(seat); d = ImageDraw.Draw(im)
    # stitching
    for pts in ([(270, 1040), (220, 1670)], [(810, 1040), (860, 1670)], [(300, 360), (280, 990)], [(780, 360), (800, 990)]):
        (x0, y0), (x1, y1) = pts; n = 46
        for i in range(n):
            if i % 2: continue
            a, b = i / n, (i + 0.6) / n
            d.line([(x0 + (x1 - x0) * a + 10, y0 + (y1 - y0) * a), (x0 + (x1 - x0) * b + 10, y0 + (y1 - y0) * b)], fill=(70, 72, 78), width=4)
    for y in (1250, 1460):                           # horizontal channel seams on the insert
        d.line([(248, y), (835, y)], fill=(140, 138, 134), width=6)
        d.line([(248, y + 5), (835, y + 5)], fill=(196, 194, 190), width=3)
    # seat-belt buckle stalk on the right edge
    rrect(d, [1000, 940, 1060, 1100], 16, fill=(30, 32, 36))
    rrect(d, [1010, 900, 1050, 960], 10, fill=(150, 154, 160), outline=(20, 22, 26), width=4)
    CLEANA = np.array(im.convert("RGB")).astype(np.float32)
    insm = np.clip(cush_ins + cush_out * 0.0, 0, 1)

    # ---- coffee stain: irregular blob + darker tide-line ring + a few drips ----
    blob = np.exp(-(((XF - ST[0]) / 165) ** 2 + ((YF - ST[1]) / 120) ** 2))
    blob *= 0.75 + 0.5 * lowfreq(31, 40)
    m = Image.new("L", (W, H), 0); md = ImageDraw.Draw(m)
    for dx, dy, r in [(150, 70, 30), (190, 100, 18), (-150, -40, 26), (60, -120, 20), (-60, 130, 22)]:
        md.ellipse([ST[0] + dx - r, ST[1] + dy - r * 0.8, ST[0] + dx + r, ST[1] + dy + r * 0.8], fill=255)
    drips = np.array(m.filter(ImageFilter.GaussianBlur(6))).astype(np.float32) / 255
    core = np.clip((blob - 0.32) / 0.2, 0, 1)
    stain = np.clip(np.maximum(core, drips), 0, 1) * cush_out
    edge = np.clip(1 - np.abs(blob - 0.34) / 0.05, 0, 1) * cush_out
    COFFEE = np.array([118, 84, 56], np.float32) + (weave * 0.8)[..., None]
    TIDE = np.array([86, 58, 36], np.float32)
    STAIN_M, EDGE_M = stain * 0.78, edge * 0.7
    # ---- crumbs and lint ----
    cr = Image.new("L", (W, H), 0); c2 = ImageDraw.Draw(cr); rr = random.Random(5)
    for _ in range(170):
        x, y = rr.uniform(140, 960), rr.uniform(1040, 1700)
        s = rr.uniform(3, 9); c2.polygon([(x - s, y), (x, y - s * 0.8), (x + s, y + s * 0.2), (x + s * 0.2, y + s)], fill=rr.randint(170, 255))
    for _ in range(22):                          # crumbs collected in the lower seam
        x = rr.uniform(250, 840); y = 1460 + rr.uniform(-6, 6); s = rr.uniform(3, 7); c2.ellipse([x - s, y - s, x + s, y + s], fill=230)
    crumbs = np.array(cr.filter(ImageFilter.GaussianBlur(0.8))).astype(np.float32) / 255 * cush_out
    CRUMBC = np.array([196, 160, 104], np.float32)
    def state(stain_k, crumbs_k=0.0, damp=0.0):
        a = blend(CLEANA, [(COFFEE, STAIN_M * stain_k), (TIDE, EDGE_M * stain_k)])
        if damp > 0:
            dm = np.exp(-(((XF - ST[0]) / 230) ** 2 + ((YF - ST[1]) / 170) ** 2)) * cush_out
            a = a * (1 - (dm * 0.20 * damp)[..., None])
        return blend(a, [(CRUMBC, crumbs * crumbs_k)])
    return state, CLEANA, cush_out

STATE, CLEAN, CUSH = make_bgs()
DIRTY = STATE(1.0, 1.0)
NOCRUMB = STATE(1.0)
LIGHT = STATE(0.38, damp=1.0)
DAMP = STATE(0.0, damp=1.0)
NOISE = lowfreq(77, 30)

def fb(arr): return to_img(arr)
def layer(): return Image.new("RGBA", (W, H), (0, 0, 0, 0))
PILL_Y = 1540

# ---------- props ----------
def soft_brush(img, x, y, ang=0):
    """upholstery brush with soft white bristles, bristles centred near (x, y)."""
    scrub_brush(img, x, y, ang=ang, col=(255, 196, 40))

def zigzag(rows, xa, xb):
    pts = []
    for i, y in enumerate(rows):
        a, b = (xa, xb) if i % 2 == 0 else (xb, xa)
        pts += [(a, y), (b, y)]
    return pts

# ---------- scenes ----------
TOTAL = 5
HOOK = make_hook(DIRTY, CLEAN,
                 [("COFFEE ON YOUR SEAT?", 92, (255, 255, 255)), ("STOP", 170, YELLOW), ("RUBBING IT", 140, YELLOW)],
                 "5 STEPS  ·  NO SOAKING", mark_xy=(ST[0] - 40, ST[1]), check_xy=(800, 1200), split_to=0.5)

SAFETY = make_safety(lambda t: fb(DIRTY), [
    ("ok", "Doors open for fresh air"),
    ("ok", "Spot-test a hidden area first"),
    ("no", "No bleach on seat fabric"),
    ("never", "NEVER mix cleaners together"),
], title="Before you start", label="SAFETY FIRST")

P1 = zigzag([1100, 1250, 1400, 1550, 1680], 170, 920)
C1 = make_card(1, "Vacuum first", "The whole seat and the seams, so crumbs don't turn to mud.", TOTAL)
def x_vac(t, D):
    p = ease_io(seg(t, 0.25, D - 0.3)) * (len(P1) - 1)
    m = trail_mask(P1, p, radius=120, blur=16) if t > 0.25 else 0
    base = fb(blend(DIRTY, [(NOCRUMB, m)]))
    if 0.2 < t < D - 0.12:
        x, y = path_point(P1, p); vac_nozzle(base, x, y + math.sin(t * 30) * 4, wand_to=(1300, 2100))
    pill(base, W // 2, PILL_Y, "SEAMS TOO", F("Bold", 48), ACC2, INK, ease(seg(t, 0.4, 0.7)))
    return base

C2 = make_card(2, "Test a hidden spot", "Upholstery cleaner, or a few drops of dish soap in warm water.", TOTAL)
def x_test(t, D):
    base = fb(NOCRUMB)
    bq = ease(seg(t, 0.15, 0.55))
    sq = 1.0 if 0.8 < t < 1.6 and (t * 4) % 1 < 0.5 else 0.0
    nx, ny = spray_bottle(base, 720 + (1 - bq) * 500, 1560, s=0.9, squeeze=sq, label="FABRIC")
    if 0.8 < t < 1.8:
        ml = layer(); mist(ml, nx, ny, t, dirn=-1, strength=0.8); base.alpha_composite(ml)
    d = ImageDraw.Draw(base)
    ring(d, HID[0], HID[1] - 30, 95, ease(seg(t, 0.4, 0.9)), col=ACC2, width=12)
    c = back(seg(t, 2.1, 2.5))
    if c > 0:
        check_badge(d, HID[0] + 10, HID[1] - 140, int(50 * c))
    pill(base, W // 2, 960, "NO FADING? GOOD TO GO" if t > 2.0 else "TEST FIRST", F("Bold", 46), ACC2, INK, ease(seg(t, 0.4, 0.7)))
    return base

C3 = make_card(3, "Mist, don't soak", "A light spray on the stain. Too much liquid soaks into the foam.", TOTAL)
def x_mist(t, D):
    wet = ease(seg(t, 0.9, 2.4))
    dm = np.exp(-(((XF - ST[0]) / 200) ** 2 + ((YF - ST[1]) / 150) ** 2)) * CUSH * 0.16 * wet
    base = fb(NOCRUMB * (1 - dm[..., None]))
    bq = ease(seg(t, 0.15, 0.5))
    sq = 1.0 if 0.8 < t < 2.3 and (t * 4) % 1 < 0.5 else 0.0
    nx, ny = spray_bottle(base, 900 + (1 - bq) * 400, 1300, s=0.9, squeeze=sq, label="FABRIC")
    if 0.8 < t < 2.5:
        ml = layer(); mist(ml, nx, ny, t, dirn=-1, strength=0.9); base.alpha_composite(ml)
    d = ImageDraw.Draw(base)
    if t > 2.5:
        check_badge(d, 560, 1110, int(44 * back(seg(t, 2.5, 2.9))))
    pill(base, W // 2, PILL_Y, "LIGHT MIST ONLY", F("Bold", 48), ACC2, INK, ease(seg(t, 0.4, 0.7)))
    return base

FOAM = [(ST[0] + 120 * math.cos(a) * r, ST[1] + 80 * math.sin(a) * r) for a, r in
        [(i * 2.39996, 0.25 + 0.75 * ((i * 0.618) % 1)) for i in range(26)]]
C4 = make_card(4, "Brush gently", "Soft brush, short strokes, from the edges in.", TOTAL)
def x_brush(t, D):
    p = ease_io(seg(t, 0.3, D - 0.3))
    m = dissolve(p, NOISE, 0.3) * 1.0
    base = fb(blend(NOCRUMB * (1 - (np.exp(-(((XF - ST[0]) / 200) ** 2 + ((YF - ST[1]) / 150) ** 2)) * CUSH * 0.16)[..., None]), [(LIGHT, m)]))
    fl = layer()
    if t > 0.4:
        bubbles(fl, t, 0.4, FOAM, col=(255, 255, 255), rise=20, rmax=12, speed=1.2)
    base.alpha_composite(fl)
    if 0.2 < t < D - 0.1:
        r = 150 * (1 - 0.7 * p)                      # spiral from the edges in
        a = t * 11
        soft_brush(base, ST[0] + math.cos(a) * r, ST[1] + 40 + math.sin(a) * r * 0.6, ang=math.sin(a) * 10)
    pill(base, W // 2, PILL_Y, "EDGES  >  CENTER", F("Bold", 48), ACC2, INK, ease(seg(t, 0.4, 0.7)))
    return base

C5 = make_card(5, "Blot, then air-dry", "Press a clean towel, don't rub. Dry with the windows cracked.", TOTAL)
def x_blot(t, D):
    presses = 4; t0, t1 = 0.3, 2.8
    ph = seg(t, t0, t1) * presses
    n = int(ph); fr = ph - n
    p = clamp((n + (1 if fr > 0.5 else 0)) / presses)
    dry = ease(seg(t, 2.9, D - 0.2))
    a = blend(LIGHT, [(DAMP, p)])
    a = blend(a, [(CLEAN, dry)])
    base = fb(a)
    if t0 < t < t1 + 0.1:
        lift = abs(math.sin(fr * math.pi)) if n < presses else 1
        y = ST[1] - 30 - 120 * lift
        sc = 1.0 + 0.08 * lift
        towel(base, ST[0] + (n % 2) * 40 - 20, y, ang=-4 + (n % 2) * 8, col=(80, 150, 230), stripe=(150, 200, 245))
        d = ImageDraw.Draw(base)
        if lift < 0.15: d.text((ST[0] + 210, ST[1] - 150), "PRESS", font=F("Bold", 40), fill=(255, 255, 255), anchor="mm", stroke_width=6, stroke_fill=INK)
    if t > 2.9:
        airflow(base, t, 0, W, [1120, 1300, 1480], alpha=int(170 * ease(seg(t, 2.9, 3.3))))
    if t > D - 0.6:
        sparkles(base, t, D - 0.6, 0.8, [(ST[0] - 60, ST[1] - 60), (ST[0] + 120, ST[1] + 30), (ST[0] - 140, ST[1] + 60)])
    label = "BLOT, DON'T RUB" if t < 2.9 else "WINDOWS CRACKED TO DRY"
    pill(base, W // 2, PILL_Y, label, F("Bold", 46), ACC2, INK, ease(seg(t, 0.4, 0.7)))
    return base

SP = [(220, 1120), (760, 1100), (480, 1300), (300, 1420), (860, 1380), (640, 1180), (140, 1300), (960, 1240)]
_BA = make_ba(DIRTY, CLEAN, y_label=900, handle_y=1250, spark_pts=SP)
def BA(t, D): return _BA(t, D)
BA.impact_at = _BA.impact_at
_OUT = make_outro(CLEAN)
def OUTRO(t, D): return _OUT(t, D)
def HOOK_F(t, D): return HOOK(t, D)
HOOK_F.headline_until = HOOK.headline_until

SCENES = [
    ("01_hook", HOOK_F, 3.3),
    ("02_safety", SAFETY, 4.4),
    ("03_vac", with_card(C1, x_vac), 3.6),
    ("04_test", with_card(C2, x_test), 3.6),
    ("05_mist", with_card(C3, x_mist), 3.4),
    ("06_brush", with_card(C4, x_brush), 4.0),
    ("07_blot", with_card(C5, x_blot), 4.4),
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
