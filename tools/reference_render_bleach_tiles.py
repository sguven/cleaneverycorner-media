import math, os, sys, subprocess, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
FD = "/usr/share/fonts/truetype/google-fonts/"
def F(w, s): return ImageFont.truetype(FD + f"Poppins-{w}.ttf", s)

INK = (24, 38, 52)
ACCENT = (14, 150, 170)
ACC2 = (255, 196, 40)
RED = (226, 64, 64)
GREEN = (40, 170, 100)
BLUE = (70, 150, 230)

# ---------- easing ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_io(x): x = clamp(x); return 3 * x * x - 2 * x * x * x
def back(x):
    x = clamp(x); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def seg(t, a, b): return clamp((t - a) / (b - a))

# ---------- tile backgrounds ----------
TILE, GROUT = 200, 16
PITCH = TILE + GROUT
OFFY = 40
yy, xx = np.mgrid[0:H, 0:W]
gx = (xx % PITCH) >= TILE
gy = ((yy + OFFY) % PITCH) >= TILE
GROUT_M = (gx | gy).astype(np.float32)

def make_bgs():
    rng = np.random.default_rng(7)
    noise = rng.normal(0, 1, (H, W)).astype(np.float32)
    # blotchy low-freq dirt
    small = rng.random((H // 60 + 2, W // 60 + 2)).astype(np.float32)
    blot = np.array(Image.fromarray((small * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)).astype(np.float32) / 255
    # per-tile gloss gradient
    lx = (xx % PITCH) / TILE; ly = ((yy + OFFY) % PITCH) / TILE
    gloss = np.clip(1 - np.abs((lx + ly) - 0.7) * 2.2, 0, 1) ** 2
    g = GROUT_M[..., None]

    tile_clean = np.array([246, 249, 251], np.float32) + gloss[..., None] * 8
    grout_clean = np.array([236, 237, 235], np.float32) + noise[..., None] * 3
    clean = tile_clean * (1 - g) + grout_clean * g

    tile_dirty = np.array([226, 219, 200], np.float32) - blot[..., None] * np.array([30, 34, 40]) + noise[..., None] * 3 + gloss[..., None] * 4
    grout_dirty = np.array([96, 84, 66], np.float32) - blot[..., None] * 28 + noise[..., None] * 10
    dirty = tile_dirty * (1 - g) + grout_dirty * g
    # mildew specks near grout
    img = Image.fromarray(np.clip(dirty, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    r2 = random.Random(3)
    for _ in range(900):
        if r2.random() < 0.5:
            x = r2.randrange(W); y = (r2.randrange(10) * PITCH - OFFY + TILE + r2.randint(-10, 22))
        else:
            y = r2.randrange(H); x = r2.randrange(6) * PITCH + TILE + r2.randint(-10, 22)
        rr = r2.randint(2, 6)
        c = r2.choice([(60, 66, 50), (80, 72, 55), (50, 56, 48)])
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=c)
    img = img.filter(ImageFilter.GaussianBlur(1.2))
    dirty = np.array(img).astype(np.float32)
    wet = dirty * 0.82 + np.array([30, 60, 90], np.float32) * 0.18 * 2.2
    wet = np.minimum(wet, 255)
    return dirty, clean, wet

DIRTY, CLEAN, WET = make_bgs()

def compose(clean_m=None, wet_m=None):
    f = DIRTY
    if wet_m is not None:
        f = f * (1 - wet_m[..., None]) + WET * wet_m[..., None]
    if clean_m is not None:
        f = f * (1 - clean_m[..., None]) + CLEAN * clean_m[..., None]
    return f

def to_img(arr): return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")

# ---------- UI pieces ----------
def rrect(d, box, r, **kw): d.rounded_rectangle(box, r, **kw)

def wrap(text, font, maxw):
    words = text.split(); lines = []; cur = ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if font.getlength(t) <= maxw: cur = t
        else: lines.append(cur); cur = w_
    if cur: lines.append(cur)
    return lines

def make_card(step, title, sub, total=5, width=940):
    fT, fS, fP = F("Bold", 84), F("Medium", 46), F("Bold", 34)
    sub_lines = []
    for s in sub.split("\n"): sub_lines += wrap(s, fS, width - 120)
    h = 60 + (80 if step else 0) + 100 + len(sub_lines) * 62 + 50
    pad = 40
    im = Image.new("RGBA", (width + pad * 2, h + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([pad, pad + 14, pad + width, pad + h + 14], 48, fill=(10, 30, 40, 90))
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    im.alpha_composite(sh)
    d = ImageDraw.Draw(im)
    rrect(d, [pad, pad, pad + width, pad + h], 48, fill=(255, 255, 255, 246))
    x0, y = pad + 60, pad + 56
    if step:
        label = f"STEP {step}"
        lw = fP.getlength(label) + 52
        rrect(d, [x0, y, x0 + lw, y + 60], 30, fill=ACCENT)
        d.text((x0 + 26, y + 30), label, font=fP, fill="white", anchor="lm")
        # progress dots
        for i in range(total):
            cx = pad + width - 60 - (total - 1 - i) * 38
            c = ACCENT if i < step else (210, 222, 226)
            d.ellipse([cx - 11, y + 19, cx + 11, y + 41], fill=c)
        y += 88
    d.text((x0, y), title, font=fT, fill=INK, anchor="lt")
    y += 108
    for ln in sub_lines:
        d.text((x0, y), ln, font=fS, fill=(80, 96, 110), anchor="lt"); y += 62
    return im

def paste_card(frame, card, t_in, t, y=250, t_out=None):
    p = ease(seg(t, t_in, t_in + 0.45))
    if t_out is not None: p = min(p, 1 - ease_io(seg(t, t_out, t_out + 0.3)))
    if p <= 0: return
    c = card
    if p < 1:
        c = card.copy(); a = c.getchannel("A").point(lambda v: int(v * p)); c.putalpha(a)
    x = (W - card.width) // 2
    frame.alpha_composite(c, (x, int(y + (1 - p) * 80)))

def sparkle(d, cx, cy, r, col=(255, 255, 255, 255)):
    if r <= 1: return
    k = r * 0.22
    pts = [(cx, cy - r), (cx + k, cy - k), (cx + r, cy), (cx + k, cy + k), (cx, cy + r), (cx - k, cy + k), (cx - r, cy), (cx - k, cy - k)]
    d.polygon(pts, fill=col)

SPARKS = [(160, 1060), (860, 980), (520, 1200), (300, 1420), (780, 1390), (930, 1230), (120, 1270), (620, 960)]
def sparkles(img, t, t0, strength=1.0):
    d = ImageDraw.Draw(img)
    for i, (x, y) in enumerate(SPARKS):
        ph = (t - t0) * 2.2 - i * 0.37
        if ph < 0: continue
        s = max(0, math.sin(ph * math.pi)) if ph < 1 else max(0, math.sin((ph % 1.6) / 1.6 * math.pi)) * 0.8
        sparkle(d, x, y, 46 * s * strength, (255, 255, 255, 240))
        sparkle(d, x, y, 20 * s * strength, (255, 245, 190, 255))

def soft_disc(img, cx, cy, r, alpha=200):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, alpha))
    lay = lay.filter(ImageFilter.GaussianBlur(10))
    img.alpha_composite(lay)

# ---------- illustrations ----------
def spray_bottle(img, x, y, s=1.0, squeeze=0.0):
    d = ImageDraw.Draw(img)
    def S(v): return v * s
    # body
    rrect(d, [x - S(95), y - S(40), x + S(95), y + S(300)], int(S(40)), fill=(255, 255, 255), outline=INK, width=8)
    rrect(d, [x - S(80), y + S(60), x + S(80), y + S(285)], int(S(30)), fill=(150, 210, 240))
    rrect(d, [x - S(60), y + S(110), x + S(60), y + S(200)], int(S(12)), fill=(255, 255, 255))
    d.text((x, y + S(155)), "BLEACH", font=F("Bold", int(S(30))), fill=INK, anchor="mm")
    # neck + head
    rrect(d, [x - S(45), y - S(95), x + S(45), y - S(35)], 10, fill=ACCENT, outline=INK, width=8)
    d.polygon([(x - S(70), y - S(95)), (x + S(60), y - S(95)), (x + S(60), y - S(165)), (x - S(150), y - S(165)), (x - S(150), y - S(130))], fill=ACCENT, outline=INK, width=8)
    # nozzle
    rrect(d, [x - S(185), y - S(160), x - S(145), y - S(130)], 6, fill=INK)
    # trigger
    ang = squeeze * 12
    tx = x - S(70) + ang
    d.polygon([(tx, y - S(95)), (tx - S(30), y - S(10)), (tx - S(5), y - S(10)), (tx + S(25), y - S(95))], fill=ACC2, outline=INK, width=6)
    return (x - S(185), y - S(145))

def mist(img, nx, ny, t, dirn=-1, strength=1.0):
    d = ImageDraw.Draw(img)
    rng = random.Random(int(t * 30))
    for i in range(70):
        dist = rng.random() ** 0.7 * 380
        a = rng.uniform(-0.45, 0.45)
        px = nx + dirn * dist * math.cos(a); py = ny + dist * math.sin(a) + dist * 0.25
        r = 3 + rng.random() * 7
        al = int(220 * (1 - dist / 400) * strength)
        d.ellipse([px - r, py - r, px + r, py + r], fill=(190, 230, 255, al))

def brush(img, x, y, ang=0):
    lay = Image.new("RGBA", (520, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    rrect(d, [20, 40, 500, 140], 50, fill=ACCENT, outline=INK, width=8)
    rrect(d, [330, 70, 470, 110], 20, fill=(255, 255, 255, 120))
    rrect(d, [40, 130, 360, 160], 8, fill=(255, 255, 255), outline=INK, width=6)
    for i in range(14):
        bx = 55 + i * 22
        d.rectangle([bx, 160, bx + 12, 240], fill=ACC2, outline=(180, 130, 0))
    lay = lay.rotate(ang, resample=Image.BICUBIC, center=(200, 200))
    img.alpha_composite(lay, (int(x - 200), int(y - 240)))

def bucket(img, cx, cy, fill_p, t):
    d = ImageDraw.Draw(img)
    top, bot = cy - 170, cy + 170
    wt, wb = 200, 150
    # handle
    d.arc([cx - wt, top - 150, cx + wt, top + 150], 190, 350, fill=INK, width=10)
    poly = [(cx - wt, top), (cx + wt, top), (cx + wb, bot), (cx - wb, bot)]
    d.polygon(poly, fill=(225, 236, 242), outline=INK, width=10)
    if fill_p > 0:
        ly = bot - (bot - top - 30) * fill_p
        k = (ly - top) / (bot - top)
        hw = wt + (wb - wt) * k
        pts = [(cx - hw + 10, ly)]
        for i in range(21):
            xx_ = cx - hw + 10 + (2 * hw - 20) * i / 20
            pts.append((xx_, ly + math.sin(i * 0.9 + t * 8) * 6))
        pts += [(cx + wb - 10, bot - 8), (cx - wb + 10, bot - 8)]
        d.polygon(pts, fill=(150, 205, 240))
    d.line([(cx - wt, top), (cx + wt, top)], fill=INK, width=12)

def timer(img, cx, cy, p, label):
    d = ImageDraw.Draw(img)
    R = 190
    d.ellipse([cx - R - 14, cy - R - 14, cx + R + 14, cy + R + 14], fill=(255, 255, 255), outline=INK, width=10)
    rrect(d, [cx - 30, cy - R - 60, cx + 30, cy - R - 20], 10, fill=INK)
    d.arc([cx - R + 14, cy - R + 14, cx + R - 14, cy + R - 14], 0, 360, fill=(220, 232, 236), width=34)
    if p > 0:
        d.arc([cx - R + 14, cy - R + 14, cx + R - 14, cy + R - 14], -90, -90 + 360 * p, fill=ACCENT, width=34)
    d.text((cx, cy - 10), label, font=F("Bold", 92), fill=INK, anchor="mm")
    d.text((cx, cy + 66), "min", font=F("Medium", 42), fill=(110, 124, 136), anchor="mm")

def towel(img, x, y, ang=0):
    lay = Image.new("RGBA", (420, 420), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    rrect(d, [60, 110, 360, 310], 30, fill=(255, 150, 120), outline=INK, width=8)
    for i in range(3):
        d.line([(80, 170 + i * 50), (340, 170 + i * 50)], fill=(255, 205, 185), width=10)
    lay = lay.rotate(ang, resample=Image.BICUBIC)
    img.alpha_composite(lay, (int(x - 210), int(y - 210)))

def bubbles(img, t, t0, region_mask_pts):
    d = ImageDraw.Draw(img)
    for i, (x, y) in enumerate(region_mask_pts):
        ph = (t - t0) * 1.4 + (i * 0.618) % 1
        if t < t0: continue
        f = ph % 1
        r = 5 + 14 * f
        al = int(230 * (1 - f))
        d.ellipse([x - r, y - r - f * 30, x + r, y + r - f * 30], outline=(255, 255, 255, al), width=4)

# grout points for bubbles
BUB = []
rb = random.Random(11)
for _ in range(60):
    if rb.random() < 0.5:
        BUB.append((rb.randrange(30, W - 30), rb.randrange(4, 9) * PITCH - OFFY + TILE + 8))
    else:
        BUB.append((rb.randrange(5) * PITCH + TILE + 8, rb.randrange(880, 1560)))

# ---------- scenes ----------
def sc_hook(t, D):
    z = 1.0
    base = to_img(compose())
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for i in range(H):
        a = int(200 * max(0, 1 - i / 1150))
        od.line([(0, i), (W, i)], fill=(8, 22, 34, a))
    base.alpha_composite(ov)
    d = ImageDraw.Draw(base)
    lines = [("HOW TO", F("Bold", 92), (255, 255, 255), 0.15),
             ("BLEACH", F("Bold", 210), ACC2, 0.35),
             ("YOUR TILES", F("Bold", 120), (255, 255, 255), 0.55)]
    y = 300
    for txt, f, col, st in lines:
        p = back(seg(t, st, st + 0.5))
        a = int(255 * ease(seg(t, st, st + 0.3)))
        lay = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
        ImageDraw.Draw(lay).text((W // 2, 130), txt, font=f, fill=col + (a,), anchor="mm")
        if p > 0:
            sc = 0.6 + 0.4 * p
            lw, lh = int(W * sc), int(260 * sc)
            l2 = lay.resize((lw, lh), Image.BICUBIC)
            base.alpha_composite(l2, ((W - lw) // 2, int(y + (260 - lh) / 2)))
        y += {92: 150, 210: 210, 120: 160}[f.size]
    p = ease(seg(t, 1.1, 1.6))
    if p > 0:
        f = F("Medium", 50)
        txt = "Dirty grout to like-new in 5 steps"
        tw = f.getlength(txt) + 80
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        yy_ = 930 + (1 - p) * 40
        rrect(ld, [(W - tw) / 2, yy_, (W + tw) / 2, yy_ + 96], 48, fill=(255, 255, 255, int(235 * p)))
        ld.text((W / 2, yy_ + 48), txt, font=f, fill=INK + (int(255 * p),), anchor="mm")
        base.alpha_composite(lay)
    q = back(seg(t, 1.5, 2.1))
    if q > 0.12:
        soft_disc(base, W // 2, 1330, int(250 * q), 170)
        spray_bottle(base, W // 2 + 40, 1260 + math.sin(t * 3) * 12, 0.95 * q, 0)
    return base

CARD_SAFETY = None
def sc_safety(t, D):
    base = to_img(compose())
    d = ImageDraw.Draw(base)
    ov = Image.new("RGBA", (W, H), (8, 22, 34, int(120 * ease(seg(t, 0, 0.4)))))
    base.alpha_composite(ov)
    p = ease(seg(t, 0.0, 0.45))
    pad, width = 40, 940
    x0 = (W - width) // 2
    top = 250 + (1 - p) * 80
    rows = [("ok", "Wear rubber gloves"), ("ok", "Open a window or run the fan"),
            ("no", "NEVER mix bleach with ammonia or vinegar"), ("no", "Not for marble or natural stone"),
            ("ok", "Test colored grout in a hidden spot")]
    h = 1180
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    rrect(ld, [x0, top, x0 + width, top + h], 48, fill=(255, 255, 255, int(246 * p)))
    if p > 0.05:
        f = F("Bold", 34); lbl = "BEFORE YOU START"; lw = f.getlength(lbl) + 52
        rrect(ld, [x0 + 60, top + 56, x0 + 60 + lw, top + 116], 30, fill=RED + (int(255 * p),))
        ld.text((x0 + 86, top + 86), lbl, font=f, fill=(255, 255, 255, int(255 * p)), anchor="lm")
        ld.text((x0 + 60, top + 150), "Safety first", font=F("Bold", 84), fill=INK + (int(255 * p),), anchor="lt")
    base.alpha_composite(lay)
    d = ImageDraw.Draw(base)
    fR = F("Medium", 46); fRb = F("Bold", 46)
    y = top + 300
    for i, (kind, txt) in enumerate(rows):
        st = 0.5 + i * 0.55
        q = ease(seg(t, st, st + 0.35))
        if q <= 0:
            y += 0;
        lines = wrap(txt, fRb if kind == "no" and i == 2 else fR, width - 200)
        if q > 0:
            lay = Image.new("RGBA", (W, 300), (0, 0, 0, 0)); l2 = ImageDraw.Draw(lay)
            cx, cy = x0 + 105, 50
            col = GREEN if kind == "ok" else RED
            l2.ellipse([cx - 38, cy - 38, cx + 38, cy + 38], fill=col)
            if kind == "ok":
                l2.line([(cx - 17, cy + 1), (cx - 4, cy + 15), (cx + 19, cy - 14)], fill="white", width=10, joint="curve")
            else:
                l2.line([(cx - 14, cy - 14), (cx + 14, cy + 14)], fill="white", width=10)
                l2.line([(cx - 14, cy + 14), (cx + 14, cy - 14)], fill="white", width=10)
            ty = cy - (len(lines) - 1) * 31
            for ln in lines:
                l2.text((x0 + 170, ty), ln, font=fRb if (kind == "no" and i == 2) else fR,
                        fill=(RED if (kind == "no" and i == 2) else INK), anchor="lm"); ty += 62
            a = lay.getchannel("A").point(lambda v: int(v * q)); lay.putalpha(a)
            base.alpha_composite(lay, (int((1 - q) * 60), int(y - 50)))
        y += 70 + len(lines) * 62 + 20
    return base

def scene_with_card(card, extra):
    def f(t, D):
        base = extra(t, D)
        paste_card(base, card, 0.0, t)
        return base
    return f

CARD1 = make_card(1, "Mix it", "1 part bleach : 10 parts water")
def x_mix(t, D):
    base = to_img(compose())
    soft_disc(base, W // 2, 1360, 330, 170)
    d = ImageDraw.Draw(base)
    pq = ease(seg(t, 0.35, 0.7))
    if pq > 0:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        rrect(ImageDraw.Draw(lay), [60, 880, W - 60, 1080], 40, fill=(255, 255, 255, int(235 * pq)))
        base.alpha_composite(lay)
    # ratio blocks
    n = 11; bw = 66; gap = 12; tot = n * bw + (n - 1) * gap; x = (W - tot) // 2
    for i in range(n):
        q = back(seg(t, 0.5 + i * 0.12, 0.8 + i * 0.12))
        if q <= 0: continue
        col = ACC2 if i == 0 else BLUE
        cx = x + i * (bw + gap) + bw / 2; cy = 950
        s = bw / 2 * q
        # droplet
        d.ellipse([cx - s, cy - s * 0.6, cx + s, cy + s * 1.2], fill=col)
        d.polygon([(cx - s * 0.75, cy), (cx, cy - s * 1.4), (cx + s * 0.75, cy)], fill=col)
    if t > 0.6:
        f = F("Bold", 34)
        d.text((x + bw / 2, 1040), "1", font=f, fill=INK, anchor="mm")
        if t > 1.9: d.text((x + bw + gap + (tot - bw - gap) / 2, 1040), "10", font=f, fill=INK, anchor="mm")
    bucket(base, W // 2, 1400, ease_io(seg(t, 0.8, 3.0)) * 0.85, t)
    return base

CARD2 = make_card(2, "Spray it", "Soak the tiles and every grout line")
def x_apply(t, D):
    p = ease_io(seg(t, 0.4, D - 0.4))
    bx = 900 - p * 640
    by = 1230 + math.sin(p * math.pi * 3) * 120
    sweep = bx - 200
    wet = np.clip((xx.astype(np.float32) - sweep) / 120 + 0.0, 0, 1) * (yy > 700)
    wet = wet * (t > 0.4)
    base = to_img(compose(wet_m=wet.astype(np.float32)))
    squeeze = 1.0 if (int(t * 6) % 2 == 0 and 0.4 < t < D - 0.4) else 0.0
    nx, ny = spray_bottle(base, bx + 120, by, 1.0, squeeze)
    if 0.4 < t < D - 0.3:
        mist(base, nx, ny, t, -1, 1.0)
    return base

CARD3 = make_card(3, "Let it sit", "5–10 minutes. Don't let it dry out!")
def x_wait(t, D):
    base = to_img(compose(wet_m=np.full((H, W), 1.0, np.float32)))
    bubbles(base, t, 0.3, BUB)
    soft_disc(base, W // 2, 1230, 270, 140)
    p = ease_io(seg(t, 0.4, D - 0.3))
    timer(base, W // 2, 1240, p, str(int(round(p * 10))))
    return base

CARD4 = make_card(4, "Scrub", "Stiff brush or old toothbrush along the grout")
def x_scrub(t, D):
    # brush zigzags across 3 horizontal grout rows
    rows = [4, 5, 6]
    seg_d = (D - 0.6) / len(rows)
    tt = t - 0.3
    m = np.zeros((H, W), np.float32)
    bx, by = W / 2, rows[0] * PITCH - OFFY + TILE + 8
    for k, r in enumerate(rows):
        gyr = r * PITCH - OFFY + TILE + 8
        q = clamp((tt - k * seg_d) / seg_d)
        if q <= 0: break
        lr = (k % 2 == 0)
        reach = 1080 * ease_io(q)
        xr = reach if lr else W - reach
        band = np.clip(1 - np.abs(yy - gyr) / (PITCH * 0.6), 0, 1).astype(np.float32) ** 0.5
        sel = np.clip(((xr - xx) if lr else (xx - xr)) / 60.0, 0, 1).astype(np.float32)
        m = np.maximum(m, band * sel)
        bx = xr + math.sin(t * 40) * 25; by = gyr
    cm = m * (0.55 + 0.45 * GROUT_M)
    base = to_img(compose(clean_m=cm, wet_m=np.full((H, W), 0.6, np.float32)))
    # foam
    d = ImageDraw.Draw(base)
    rng = random.Random(int(t * 15))
    for _ in range(14):
        fx = bx + rng.uniform(-120, 120); fy = by + rng.uniform(-40, 40); r = rng.uniform(8, 22)
        d.ellipse([fx - r, fy - r, fx + r, fy + r], fill=(255, 255, 255, 220), outline=(200, 225, 240), width=2)
    brush(base, bx, by - 10, ang=math.sin(t * 40) * 4)
    return base

CARD5 = make_card(5, "Rinse & dry", "Wipe with clean water, then dry with a towel")
def x_rinse(t, D):
    p = ease_io(seg(t, 0.4, D - 1.0))
    edge = -150 + p * (W + 300)
    m = np.clip((edge - xx.astype(np.float32)) / 150, 0, 1)
    base = to_img(compose(clean_m=m, wet_m=np.full((H, W), 0.5, np.float32)))
    if 0.3 < t < D - 0.9:
        towel(base, edge, 1250 + math.sin(t * 9) * 140, ang=math.sin(t * 9) * 10)
    if t > D - 1.2:
        sparkles(base, t, D - 1.2)
    return base

def sc_ba(t, D):
    p = ease_io(seg(t, 0.4, 2.2))
    split = W - p * W * 0.5
    m = (xx >= split).astype(np.float32)
    base = to_img(compose(clean_m=m))
    d = ImageDraw.Draw(base)
    d.line([(split, 0), (split, H)], fill=(255, 255, 255), width=10)
    d.ellipse([split - 50, 1190 - 50, split + 50, 1190 + 50], fill="white", outline=INK, width=6)
    d.polygon([(split - 30, 1190), (split - 10, 1172), (split - 10, 1208)], fill=INK)
    d.polygon([(split + 30, 1190), (split + 10, 1172), (split + 10, 1208)], fill=INK)
    f = F("Bold", 56)
    q = ease(seg(t, 0.2, 0.6))
    for txt, cx, show in [("BEFORE", min(split, W) / 2, 1.0), ("AFTER", split + (W - split) / 2, ease(seg(t, 1.0, 1.5)))]:
        a = q * show
        if a <= 0: continue
        tw = f.getlength(txt) + 70
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        col = (40, 40, 40) if txt == "BEFORE" else ACCENT
        rrect(ld, [cx - tw / 2, 330, cx + tw / 2, 430], 50, fill=col + (int(240 * a),))
        ld.text((cx, 380), txt, font=f, fill=(255, 255, 255, int(255 * a)), anchor="mm")
        base.alpha_composite(lay)
    if t > 2.0:
        sp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sparkles(sp, t, 2.0)
        mask = Image.fromarray(((xx >= split) * 255).astype(np.uint8))
        a = Image.fromarray(np.minimum(np.array(sp.getchannel("A")), np.array(mask)))
        sp.putalpha(a)
        base.alpha_composite(sp)
    return base

def sc_outro(t, D):
    base = to_img(CLEAN)
    sparkles(base, t, 0.0, 0.8)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    p = ease(seg(t, 0.1, 0.6))
    top = 520 + (1 - p) * 60
    rrect(ld, [70, top, W - 70, top + 640], 56, fill=ACCENT + (int(245 * p),))
    a = int(255 * p)
    # bookmark icon
    bx, by = W / 2, top + 140
    ld.polygon([(bx - 48, by - 70), (bx + 48, by - 70), (bx + 48, by + 70), (bx, by + 30), (bx - 48, by + 70)], fill=(255, 255, 255, a))
    ld.text((W / 2, top + 290), "Save this for", font=F("Bold", 76), fill=(255, 255, 255, a), anchor="mm")
    ld.text((W / 2, top + 380), "cleaning day!", font=F("Bold", 76), fill=ACC2 + (a,), anchor="mm")
    q = ease(seg(t, 0.9, 1.4))
    rrect(ld, [W / 2 - 330, top + 470, W / 2 + 330, top + 570], 50, fill=(255, 255, 255, int(255 * q)))
    ld.text((W / 2, top + 520), "Follow @cleaneverycorner", font=F("Bold", 42), fill=ACCENT + (int(255 * q),), anchor="mm")
    base.alpha_composite(lay)
    return base

SCENES = [
    ("01_hook", sc_hook, 3.3),
    ("02_safety", sc_safety, 6.0),
    ("03_mix", scene_with_card(CARD1, x_mix), 4.0),
    ("04_apply", scene_with_card(CARD2, x_apply), 4.0),
    ("05_wait", scene_with_card(CARD3, x_wait), 3.6),
    ("06_scrub", scene_with_card(CARD4, x_scrub), 4.6),
    ("07_rinse", scene_with_card(CARD5, x_rinse), 4.4),
    ("08_ba", sc_ba, 4.0),
    ("09_outro", sc_outro, 3.6),
]

def render_scene(i):
    name, fn, D = SCENES[i]
    n = int(round(D * FPS))
    out = f"/home/claude/tiles/out/{name}.mp4"; tmp = out[:-4] + ".tmp.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), tmp]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k in range(n):
        t = k / FPS
        fr = fn(t, D).convert("RGB")
        # fade in from previous for the first scene / to black? only quick fade-in on hook
        pr.stdin.write(fr.tobytes())
    pr.stdin.close()
    if pr.wait() == 0: os.replace(tmp, out)
    return name

if __name__ == "__main__":
    os.makedirs("/home/claude/tiles/out", exist_ok=True)
    os.makedirs("/home/claude/tiles/stills", exist_ok=True)
    if sys.argv[1] == "stills":
        for i, (name, fn, D) in enumerate(SCENES):
            for frac in (0.55, 0.95):
                fn(D * frac, D).convert("RGB").save(f"/home/claude/tiles/stills/{name}_{int(frac*100)}.jpg", quality=85)
    else:
        from multiprocessing import Pool
        with Pool(2) as p:
            for r in p.imap_unordered(render_scene, range(len(SCENES))): print("done", r, flush=True)
