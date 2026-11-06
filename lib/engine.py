"""Shared render engine for @cleaneverycorner Reels.

Look extracted from tools/reference_render_bleach_tiles.py. A daily script only has to
provide backgrounds (numpy float arrays HxWx3), its illustrations and the scene list.

    from lib.engine import *
    SCENES = [("01_hook", make_hook(...), 3.3), ...]
    build(SCENES, workdir, out_mp4, music_fn)   # renders scenes, concat -c copy, mux audio
"""
import math, os, sys, subprocess, random, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
SAFE_TOP, SAFE_BOT = 250, 1920 - 350          # keep text inside [250, 1570]
FD = "/usr/share/fonts/truetype/google-fonts/"
_FC = {}
def F(w, s):
    k = (w, int(s))
    if k not in _FC: _FC[k] = ImageFont.truetype(FD + f"Poppins-{w}.ttf", int(s))
    return _FC[k]

INK = (24, 38, 52)
ACCENT = TEAL = (14, 150, 170)
ACC2 = YELLOW = (255, 196, 40)
RED = (226, 64, 64)
GREEN = (40, 170, 100)
BLUE = (70, 150, 230)
GREY_TXT = (80, 96, 110)

yy, xx = np.mgrid[0:H, 0:W]
XF, YF = xx.astype(np.float32), yy.astype(np.float32)

# ---------- easing ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_io(x): x = clamp(x); return 3 * x * x - 2 * x * x * x
def back(x):
    x = clamp(x); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def seg(t, a, b): return clamp((t - a) / (b - a))

# ---------- backgrounds ----------
def lowfreq(seed, cell=60, shape=(H, W)):
    rng = np.random.default_rng(seed)
    small = rng.random((shape[0] // cell + 2, shape[1] // cell + 2)).astype(np.float32)
    im = Image.fromarray((small * 255).astype(np.uint8)).resize((shape[1], shape[0]), Image.BICUBIC)
    im = im.filter(ImageFilter.GaussianBlur(cell * 0.45))      # remove bicubic grid artefacts
    a = np.array(im).astype(np.float32); a -= a.min(); return a / (a.max() + 1e-6)

def blend(base, layers):
    """base: HxWx3 float; layers: [(arr HxWx3, mask HxW or scalar), ...] applied in order."""
    f = base
    for arr, m in layers:
        if m is None: continue
        if np.isscalar(m):
            if m <= 0: continue
            f = f * (1 - m) + arr * m
        else:
            f = f * (1 - m[..., None]) + arr * m[..., None]
    return f

def to_img(arr): return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")

def punch(img, z, dx=0, dy=0):
    """centered zoom (z>=1) for punch-in motion; dx/dy shift the crop (shake without black edges)."""
    if z <= 1.0005: return img
    w, h = int(W / z), int(H / z)
    x0 = int(clamp((W - w) // 2 + dx, 0, W - w)); y0 = int(clamp((H - h) // 2 + dy, 0, H - h))
    return img.crop((x0, y0, x0 + w, y0 + h)).resize((W, H), Image.BILINEAR)

def shake(t, t0, dur=0.25, amp=14):
    if not (t0 <= t < t0 + dur): return 0, 0
    k = 1 - (t - t0) / dur
    return int(math.sin(t * 90) * amp * k), int(math.cos(t * 73) * amp * k)

def top_shade(img, height=1150, alpha=200, col=(8, 22, 34)):
    a = (np.clip(1 - np.arange(H) / height, 0, 1) * alpha).astype(np.uint8)
    lay = Image.new("RGBA", (W, H), col + (0,))
    lay.putalpha(Image.fromarray(np.repeat(a[:, None], W, 1)))
    img.alpha_composite(lay)

def dim(img, a):
    if a > 0: img.alpha_composite(Image.new("RGBA", (W, H), (8, 22, 34, int(a))))

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

def with_alpha(im, p):
    if p >= 1: return im
    c = im.copy(); c.putalpha(c.getchannel("A").point(lambda v: int(v * p))); return c

def make_card(step, title, sub, total=5, width=940):
    fT, fS, fP = F("Bold", 84), F("Medium", 46), F("Bold", 34)
    sub_lines = []
    for s in sub.split("\n"): sub_lines += wrap(s, fS, width - 120)
    h = 60 + (80 if step else 0) + 100 + len(sub_lines) * 62 + 50
    pad = 40
    im = Image.new("RGBA", (width + pad * 2, h + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([pad, pad + 14, pad + width, pad + h + 14], 48, fill=(10, 30, 40, 90))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    d = ImageDraw.Draw(im)
    rrect(d, [pad, pad, pad + width, pad + h], 48, fill=(255, 255, 255, 255))
    x0, y = pad + 60, pad + 56
    if step:
        label = f"STEP {step}"
        lw = fP.getlength(label) + 52
        rrect(d, [x0, y, x0 + lw, y + 60], 30, fill=ACCENT)
        d.text((x0 + 26, y + 30), label, font=fP, fill="white", anchor="lm")
        for i in range(total):
            cx = pad + width - 60 - (total - 1 - i) * 38
            c = ACCENT if i < step else (210, 222, 226)
            d.ellipse([cx - 11, y + 19, cx + 11, y + 41], fill=c)
        y += 88
    tf = fT
    while tf.getlength(title) > width - 120: tf = F("Bold", tf.size - 4)
    d.text((x0, y), title, font=tf, fill=INK, anchor="lt")
    y += 108
    for ln in sub_lines:
        d.text((x0, y), ln, font=fS, fill=GREY_TXT, anchor="lt"); y += 62
    return im

def paste_card(frame, card, t_in, t, y=SAFE_TOP - 30, t_out=None):
    p = ease(seg(t, t_in, t_in + 0.45))
    if t_out is not None: p = min(p, 1 - ease_io(seg(t, t_out, t_out + 0.3)))
    if p <= 0: return
    frame.alpha_composite(with_alpha(card, p), ((W - card.width) // 2, int(y + (1 - p) * 80)))

def pill(img, cx, cy, text, font, bg, fg, p=1.0, padx=40, h=None):
    if p <= 0: return
    tw = font.getlength(text) + padx * 2; h = h or int(font.size * 1.9)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    rrect(ld, [cx - tw / 2, cy - h / 2, cx + tw / 2, cy + h / 2], h // 2, fill=bg + (int(245 * p),))
    ld.text((cx, cy), text, font=font, fill=fg + (int(255 * p),), anchor="mm")
    img.alpha_composite(lay)

def stroke_text_layer(text, font, fill, stroke=10, stroke_fill=(16, 26, 36)):
    w = int(font.getlength(text)) + stroke * 4 + 20; h = int(font.size * 1.35) + stroke * 4
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((w // 2, h // 2), text, font=font, fill=fill, anchor="mm",
                             stroke_width=stroke, stroke_fill=stroke_fill)
    return lay

def check_badge(d, cx, cy, r=38, col=GREEN):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col, outline="white", width=max(3, r // 8))
    k = r / 38
    d.line([(cx - 17 * k, cy + 1 * k), (cx - 4 * k, cy + 15 * k), (cx + 19 * k, cy - 14 * k)], fill="white", width=int(10 * k), joint="curve")

def x_badge(d, cx, cy, r=38, col=RED):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col, outline="white", width=max(3, r // 8))
    k = r / 38
    d.line([(cx - 14 * k, cy - 14 * k), (cx + 14 * k, cy + 14 * k)], fill="white", width=int(10 * k))
    d.line([(cx - 14 * k, cy + 14 * k), (cx + 14 * k, cy - 14 * k)], fill="white", width=int(10 * k))

def ring(d, cx, cy, r, p, col=RED, width=14):
    """hand-drawn style circle that draws on with p in [0,1]."""
    if p <= 0: return
    d.arc([cx - r, cy - r * 0.85, cx + r, cy + r * 0.85], -120, -120 + 370 * p, fill=col, width=width)

def sparkle(d, cx, cy, r, col=(255, 255, 255, 255)):
    if r <= 1: return
    k = r * 0.22
    d.polygon([(cx, cy - r), (cx + k, cy - k), (cx + r, cy), (cx + k, cy + k), (cx, cy + r), (cx - k, cy + k), (cx - r, cy), (cx - k, cy - k)], fill=col)

SPARKS = [(160, 1060), (860, 980), (520, 1200), (300, 1420), (780, 1390), (930, 1230), (120, 1270), (620, 960)]
def sparkles(img, t, t0, strength=1.0, pts=SPARKS):
    d = ImageDraw.Draw(img)
    for i, (x, y) in enumerate(pts):
        ph = (t - t0) * 2.2 - i * 0.37
        if ph < 0: continue
        s = max(0, math.sin(ph * math.pi)) if ph < 1 else max(0, math.sin((ph % 1.6) / 1.6 * math.pi)) * 0.8
        sparkle(d, x, y, 46 * s * strength, (255, 255, 255, 240))
        sparkle(d, x, y, 20 * s * strength, (255, 245, 190, 255))

def soft_disc(img, cx, cy, r, alpha=200, col=(255, 255, 255)):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).ellipse([cx - r, cy - r, cx + r, cy + r], fill=col + (alpha,))
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(10)))

# ---------- generic props ----------
def spray_bottle(img, x, y, s=1.0, squeeze=0.0, label="", liquid=(150, 210, 240)):
    d = ImageDraw.Draw(img)
    def S(v): return v * s
    rrect(d, [x - S(95), y - S(40), x + S(95), y + S(300)], int(S(40)), fill=(255, 255, 255), outline=INK, width=8)
    rrect(d, [x - S(80), y + S(60), x + S(80), y + S(285)], int(S(30)), fill=liquid)
    if label:
        rrect(d, [x - S(70), y + S(110), x + S(70), y + S(200)], int(S(12)), fill=(255, 255, 255))
        f = F("Bold", int(S(30)))
        while f.getlength(label) > S(130): f = F("Bold", f.size - 2)
        d.text((x, y + S(155)), label, font=f, fill=INK, anchor="mm")
    rrect(d, [x - S(45), y - S(95), x + S(45), y - S(35)], 10, fill=ACCENT, outline=INK, width=8)
    d.polygon([(x - S(70), y - S(95)), (x + S(60), y - S(95)), (x + S(60), y - S(165)), (x - S(150), y - S(165)), (x - S(150), y - S(130))], fill=ACCENT, outline=INK, width=8)
    rrect(d, [x - S(185), y - S(160), x - S(145), y - S(130)], 6, fill=INK)
    tx = x - S(70) + squeeze * 12
    d.polygon([(tx, y - S(95)), (tx - S(30), y - S(10)), (tx - S(5), y - S(10)), (tx + S(25), y - S(95))], fill=ACC2, outline=INK, width=6)
    return (x - S(185), y - S(145))

def mist(img, nx, ny, t, dirn=-1, strength=1.0, col=(190, 230, 255)):
    d = ImageDraw.Draw(img)
    rng = random.Random(int(t * 30))
    for i in range(70):
        dist = rng.random() ** 0.7 * 380
        a = rng.uniform(-0.45, 0.45)
        px = nx + dirn * dist * math.cos(a); py = ny + dist * math.sin(a) + dist * 0.25
        r = 3 + rng.random() * 7
        d.ellipse([px - r, py - r, px + r, py + r], fill=col + (int(220 * (1 - dist / 400) * strength),))

def towel(img, x, y, ang=0, col=(255, 150, 120), stripe=(255, 205, 185)):
    lay = Image.new("RGBA", (420, 420), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    rrect(d, [60, 110, 360, 310], 30, fill=col, outline=INK, width=8)
    for i in range(3):
        d.line([(80, 170 + i * 50), (340, 170 + i * 50)], fill=stripe, width=10)
    img.alpha_composite(lay.rotate(ang, resample=Image.BICUBIC), (int(x - 210), int(y - 210)))

def timer(img, cx, cy, p, label, unit="min", R=190):
    d = ImageDraw.Draw(img)
    d.ellipse([cx - R - 14, cy - R - 14, cx + R + 14, cy + R + 14], fill=(255, 255, 255), outline=INK, width=10)
    rrect(d, [cx - 30, cy - R - 60, cx + 30, cy - R - 20], 10, fill=INK)
    d.arc([cx - R + 14, cy - R + 14, cx + R - 14, cy + R - 14], 0, 360, fill=(220, 232, 236), width=34)
    if p > 0:
        d.arc([cx - R + 14, cy - R + 14, cx + R - 14, cy + R - 14], -90, -90 + 360 * p, fill=ACCENT, width=34)
    d.text((cx, cy - 10), label, font=F("Bold", 92), fill=INK, anchor="mm")
    d.text((cx, cy + 66), unit, font=F("Medium", 42), fill=(110, 124, 136), anchor="mm")

def bubbles(img, t, t0, pts, col=(255, 255, 255), rise=30, rmax=14, speed=1.4):
    if t < t0: return
    d = ImageDraw.Draw(img)
    for i, (x, y) in enumerate(pts):
        f = ((t - t0) * speed + (i * 0.618) % 1) % 1
        r = 5 + rmax * f
        d.ellipse([x - r, y - r - f * rise, x + r, y + r - f * rise], outline=col + (int(230 * (1 - f)),), width=4)

# ---------- scene builders ----------
def make_hook(dirty, clean, lines, pill_text, mark_xy, check_xy, split_to=0.5, labels=True, extra=None):
    """Scroll-stopping hook: punch-in, split screen dirty|clean from frame 0, bold stroked headline,
    red ring on the problem, check on the result, pill. lines = [(text, size, color), ...]."""
    layers = [(stroke_text_layer(tx, F("Bold", sz), col, stroke=max(8, sz // 16)), sz) for tx, sz, col in lines]
    for i, (lay, sz) in enumerate(layers):            # never wider than the safe width
        if lay.width > W - 60:
            r = (W - 60) / lay.width
            layers[i] = (lay.resize((int(lay.width * r), int(lay.height * r)), Image.LANCZOS), int(sz * r))
    fp = F("Bold", 46)
    def f(t, D):
        sx = W * (0.88 - (0.88 - split_to) * ease(seg(t, 0.0, 0.7)))
        m = (XF >= sx).astype(np.float32)
        base = to_img(blend(dirty, [(clean, m)]))
        if extra: extra(base, t, D, sx)
        d = ImageDraw.Draw(base)
        d.line([(sx, 0), (sx, H)], fill="white", width=10)
        cy = check_xy[1] + 140
        d.ellipse([sx - 46, cy - 46, sx + 46, cy + 46], fill="white", outline=INK, width=6)
        d.polygon([(sx - 28, cy), (sx - 9, cy - 17), (sx - 9, cy + 17)], fill=INK)
        d.polygon([(sx + 28, cy), (sx + 9, cy - 17), (sx + 9, cy + 17)], fill=INK)
        ring(d, mark_xy[0], mark_xy[1], 120, ease(seg(t, 0.25, 0.75)))
        q = back(seg(t, 0.55, 0.9))
        if q > 0: check_badge(d, check_xy[0], check_xy[1], int(56 * q))
        if labels:
            fl = F("Bold", 40)
            pill(base, sx / 2, SAFE_BOT - 60, "BEFORE", fl, (40, 40, 40), (255, 255, 255), ease(seg(t, 0.3, 0.6)))
            pill(base, sx + (W - sx) / 2, SAFE_BOT - 60, "AFTER", fl, ACCENT, (255, 255, 255), ease(seg(t, 0.5, 0.8)))
        top_shade(base, 1000, 190)
        y = SAFE_TOP + 10
        for i, (lay, sz) in enumerate(layers):
            st = i * 0.12
            p = back(seg(t, st, st + 0.4))
            sc = 0.82 + 0.18 * p                      # visible from frame 0, pops to full size
            if i > 0 and t < st: sc = 0.82
            l2 = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.BICUBIC)
            base.alpha_composite(l2, (int((W - l2.width) / 2), int(y + (lay.height - l2.height) / 2)))
            y += int(lay.height * 0.86)
        pill(base, W / 2, y + 60, pill_text, fp, ACC2, INK, 1.0 if t > 0.15 else 0.6 + t * 2.6)
        z = 1.10 - 0.10 * ease(seg(t, 0, 0.9)) + 0.015 * math.sin(t * 2.2)
        dx, dy = shake(t, 0.0, 0.3, 12)
        return punch(base, max(1.0, z), dx, dy)
    f.headline_until = 0.6   # first time the full headline is at full size
    return f

def make_safety(bg, rows, title="Safety first", label="BEFORE YOU START", width=940):
    """rows = [(kind 'ok'|'no'|'never', text), ...]; 'never' is bold red."""
    fR, fRb = F("Medium", 46), F("Bold", 46)
    x0 = (W - width) // 2
    wrapped = [(k, wrap(tx, fRb if k == "never" else fR, width - 210)) for k, tx in rows]
    h = 300 + sum(70 + len(l) * 62 + 20 for _, l in wrapped) + 10
    def f(t, D):
        base = bg(t) if callable(bg) else to_img(bg)
        dim(base, 120 * ease(seg(t, 0, 0.4)))
        p = ease(seg(t, 0.0, 0.45))
        top = SAFE_TOP + (1 - p) * 80
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        rrect(ld, [x0, top, x0 + width, top + h], 48, fill=(255, 255, 255, int(255 * p)))
        f34 = F("Bold", 34); lw = f34.getlength(label) + 52
        rrect(ld, [x0 + 60, top + 56, x0 + 60 + lw, top + 116], 30, fill=RED + (int(255 * p),))
        ld.text((x0 + 86, top + 86), label, font=f34, fill=(255, 255, 255, int(255 * p)), anchor="lm")
        ld.text((x0 + 60, top + 150), title, font=F("Bold", 84), fill=INK + (int(255 * p),), anchor="lt")
        base.alpha_composite(lay)
        y = top + 300
        for i, (kind, lines) in enumerate(wrapped):
            q = ease(seg(t, 0.5 + i * 0.5, 0.85 + i * 0.5))
            if q > 0:
                rl = Image.new("RGBA", (W, 300), (0, 0, 0, 0)); l2 = ImageDraw.Draw(rl)
                cx, cy = x0 + 105, 50
                (check_badge if kind == "ok" else x_badge)(l2, cx, cy)
                ty = cy - (len(lines) - 1) * 31
                for ln in lines:
                    l2.text((x0 + 170, ty), ln, font=fRb if kind == "never" else fR, fill=RED if kind == "never" else INK, anchor="lm"); ty += 62
                base.alpha_composite(with_alpha(rl, q), (int((1 - q) * 60), int(y - 50)))
            y += 70 + len(lines) * 62 + 20
        return base
    f.card_bottom = SAFE_TOP + h
    return f

def with_card(card, extra):
    def f(t, D):
        base = extra(t, D); paste_card(base, card, 0.0, t); return base
    return f

def make_ba(dirty, clean, y_label=SAFE_TOP + 110, handle_y=1190, spark_pts=SPARKS):
    def f(t, D):
        p = ease_io(seg(t, 0.4, 2.2))
        split = W - p * W * 0.5
        m = (XF >= split).astype(np.float32)
        base = to_img(blend(dirty, [(clean, m)]))
        d = ImageDraw.Draw(base)
        d.line([(split, 0), (split, H)], fill=(255, 255, 255), width=10)
        d.ellipse([split - 50, handle_y - 50, split + 50, handle_y + 50], fill="white", outline=INK, width=6)
        d.polygon([(split - 30, handle_y), (split - 10, handle_y - 18), (split - 10, handle_y + 18)], fill=INK)
        d.polygon([(split + 30, handle_y), (split + 10, handle_y - 18), (split + 10, handle_y + 18)], fill=INK)
        f56 = F("Bold", 56); q = ease(seg(t, 0.2, 0.6))
        pill(base, min(split, W) / 2, y_label, "BEFORE", f56, (40, 40, 40), (255, 255, 255), q, padx=35, h=100)
        pill(base, split + (W - split) / 2, y_label, "AFTER", f56, ACCENT, (255, 255, 255), q * ease(seg(t, 1.0, 1.5)), padx=35, h=100)
        if t > 2.0:
            sp = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sparkles(sp, t, 2.0, 1.0, spark_pts)
            sp.putalpha(Image.fromarray(np.minimum(np.array(sp.getchannel("A")), ((xx >= split) * 255).astype(np.uint8))))
            base.alpha_composite(sp)
        return base
    f.impact_at = 0.5
    return f

def make_outro(bg):
    def f(t, D):
        base = to_img(bg); sparkles(base, t, 0.0, 0.8)
        dim(base, 60)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        p = ease(seg(t, 0.1, 0.6)); top = 520 + (1 - p) * 60; a = int(255 * p)
        rrect(ld, [70, top, W - 70, top + 640], 56, fill=ACCENT + (int(245 * p),))
        bx, by = W / 2, top + 140
        ld.polygon([(bx - 48, by - 70), (bx + 48, by - 70), (bx + 48, by + 70), (bx, by + 30), (bx - 48, by + 70)], fill=(255, 255, 255, a))
        ld.text((W / 2, top + 290), "Save this for", font=F("Bold", 76), fill=(255, 255, 255, a), anchor="mm")
        ld.text((W / 2, top + 380), "cleaning day!", font=F("Bold", 76), fill=ACC2 + (a,), anchor="mm")
        q = ease(seg(t, 0.9, 1.4))
        rrect(ld, [W / 2 - 330, top + 470, W / 2 + 330, top + 570], 50, fill=(255, 255, 255, int(255 * q)))
        ld.text((W / 2, top + 520), "Follow @cleaneverycorner", font=F("Bold", 42), fill=ACCENT + (int(255 * q),), anchor="mm")
        base.alpha_composite(lay)
        return base
    return f

# ---------- rendering ----------
_SCENES, _OUT = None, None
def _render_one(i):
    name, fn, D = _SCENES[i]
    n = int(round(D * FPS))
    out = os.path.join(_OUT, f"{name}.mp4"); tmp = out[:-4] + ".tmp.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), tmp]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k in range(n):
        pr.stdin.write(fn(k / FPS, D).convert("RGB").tobytes())
    pr.stdin.close()
    if pr.wait() != 0: raise RuntimeError("ffmpeg failed for " + name)
    os.replace(tmp, out)
    return name

def scene_starts(scenes):
    st, t = [], 0.0
    for _, _, D in scenes: st.append(t); t += int(round(D * FPS)) / FPS
    return st, t

def stills(scenes, outdir, fracs=(0.55, 0.95), only=None):
    os.makedirs(outdir, exist_ok=True); paths = []
    for name, fn, D in scenes:
        if only and name not in only: continue
        for fr in fracs:
            p = os.path.join(outdir, f"{name}_{int(fr * 100)}.jpg")
            fn(D * fr, D).convert("RGB").save(p, quality=85); paths.append(p)
    return paths

def render_scenes(scenes, outdir, procs=2):
    global _SCENES, _OUT
    _SCENES, _OUT = scenes, outdir
    os.makedirs(outdir, exist_ok=True)
    from multiprocessing import Pool
    order = sorted(range(len(scenes)), key=lambda i: -scenes[i][2])
    with Pool(procs) as p:
        for r in p.imap_unordered(_render_one, order): print("done", r, flush=True)
    return [os.path.join(outdir, f"{n}.mp4") for n, _, _ in scenes]

def concat(files, out):
    lst = out + ".txt"
    with open(lst, "w") as fh:
        for f_ in files: fh.write(f"file '{os.path.abspath(f_)}'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out], check=True)

def mux(video, wav, out, lufs=-15.0, tp=-3.0):
    """two-pass loudnorm + limiter (AAC overshoot headroom) -> about -15 LUFS, true peak <= -1.5 dB, AAC 192k."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", wav, "-af", f"loudnorm=I={lufs}:TP={tp}:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    js = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
    af = (f"loudnorm=I={lufs}:TP={tp}:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
          f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", af + ",alimiter=limit=0.70:level=false:attack=2:release=60,aresample=44100", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)

def build(scenes, workdir, out_mp4, music_fn, procs=2):
    """music_fn(duration, cut_times, impact_times, wav_path)"""
    files = render_scenes(scenes, os.path.join(workdir, "scenes"), procs)
    silent = os.path.join(workdir, "video_silent.mp4"); concat(files, silent)
    st, total = scene_starts(scenes)
    impacts = [st[i] + getattr(fn, "impact_at", 0) for i, (_, fn, _) in enumerate(scenes) if hasattr(fn, "impact_at")]
    wav = os.path.join(workdir, "music.wav"); music_fn(total, st[1:], impacts, wav)
    mux(silent, wav, out_mp4)
    return total
