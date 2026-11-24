"""2026-11-24 — 10-minute car interior reset before a road trip (car). lib/engine.py + lib/music_upbeat.py (clean style, upbeat=True).
Hook (contrarian / "not X, it's Y"): "YOU DON'T NEED A FULL DETAIL" -> split screen cluttered seat + footwell | reset seat,
pill "10-MINUTE ROAD TRIP RESET". Then safety -> 3 steps (trash + mats out, vacuum top to bottom, wipe touch points)
-> before/after wipe -> loop outro.
    python3 render.py stills [scene,scene] [fracs]      -> stills/*.jpg
    python3 render.py render                            -> 10-minute-interior-reset.mp4 (+ work/)
Sources checked (2026-11-24): Chemical Guys interior detailing guide (clear the cabin and pull the mats first; work top to
bottom because dust falls; vacuum before any liquid product; apply cleaner to a microfiber towel, never directly onto the
screen; steering wheel, door handles, console/cup holders get a detail pass; glass last), Jimbo's Detailing interior
cleaning order (declutter incl. floor mats first, then vacuum, then hard surfaces; spray onto the towel not the surface),
Tesla interior cleaning tips (avoid bleach, alcohol-based, citrus, naphtha and silicone products; no cleaners on the
touchscreen; keep liquid out of the seat-belt mechanism), The Drive (avoid ammonia glass cleaners on interior plastics,
work top-down). Sources disagree on wipe-vs-vacuum order, so the Reel follows the vacuum-before-liquid order and does not
claim either is wrong.
"""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from lib.engine import *
from lib.music_upbeat import make_track
from lib.music_styles import pick_style

SLUG = "2026-11-24-10-minute-interior-reset"
NAME = "10-minute-interior-reset"
PILL_Y = 1505
CUPS = [(92, 1170), (92, 1360)]          # cup holders in the centre console (left edge)
MAT_Y = 1600                              # top of the floor mat

def lmask(draw_fn, blur=2):
    m = Image.new("L", (W, H), 0); draw_fn(ImageDraw.Draw(m))
    m = m.filter(ImageFilter.GaussianBlur(blur)) if blur else m
    return np.array(m).astype(np.float32) / 255

def poly(pts, blur=2): return lmask(lambda d: d.polygon(pts, fill=255), blur)

# ---------------- backgrounds ----------------
def make_bgs():
    rng = np.random.default_rng(1124)
    grain = rng.normal(0, 1, (H, W)).astype(np.float32)
    k = np.clip(YF / H, 0, 1)[..., None]
    bg = np.array([62, 72, 86], np.float32) * (1 - k) + np.array([30, 34, 42], np.float32) * k
    bg += (np.exp(-(((XF - 860) / 420) ** 2 + ((YF - 320) / 380) ** 2)) * 46)[..., None]     # window light
    bg += (grain * 2)[..., None]
    # footwell carpet
    carpet_m = np.clip((YF - 1555) / 8, 0, 1)
    carpet = np.array([46, 48, 54], np.float32) + (grain * 7 + (lowfreq(8, 5) - 0.5) * 12)[..., None]
    bg = blend(bg, [(carpet, carpet_m)])
    # fabric seat
    weave = (np.sin(XF * 1.15) * np.sin(YF * 1.15)) * 5 + np.sin((XF + YF) * 0.35) * 3
    heather = (lowfreq(3, 6) - 0.5) * 14 + grain * 3
    ins_col = np.array([70, 92, 112], np.float32) + (weave + heather)[..., None]            # slate-blue insert
    bol_col = np.array([44, 48, 56], np.float32) + (grain * 3 + (lowfreq(4, 8) - 0.5) * 10)[..., None]
    back_out = poly([(290, 330), (990, 330), (1010, 1010), (260, 1010)], 3)
    back_ins = poly([(420, 360), (860, 360), (875, 990), (405, 990)], 2)
    cush_out = poly([(250, 1000), (1030, 1000), (1080, 1480), (210, 1480)], 3)
    cush_ins = poly([(390, 1030), (890, 1030), (925, 1450), (365, 1450)], 2)
    front = poly([(210, 1478), (1080, 1478), (1080, 1565), (230, 1565)], 3)              # cushion front face
    sh_b = np.clip((YF - 330) / 680, 0, 1); sh_c = np.clip((YF - 1000) / 480, 0, 1)
    seat = blend(bg, [(bol_col - (sh_b * 14)[..., None], back_out), (ins_col - (sh_b * 18)[..., None], back_ins)])
    seat = blend(seat, [(bol_col + (14 - sh_c * 22)[..., None], cush_out), (ins_col + (16 - sh_c * 24)[..., None], cush_ins),
                        (bol_col * 0.72, front)])
    seat += (np.exp(-((YF - 1016) / 14) ** 2) * -40 * np.clip(cush_out + back_out, 0, 1))[..., None]
    # centre console (left), dark textured plastic with two cup holders
    cons = poly([(0, 930), (205, 930), (225, 1920), (0, 1920)], 2)
    cons_col = np.array([38, 40, 46], np.float32) + (grain * 2.5 + (lowfreq(9, 3) - 0.5) * 8)[..., None]
    cons_col += (np.exp(-((XF - 150) / 40) ** 2) * 16)[..., None]
    seat = blend(seat, [(cons_col, cons)])
    im = to_img(seat); d = ImageDraw.Draw(im)
    d.line([(205, 930), (225, 1920)], fill=(70, 74, 82), width=5)
    rrect(d, [14, 1490, 190, 1640], 26, fill=(32, 34, 40), outline=(60, 64, 72), width=4)          # storage lid
    for cx, cy in CUPS:
        d.ellipse([cx - 70, cy - 70, cx + 70, cy + 70], fill=(56, 60, 68))
        d.ellipse([cx - 60, cy - 60, cx + 60, cy + 60], fill=(18, 20, 24))
        d.ellipse([cx - 44, cy - 40, cx + 44, cy + 48], fill=(26, 28, 33))
    for pts in ([(390, 1030), (365, 1450)], [(890, 1030), (925, 1450)], [(420, 360), (405, 990)], [(860, 360), (875, 990)]):
        (x0, y0), (x1, y1) = pts; n = 40
        for i in range(0, n, 2):
            a, b = i / n, (i + 0.6) / n
            d.line([(x0 + (x1 - x0) * a + 10, y0 + (y1 - y0) * a), (x0 + (x1 - x0) * b + 10, y0 + (y1 - y0) * b)], fill=(30, 34, 40), width=4)
    for y in (1240,):
        d.line([(378, y), (906, y)], fill=(52, 68, 84), width=6)
    rrect(d, [1020, 930, 1075, 1090], 16, fill=(26, 28, 32))                                    # belt buckle
    rrect(d, [1028, 890, 1068, 950], 10, fill=(150, 154, 160), outline=(20, 22, 26), width=4)
    CLEAN_NM = np.array(im.convert("RGB")).astype(np.float32)

    # ---- dirt: crumbs on cushion/seam/carpet, dust on console, sticky rings in cup holders ----
    cr = Image.new("L", (W, H), 0); c2 = ImageDraw.Draw(cr); rr = random.Random(24)
    for _ in range(190):
        x, y = rr.uniform(260, 1040), rr.uniform(1030, 1470)
        s = rr.uniform(3, 9); c2.polygon([(x - s, y), (x, y - s * 0.8), (x + s, y + s * 0.2), (x + s * 0.2, y + s)], fill=rr.randint(170, 255))
    for _ in range(40):
        x = rr.uniform(280, 1020); y = 1018 + rr.uniform(-8, 8); s = rr.uniform(3, 7); c2.ellipse([x - s, y - s, x + s, y + s], fill=235)
    for _ in range(260):
        x, y = rr.uniform(230, 1080), rr.uniform(1570, 1920)
        s = rr.uniform(3, 8); c2.polygon([(x - s, y), (x, y - s), (x + s, y + s * 0.3)], fill=rr.randint(150, 255))
    crumbs = np.array(cr.filter(ImageFilter.GaussianBlur(0.8))).astype(np.float32) / 255
    CRUMBC = np.array([200, 166, 110], np.float32)
    dust = (rng.random((H, W)) > 0.93).astype(np.float32) * cons * 0.5 + (lowfreq(12, 30) * 0.35) * cons
    sticky = np.zeros((H, W), np.float32)
    for cx, cy in CUPS:
        r = np.sqrt((XF - cx) ** 2 + ((YF - cy - 4) * 1.1) ** 2)
        sticky += np.clip(1 - np.abs(r - 36) / 9, 0, 1) * 0.9 + np.clip(1 - r / 34, 0, 1) * 0.45
    sticky = np.clip(sticky, 0, 1)
    STICKC = np.array([120, 78, 40], np.float32)
    DUSTC = np.array([120, 118, 112], np.float32)
    cons_dirt = [(DUSTC, dust * 0.55), (STICKC, sticky * 0.8)]
    DIRTY_NM = blend(CLEAN_NM, [(CRUMBC, crumbs * 0.95)] + cons_dirt)
    VAC_NM = blend(CLEAN_NM, cons_dirt)                 # crumbs vacuumed, console still dusty/sticky
    return DIRTY_NM, VAC_NM, CLEAN_NM, cons

DIRTY_NM, VAC_NM, CLEAN_NM, CONS = make_bgs()

# ---------------- floor mats (sprites so they can slide out / back in) ----------------
def make_mat(dirty):
    w, h = 760, 360
    rng = np.random.default_rng(7 if dirty else 8)
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    rrect(d, [0, 0, w - 1, h + 60], 50, fill=(22, 23, 26))
    rrect(d, [40, 36, w - 41, h + 60], 36, fill=(34, 35, 40))
    for y in range(70, h, 44):
        for x in range(80, w - 80, 120):
            rrect(d, [x, y, x + 86, y + 16], 8, fill=(44, 46, 52))
    if dirty:
        rr = random.Random(3)
        for _ in range(30):                              # salt/sand smudges + leaves
            x, y = rr.uniform(60, w - 60), rr.uniform(40, h - 10); r = rr.uniform(16, 60)
            d.ellipse([x - r, y - r * 0.6, x + r, y + r * 0.6], fill=(150, 132, 104, rr.randint(60, 120)))
        for _ in range(120):
            x, y = rr.uniform(40, w - 40), rr.uniform(30, h); s = rr.uniform(3, 7)
            d.ellipse([x - s, y - s, x + s, y + s], fill=(200, 180, 140, 230))
        for x, y, a in [(160, 120, 20), (520, 220, -35), (640, 90, 60)]:
            leaf = Image.new("RGBA", (120, 70), (0, 0, 0, 0)); ld = ImageDraw.Draw(leaf)
            ld.ellipse([6, 10, 114, 60], fill=(176, 104, 40, 255)); ld.line([(10, 35), (112, 35)], fill=(120, 66, 24), width=4)
            lay.alpha_composite(leaf.rotate(a, expand=True, resample=Image.BICUBIC), (x - 60, y - 40))
    return lay
MAT_D, MAT_C = make_mat(True), make_mat(False)
MAT_X = 270
def put_mat(img, mat, dy=0, ang=0.0):
    m = mat.rotate(ang, expand=True, resample=Image.BICUBIC) if ang else mat
    img.alpha_composite(m, (int(MAT_X - (m.width - mat.width) / 2), int(MAT_Y + dy)))

# ---------------- clutter items (all generic, drawn) ----------------
def item_cup():
    lay = Image.new("RGBA", (300, 200), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)       # takeaway cup lying on its side
    d.polygon([(30, 60), (250, 40), (250, 160), (30, 140)], fill=(244, 240, 232), outline=INK, width=6)
    d.polygon([(110, 53), (190, 46), (190, 154), (110, 147)], fill=ACCENT, outline=INK, width=5)
    rrect(d, [240, 30, 280, 170], 12, fill=(250, 250, 250), outline=INK, width=6)
    d.ellipse([140, 150, 230, 190], fill=(110, 72, 40, 200))                          # coffee drip
    return lay
def item_wrapper():
    lay = Image.new("RGBA", (180, 170), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.polygon([(30, 70), (70, 20), (130, 30), (165, 80), (140, 140), (80, 155), (25, 120)], fill=(236, 214, 150), outline=INK, width=6)
    for a, b in [((60, 50), (110, 90)), ((90, 40), (70, 120)), ((120, 70), (60, 130))]:
        d.line([a, b], fill=(196, 170, 110), width=5)
    return lay
def item_chips():
    lay = Image.new("RGBA", (220, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.polygon([(30, 30), (190, 20), (200, 240), (20, 235)], fill=(240, 120, 60), outline=INK, width=6)
    for y in (40, 222):
        for x in range(30, 196, 14): d.line([(x, y - 10), (x + 7, y + 6)], fill=(200, 90, 40), width=4)
    d.ellipse([70, 90, 150, 170], fill=(255, 200, 70))                                 # generic sun shape, no text
    return lay
def item_receipt():
    lay = Image.new("RGBA", (150, 230), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.polygon([(20, 10), (130, 20), (124, 210), (14, 200)], fill=(250, 250, 246), outline=(120, 128, 136), width=4)
    for i in range(6): d.line([(36, 50 + i * 24), (108, 54 + i * 24)], fill=(170, 176, 184), width=6)
    return lay
def item_bottle():
    lay = Image.new("RGBA", (330, 140), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)     # water bottle lying down
    rrect(d, [20, 25, 250, 115], 40, fill=(170, 215, 245, 230), outline=INK, width=6)
    d.polygon([(250, 40), (290, 55), (290, 85), (250, 100)], fill=(170, 215, 245, 230), outline=INK, width=6)
    rrect(d, [286, 48, 318, 92], 8, fill=ACCENT, outline=INK, width=5)
    rrect(d, [90, 30, 170, 110], 6, fill=(90, 170, 230, 230))
    return lay
# (sprite, centre x, y, rotation) — left half shows the most clutter (hook split screen)
ITEMS = [(item_cup(), 340, 1180, -8), (item_wrapper(), 520, 1350, 0), (item_receipt(), 300, 1400, 25),
         (item_chips(), 760, 1180, -14), (item_receipt(), 880, 1390, -30), (item_bottle(), 420, 1760, 6)]
ITEMS = [(s.rotate(a, expand=True, resample=Image.BICUBIC), x, y) for s, x, y, a in ITEMS]
BAG = (960, 1690)

def put_items(img, t=None, t0=0.0, step=0.18, fly=0.45):
    """t=None: all items in place. Otherwise item i flies into the trash bag starting at t0 + i*step."""
    for i, (s, x, y) in enumerate(ITEMS):
        if t is None: p = 0.0
        else: p = seg(t, t0 + i * step, t0 + i * step + fly)
        if p >= 1: continue
        e = ease_io(p)
        cx = x + (BAG[0] - x) * e; cy = y + (BAG[1] - 120 - y) * e - math.sin(e * math.pi) * 260
        sc = 1 - 0.55 * e
        s2 = s.rotate(e * 200, expand=True, resample=Image.BICUBIC) if e > 0 else s
        s2 = s2.resize((max(1, int(s2.width * sc)), max(1, int(s2.height * sc))), Image.BICUBIC)
        img.alpha_composite(s2, (int(cx - s2.width / 2), int(cy - s2.height / 2)))

def trash_bag(img, p, fill=0.0):
    if p <= 0: return
    lay = Image.new("RGBA", (300, 340), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.polygon([(40, 90), (260, 90), (280, 320), (20, 320)], fill=(52, 56, 64), outline=INK, width=7)
    d.polygon([(40, 90), (100, 40), (150, 80), (200, 40), (260, 90)], fill=(66, 70, 80), outline=INK, width=7)
    d.ellipse([60, 70, 240, 120], fill=(20, 22, 26))
    s = 0.6 + 0.4 * back(p) + 0.04 * fill
    lay = lay.resize((int(300 * s), int(340 * s)), Image.BICUBIC)
    img.alpha_composite(with_alpha(lay, min(1, p * 2)), (int(BAG[0] - lay.width / 2), int(BAG[1] - lay.height * 0.55)))

def frame_of(arr, mat=None, mat_dy=0, items=True):
    im = to_img(arr)
    if mat is not None: put_mat(im, mat, mat_dy)
    if items: put_items(im)
    return im
DIRTY_FULL = np.array(frame_of(DIRTY_NM, MAT_D).convert("RGB")).astype(np.float32)
CLEAN = np.array(frame_of(CLEAN_NM, MAT_C, items=False).convert("RGB")).astype(np.float32)

# ---------------- scenes ----------------
TOTAL = 3
HOOK = make_hook(DIRTY_FULL, CLEAN, [("YOU DON'T NEED", 150, YELLOW), ("A FULL DETAIL", 150, YELLOW)],
                 "10-MINUTE ROAD TRIP RESET", mark_xy=(350, 1200), check_xy=(800, 1150), split_to=0.5, labels=True)
HOOK_D = 2.4

SAFETY = make_safety(lambda t: to_img(DIRTY_FULL), [
    ("never", "Never mix cleaners. No bleach or ammonia."),
    ("ok", "Doors open. Spray the towel, not the screen."),
], title="Safety first", label="BEFORE YOU START")

# step 1: trash into a bag, mats out
C1 = make_card(1, "Trash out, mats out", "Bag the trash, shake mats outside.", TOTAL)
def x_trash(t, D):
    im = to_img(DIRTY_NM)
    mp = ease_io(seg(t, 1.45, D - 0.15))
    put_mat(im, MAT_D, mp * 420, ang=-6 * mp)
    trash_bag(im, seg(t, 0.0, 0.3), fill=seg(t, 0.3, 1.5))
    put_items(im, t, 0.3, step=0.17, fly=0.42)
    pill(im, W // 2, PILL_Y, "ONE BAG, ONE PASS", F("Bold", 46), ACC2, INK, ease(seg(t, 0.3, 0.6)))
    return im

# step 2: vacuum top to bottom: seat seam -> cushion -> carpet
VPATH = ([(280 + 740 * i / 6, 1022) for i in range(7)] +
         [(1010, 1130), (300, 1130), (300, 1260), (1010, 1260), (1010, 1390), (300, 1390),
          (300, 1640), (1050, 1640), (1050, 1780), (300, 1780), (300, 1900), (1050, 1900)])
C2 = make_card(2, "Vacuum top to bottom", "Seat seams first, the floor last.", TOTAL)
def x_vac(t, D):
    t0 = 0.15
    p = ease_io(seg(t, t0, D - 0.1)) * (len(VPATH) - 1)
    m = trail_mask(VPATH, p, radius=95, blur=16) if t > t0 else 0
    im = to_img(blend(DIRTY_NM, [(VAC_NM, m)]))
    x, y = path_point(VPATH, p)
    crevice_tool(im, x, y, wand_to=(x + 520, y + 900))
    pill(im, W // 2, PILL_Y, "BEFORE ANY SPRAY", F("Bold", 46), ACC2, INK, ease(seg(t, 0.3, 0.6)))
    return im

# step 3: wipe touch points (console + cup holders) with a sprayed towel, then clean mats back in
WPATH = [(95 + 60 * math.sin(k * 0.9), 980 + 560 * k / 24) for k in range(25)]
C3 = make_card(3, "Wipe what you touch", "Wheel, handles, cup holders.", TOTAL)
SP3 = [(90, 1170), (100, 1360), (600, 1200), (820, 1350), (480, 1700), (860, 1760)]
def x_wipe(t, D):
    t0 = 0.45
    p = ease_io(seg(t, t0, D - 0.9)) * (len(WPATH) - 1)
    m = trail_mask(WPATH, p, radius=130, blur=22) * CONS if t > t0 else 0
    if t > D - 0.95: m = np.maximum(m, CONS * ease(seg(t, D - 0.95, D - 0.7)))
    im = to_img(blend(VAC_NM, [(CLEAN_NM, m)]))
    if t < t0 + 0.05:                                   # spray the towel, not the surface
        towel(im, 560, 1300, ang=-8, col=(90, 170, 230), stripe=(170, 215, 245))
        nx, ny = spray_bottle(im, 860, 1180, s=0.8, squeeze=math.sin(t * 30) > 0, label="CLEANER")
        mist(im, nx, ny, t, dirn=-1, strength=0.9)
    elif t < D - 0.8:
        x, y = path_point(WPATH, p)
        towel(im, x + 40, y, ang=math.sin(t * 9) * 12, col=(90, 170, 230), stripe=(170, 215, 245))
    mp = ease(seg(t, D - 0.85, D - 0.35))
    if mp > 0: put_mat(im, MAT_C, (1 - mp) * 420)
    if t > D - 0.6: sparkles(im, t, D - 0.6, 1.0, SP3)
    pill(im, W // 2, PILL_Y, "GLASS GOES LAST", F("Bold", 46), ACC2, INK, ease(seg(t, 0.3, 0.6)))
    return im

SP = [(300, 1100), (620, 1080), (880, 1200), (430, 1330), (760, 1420), (560, 1700), (900, 1800)]
_BA = make_ba(DIRTY_FULL, CLEAN, y_label=SAFE_TOP + 120, handle_y=1240, spark_pts=SP)
def BA(t, D): return _BA(t, D)
BA.impact_at = _BA.impact_at

_OUT = make_loop_outro(CLEAN, HOOK(0.0, HOOK_D), ask="Crumbs or wrappers?")
def OUTRO(t, D): return _OUT(t, D)

SCENES = [
    ("01_hook", HOOK, HOOK_D),
    ("02_safety", SAFETY, 2.1),
    ("03_trash", with_card(C1, x_trash), 2.7),
    ("04_vac", with_card(C2, x_vac), 2.5),
    ("05_wipe", with_card(C3, x_wipe), 2.8),
    ("06_ba", BA, 2.5),
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
