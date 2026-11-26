"""2026-11-26 — Get crumbs out of car seat crevices (car). lib/engine.py + lib/music_upbeat.py (clean style, upbeat=True).
Hook (myth-bust / "it's not X, it's Y"): "IT'S NOT YOUR VACUUM" on a close-up split screen (crumbs packed in the seat
bight + console gap | clean), pill "CRUMBS HIDE IN THE SEAMS". Then 3 steps (slide the seat back to expose the gap
and rails, spread the seam and brush crumbs loose, slow crevice-tool pass along the seam and the console gap)
-> before/after wipe -> loop outro. No chemicals are used, so there is no safety scene (STYLE.md: safety scene
whenever a chemical/product is used); the caption carries the compressed-air / sharp-tool notes.
    python3 render.py stills [scene,scene] [fracs]      -> stills/*.jpg
    python3 render.py render                            -> crumbs-in-car-seats.mp4 (+ work/)
Sources checked (2026-11-26): Autoblog Details "how to properly vacuum your car" (brush to loosen, then vacuum
immediately; spread seat seams by hand and run the crevice tool at the base of the stitch; push the seat back on its
rails to vacuum under it and the rails; compressed air for tracks/seams if you have it; don't strip the seat-rail
grease; burrs on a crevice tool snag fabric), Jimbo's Detailing "how to clean between car seats" (slide the seat fully
back, clean, then fully forward and repeat; crevice tool under the tracks; never spray cleaner into the seat gap —
electronics and rails), Parkers "how to vacuum your car" (turbo/stiff brush dislodges what suction alone won't;
crevice tool along the seat-back/base seam and between seat and console). Seat-gap fillers were left out (they can
crowd the seat-belt buckle; not verified as safe for every car).
"""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from lib.engine import *
from lib.music_upbeat import make_track
from lib.music_styles import pick_style

SLUG = "2026-11-26-crumbs-in-car-seats"
NAME = "crumbs-in-car-seats"
PILL_Y = 1505
SEAM_Y = 905                     # seat bight (backrest meets cushion)
GAP_X0, GAP_X1 = 190, 266        # dark gap between centre console and seat
SC_CX, SC_CY = 700, 300          # seat slides "back" = shrinks toward this point

def lmask(draw_fn, blur=2):
    m = Image.new("L", (W, H), 0); draw_fn(ImageDraw.Draw(m))
    m = m.filter(ImageFilter.GaussianBlur(blur)) if blur else m
    return np.array(m).astype(np.float32) / 255

def poly(pts, blur=2): return lmask(lambda d: d.polygon(pts, fill=255), blur)

CRUMB_COLS = [(222, 178, 108), (206, 150, 80), (236, 206, 150), (180, 120, 64), (245, 226, 180)]
def draw_crumbs(img, pts, seed, smin=5, smax=13):
    """irregular cracker/cookie crumbs with a dark contact shadow so they read on dark fabric."""
    d = ImageDraw.Draw(img); rr = random.Random(seed)
    for x, y in pts:
        s = rr.uniform(smin, smax); a = rr.uniform(0, math.tau); k = rr.randint(4, 6)
        shape = [(x + math.cos(a + i * math.tau / k) * s * rr.uniform(0.6, 1.15),
                  y + math.sin(a + i * math.tau / k) * s * rr.uniform(0.5, 1.0)) for i in range(k)]
        d.polygon([(px + 2, py + 3) for px, py in shape], fill=(10, 10, 14, 150))
        d.polygon(shape, fill=rr.choice(CRUMB_COLS) + (255,))

# ---------------- floor layer (console, gap, carpet, seat rail) ----------------
def make_floor(dirty):
    rng = np.random.default_rng(1126)
    grain = rng.normal(0, 1, (H, W)).astype(np.float32)
    k = np.clip(YF / H, 0, 1)[..., None]
    bg = np.array([66, 74, 86], np.float32) * (1 - k) + np.array([28, 32, 40], np.float32) * k
    bg += (np.exp(-(((XF - 880) / 420) ** 2 + ((YF - 160) / 360) ** 2)) * 50)[..., None]
    bg += (grain * 2)[..., None]
    carpet_m = np.clip((YF - 1300) / 8, 0, 1)
    carpet = np.array([44, 46, 52], np.float32) + (grain * 7 + (lowfreq(8, 5) - 0.5) * 12)[..., None]
    bg = blend(bg, [(carpet, carpet_m)])
    gap = poly([(GAP_X0 - 6, 760), (GAP_X1 + 120, 760), (GAP_X1 + 120, 1920), (GAP_X0 + 6, 1920)], 2)
    bg = blend(bg, [(np.array([20, 20, 24], np.float32) + (grain * 2)[..., None], gap * (1 - carpet_m * 0.6))])
    cons = poly([(0, 760), (GAP_X0, 760), (GAP_X0 + 12, 1920), (0, 1920)], 2)
    cons_col = np.array([40, 42, 48], np.float32) + (grain * 2.5 + (lowfreq(9, 3) - 0.5) * 8)[..., None]
    cons_col += (np.exp(-((XF - 140) / 40) ** 2) * 16)[..., None]
    bg = blend(bg, [(cons_col, cons)])
    im = to_img(bg); d = ImageDraw.Draw(im)
    d.line([(GAP_X0, 760), (GAP_X0 + 12, 1920)], fill=(74, 78, 86), width=6)
    rrect(d, [16, 1240, 170, 1400], 26, fill=(32, 34, 40), outline=(62, 66, 74), width=4)       # storage lid
    d.ellipse([22, 900, 170, 1048], fill=(56, 60, 68)); d.ellipse([34, 912, 158, 1036], fill=(18, 20, 24))
    for x0 in (360, 900):                                                                          # seat rails
        rrect(d, [x0 - 20, 1300, x0 + 20, 1920], 8, fill=(70, 74, 80), outline=(20, 22, 26), width=4)
        for y in range(1330, 1900, 60): d.ellipse([x0 - 7, y - 7, x0 + 7, y + 7], fill=(30, 32, 36))
    if dirty:
        rr = random.Random(5)
        gp = [(rr.uniform(GAP_X0 + 10, GAP_X1 + 70), rr.uniform(820, 1860)) for _ in range(150)]
        gp += [(rr.uniform(300, 1060), rr.uniform(1310, 1480)) for _ in range(120)]           # under the seat front
        draw_crumbs(im, gp, 51, 5, 12)
    return im

# ---------------- seat sprite (RGBA, full frame, so it can slide back) ----------------
def make_seat(state):
    rng = np.random.default_rng(26)
    grain = rng.normal(0, 1, (H, W)).astype(np.float32)
    weave = (np.sin(XF * 1.15) * np.sin(YF * 1.15)) * 5 + np.sin((XF + YF) * 0.35) * 3
    ins_col = np.array([62, 68, 78], np.float32) + (weave + (lowfreq(3, 6) - 0.5) * 14 + grain * 3)[..., None]
    bol_col = np.array([40, 43, 50], np.float32) + (grain * 3 + (lowfreq(4, 8) - 0.5) * 10)[..., None]
    back_out = poly([(300, 120), (1040, 120), (1062, SEAM_Y), (280, SEAM_Y)], 3)
    back_ins = poly([(430, 150), (900, 150), (918, SEAM_Y - 18), (414, SEAM_Y - 18)], 2)
    cush_out = poly([(272, SEAM_Y - 8), (1080, SEAM_Y - 8), (1100, 1420), (GAP_X1, 1420)], 3)
    cush_ins = poly([(400, SEAM_Y + 22), (935, SEAM_Y + 22), (968, 1395), (382, 1395)], 2)
    front = poly([(GAP_X1, 1418), (1100, 1418), (1100, 1500), (GAP_X1 + 10, 1500)], 3)
    sh_b = np.clip((YF - 120) / 780, 0, 1); sh_c = np.clip((YF - SEAM_Y) / 520, 0, 1)
    z = np.zeros((H, W, 3), np.float32)
    seat = blend(z, [(bol_col - (sh_b * 14)[..., None], back_out), (ins_col - (sh_b * 18)[..., None], back_ins)])
    seat = blend(seat, [(bol_col + (14 - sh_c * 22)[..., None], cush_out), (ins_col + (16 - sh_c * 24)[..., None], cush_ins),
                        (bol_col * 0.72, front)])
    seat += (np.exp(-((YF - SEAM_Y - 6) / 13) ** 2) * -42 * np.clip(cush_out + back_out, 0, 1))[..., None]
    alpha = np.clip(back_out + cush_out + front, 0, 1)
    im = to_img(seat); im.putalpha(Image.fromarray((alpha * 255).astype(np.uint8)))
    d = ImageDraw.Draw(im)
    for (x0, y0), (x1, y1) in ([(400, SEAM_Y + 22), (382, 1395)], [(935, SEAM_Y + 22), (968, 1395)],
                               [(430, 150), (414, SEAM_Y - 18)], [(900, 150), (918, SEAM_Y - 18)]):
        n = 44
        for i in range(0, n, 2):
            a, b = i / n, (i + 0.6) / n
            d.line([(x0 + (x1 - x0) * a + 10, y0 + (y1 - y0) * a), (x0 + (x1 - x0) * b + 10, y0 + (y1 - y0) * b)], fill=(28, 32, 38), width=4)
    d.line([(390, 1160), (950, 1160)], fill=(50, 56, 66), width=6)
    rr = random.Random(9)
    if state == "dirty":
        pts = [(rr.uniform(300, 1050), SEAM_Y + rr.uniform(-9, 10)) for _ in range(170)]       # packed in the bight
        pts += [(rr.uniform(310, 1040), rr.uniform(SEAM_Y + 30, SEAM_Y + 150)) for _ in range(30)]
        draw_crumbs(im, pts, 61, 5, 13)
    elif state == "loose":                                                                       # brushed up onto the cushion
        pts = [(rr.uniform(300, 1050), SEAM_Y + 22 + min(125, abs(rr.gauss(0, 50)))) for _ in range(170)]
        pts += [(rr.uniform(310, 1040), rr.uniform(SEAM_Y + 30, SEAM_Y + 150)) for _ in range(30)]
        draw_crumbs(im, pts, 61, 6, 14)
    return im

FLOOR_D, FLOOR_C = make_floor(True), make_floor(False)
SEAT_D, SEAT_L, SEAT_C = make_seat("dirty"), make_seat("loose"), make_seat("clean")

def compose(floor, seat, s=1.0):
    im = floor.copy()
    if s >= 0.999: im.alpha_composite(seat)
    else:
        sp = seat.resize((int(W * s), int(H * s)), Image.BICUBIC)
        im.alpha_composite(sp, (int(SC_CX - SC_CX * s), int(SC_CY - SC_CY * s)))
    return im

def arr(im): return np.array(im.convert("RGB")).astype(np.float32)
DIRTY_FULL = arr(compose(FLOOR_D, SEAT_D))
LOOSE_FULL = arr(compose(FLOOR_D, SEAT_L))
CLEAN = arr(compose(FLOOR_C, SEAT_C))

def zoom_arr(a, z=1.3, cx=560, cy=1000):
    cw, ch = W / z, H / z
    box = (int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))
    im = Image.fromarray(a.astype(np.uint8)).crop(box).resize((W, H), Image.LANCZOS)
    return np.array(im).astype(np.float32)

# ---------------- scenes ----------------
TOTAL = 3
HOOK = make_hook(zoom_arr(DIRTY_FULL), zoom_arr(CLEAN), [("IT'S NOT", 150, YELLOW), ("YOUR VACUUM", 150, YELLOW)],
                 "CRUMBS HIDE IN THE SEAMS", mark_xy=(300, 860), check_xy=(800, 900), split_to=0.5, labels=True)
HOOK_D = 2.4

# step 1: slide the seat back -> the gap and rails show their crumbs, then forward again
C1 = make_card(1, "Slide the seat back", "Then forward. Look in the gaps.", TOTAL)
def x_slide(t, D):
    s = 1 - 0.14 * ease_io(seg(t, 0.25, 1.05)) + 0.14 * ease_io(seg(t, D - 0.75, D - 0.1))
    im = compose(FLOOR_D, SEAT_D, s)
    d = ImageDraw.Draw(im)
    q = ease(seg(t, 0.9, 1.4)) * (1 - ease(seg(t, D - 0.8, D - 0.6)))
    if q > 0:
        ring(d, 250, 1240, 110, q); ring(d, 700, 1420, 130, ease(seg(t, 1.05, 1.55)) * (1 - ease(seg(t, D - 0.8, D - 0.6))))
    # direction arrow on the cushion
    a = ease(seg(t, 0.15, 0.4)) * (1 - ease(seg(t, 1.0, 1.2)))
    if a > 0:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        ld.line([(700, 1330), (700, 1110)], fill=(255, 255, 255, int(235 * a)), width=26)
        ld.polygon([(650, 1120), (750, 1120), (700, 1040)], fill=(255, 255, 255, int(235 * a)))
        im.alpha_composite(lay)
    pill(im, W // 2, PILL_Y, "CRUMBS HIDE IN THE GAP", F("Bold", 46), ACC2, INK, ease(seg(t, 0.3, 0.6)))
    return im

# step 2: spread the seam + soft brush: crumbs come up out of the bight
BPATH = [(1040 - 740 * i / 10, SEAM_Y + 6 + 10 * math.sin(i * 1.7)) for i in range(11)]
C2 = make_card(2, "Brush them loose", "Spread the seam, flick crumbs up.", TOTAL)
def x_brush(t, D):
    t0 = 0.2
    p = ease_io(seg(t, t0, D - 0.15)) * (len(BPATH) - 1)
    m = trail_mask(BPATH, p, radius=120, blur=18) if t > t0 else 0
    im = to_img(blend(DIRTY_FULL, [(LOOSE_FULL, m)]))
    x, y = path_point(BPATH, p)
    detail_brush(im, x + 6 * math.sin(t * 40), y - 4, ang=-30 + 10 * math.sin(t * 22))
    pill(im, W // 2, PILL_Y, "LOOSEN FIRST", F("Bold", 46), ACC2, INK, ease(seg(t, 0.3, 0.6)))
    return im

# step 3: crevice tool, slow pass: along the seam, then down the console gap
VPATH = ([(1040 - 740 * i / 8, SEAM_Y + 40) for i in range(9)] +
         [(GAP_X0 + 40, SEAM_Y + 120), (GAP_X0 + 40, 1150), (GAP_X0 + 40, 1350), (GAP_X0 + 40, 1600), (GAP_X0 + 40, 1880)])
C3 = make_card(3, "Then vacuum, slowly", "Crevice tool: seam, then the gap.", TOTAL)
SP3 = [(330, 960), (620, 940), (900, 1000), (230, 1250), (560, 1200), (840, 1300)]
def x_vac(t, D):
    t0 = 0.15; t1 = D - 0.55
    p = ease_io(seg(t, t0, t1)) * (len(VPATH) - 1)
    m = trail_mask(VPATH, p, radius=135, blur=16) if t > t0 else 0
    im = to_img(blend(LOOSE_FULL, [(CLEAN, m)]))
    x, y = path_point(VPATH, p)
    if t < t1 + 0.1: crevice_tool(im, x, y, wand_to=(x + 560, y + 950))
    if t > t1: sparkles(im, t, t1, 1.0, SP3)
    pill(im, W // 2, PILL_Y, "SLOW PASS, NO DIGGING", F("Bold", 46), ACC2, INK, ease(seg(t, 0.3, 0.6)))
    return im

SP = [(330, 980), (620, 950), (880, 1050), (430, 1250), (760, 1300), (230, 1200), (900, 1450)]
_BA = make_ba(DIRTY_FULL, CLEAN, y_label=SAFE_TOP + 120, handle_y=1150, spark_pts=SP)
def BA(t, D): return _BA(t, D)
BA.impact_at = _BA.impact_at

_OUT = make_loop_outro(CLEAN, HOOK(0.0, HOOK_D), ask="Kids or snacks: who's guilty?")
def OUTRO(t, D): return _OUT(t, D)

SCENES = [
    ("01_hook", HOOK, HOOK_D),
    ("02_slide", with_card(C1, x_slide), 2.6),
    ("03_brush", with_card(C2, x_brush), 2.5),
    ("04_vac", with_card(C3, x_vac), 2.7),
    ("05_ba", BA, 2.5),
    ("06_outro", OUTRO, 2.4),
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
