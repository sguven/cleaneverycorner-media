"""Opening formats for @cleaneverycorner Reels (added 2026-11-26, hook test).

The standard opening (`engine.make_hook`: split screen + yellow headline) stays as the control. Two new ones:

    make_wipe_hook   no headline: full-screen dirty close-up, one wipe reveals the clean surface in the first second,
                     a small caption sticker lands at ~0.3 s ("satisfying first", explanation second)
    make_quiz_hook   "A or B?" over the dirty surface with a countdown; the answer lands at ~1.7 s and the
                     surface turns clean

Both take the same DIRTY / CLEAN numpy backgrounds as make_hook and return f(t, D) like every other scene, so
`make_loop_outro(bg, HOOK(0, D))` keeps working. Worked examples: tools/hook_demo.py.

Rules: motion from frame 0, at most ONE short text block in the first second (max 6 words), text inside
SAFE_TOP..SAFE_BOT, safety scene still follows the hook whenever a product is used.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from lib.engine import *

WHITE = (255, 255, 255)


def sticker(img, lines, cy, t, t0=0.0, size=64, bg=WHITE, fg=INK, pad=(44, 26), dur=0.28):
    """Caption box in the native "text sticker" look (white rounded box, dark bold text). lines: 1-2 short strings."""
    if isinstance(lines, str): lines = [lines]
    if t < t0: return
    p = back(seg(t, t0, t0 + dur))
    f = F("Bold", size)
    tw = max(f.getlength(l) for l in lines)
    while tw > W - 150 and size > 40:
        size -= 2; f = F("Bold", size); tw = max(f.getlength(l) for l in lines)
    lh = int(size * 1.28)
    bw, bh = int(tw + pad[0] * 2), int(lh * len(lines) + pad[1] * 2)
    lay = Image.new("RGBA", (bw + 40, bh + 40), (0, 0, 0, 0))
    sh = Image.new("RGBA", lay.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([20, 26, 20 + bw, 26 + bh], 30, fill=(0, 0, 0, 110))
    lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle([20, 20, 20 + bw, 20 + bh], 30, fill=bg + (255,))
    for i, l in enumerate(lines):
        d.text((20 + bw / 2, 20 + pad[1] + i * lh + lh / 2), l, font=f, fill=fg, anchor="mm")
    sc = 0.85 + 0.15 * p
    l2 = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.BICUBIC)
    img.alpha_composite(l2, (int(W / 2 - l2.width / 2), int(cy - l2.height / 2)))


def make_wipe_hook(dirty, clean, path, caption, tool=None, radius=150, t_wipe=(0.05, 1.0), t_caption=0.3,
                   caption_y=None, spark_pts=None, zoom=(1.16, 1.0)):
    """Wipe-first opening. path: list of (x, y) the tool travels (2-4 points across the dirtiest area).
    caption: 1-2 short lines (max 6 words total). tool: fn(img, x, y) drawing the tool at the wipe point
    (default: the engine's towel). The wipe starts in frame 1 and is done by ~1 s; the rest of the scene holds
    the half-clean surface with sparkles so the result stays on screen."""
    caption_y = caption_y or SAFE_BOT - 150
    def f(t, D):
        p = ease_io(seg(t, t_wipe[0], t_wipe[1])) * (len(path) - 1)
        m = trail_mask(path, p, radius=radius, blur=16) if t > t_wipe[0] else np.zeros((H, W), np.float32)
        base = to_img(blend(dirty, [(clean, m)]))
        if t > t_wipe[1] - 0.15: sparkles(base, t, t_wipe[1] - 0.15, 1.0, spark_pts or [tuple(map(int, q)) for q in path])
        if t < t_wipe[1] + 0.25:
            x, y = path_point(path, p)
            a = 1 - seg(t, t_wipe[1], t_wipe[1] + 0.25)
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            (tool or (lambda im, px, py: towel(im, px, py, ang=-18)))(lay, x, y)
            base.alpha_composite(with_alpha(lay, a))
        sticker(base, caption, caption_y, t, t_caption, size=72)
        z = zoom[0] + (zoom[1] - zoom[0]) * ease(seg(t, 0, 1.1)) + 0.012 * math.sin(t * 2.2)
        dx, dy = shake(t, t_wipe[1] - 0.05, 0.25, 10)
        return punch(base, max(1.0, z), dx, dy)
    f.headline_until = t_caption + 0.3
    return f


def make_quiz_hook(dirty, clean, question, a, b, correct, t_reveal=1.7, y=900, h=300, mark_xy=None):
    """A-or-B opening. question: max 6 words. a / b: 1-3 word answers. correct: "a" or "b".
    Countdown bar runs out at t_reveal; then the right card turns green, the wrong one red, and the surface
    behind turns clean. mark_xy: optional (x, y) of the problem spot to ring in red from frame 0."""
    def f(t, D):
        rv = seg(t, t_reveal, t_reveal + 0.3)
        k = ease(seg(t, t_reveal, t_reveal + 0.6))
        base = to_img(blend(dirty, [(clean, np.float32(k))]) if k > 0 else dirty)
        if mark_xy and rv == 0: ring(ImageDraw.Draw(base), mark_xy[0], mark_xy[1], 120, ease(seg(t, 0.0, 0.4)))
        if k > 0.5: sparkles(base, t, t_reveal + 0.3, 1.0)
        dim(base, 95 * (1 - 0.6 * k))
        sticker(base, question, SAFE_TOP + 150, t, -0.2, size=76)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        gap, mg = 36, 50
        cw = (W - 2 * mg - gap) // 2
        for i, (key, txt) in enumerate((("a", a), ("b", b))):
            p = back(seg(t, i * 0.08, 0.32 + i * 0.08))
            x0 = mg + i * (cw + gap); yo = y + int((1 - p) * 70)
            ok = key == correct
            bg, fg = ((GREEN, WHITE) if ok else ((250, 222, 223), (150, 80, 84))) if rv > 0 else (WHITE, INK)
            edge = ACC2 if rv == 0 else (GREEN if ok else RED)
            d.rounded_rectangle([x0 + 6, yo + 12, x0 + cw + 6, yo + h + 12], 44, fill=(0, 0, 0, 90))
            d.rounded_rectangle([x0, yo, x0 + cw, yo + h], 44, fill=bg + (255,), outline=edge + (255,), width=8)
            d.ellipse([x0 + 26, yo + 26, x0 + 98, yo + 98], fill=(ACC2 if rv == 0 else (WHITE if ok else RED)) + (255,))
            d.text((x0 + 62, yo + 62), key.upper(), font=F("Bold", 44), fill=(INK if rv == 0 or ok else WHITE), anchor="mm")
            words = wrap(txt, F("Bold", 70), cw - 60)
            size = 70
            while (len(words) > 2 or max(F("Bold", size).getlength(w_) for w_ in words) > cw - 60) and size > 40:
                size -= 4; words = wrap(txt, F("Bold", size), cw - 60)
            fnt = F("Bold", size); lh = int(size * 1.15)
            for j, w_ in enumerate(words):
                d.text((x0 + cw / 2, yo + h / 2 + 34 + (j - (len(words) - 1) / 2) * lh), w_, font=fnt, fill=fg, anchor="mm")
            if rv > 0:
                r = int(44 * back(rv)); cx, cy = x0 + cw - 62, yo + 62
                if ok:
                    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE)
                    d.line([(cx - r * .45, cy), (cx - r * .1, cy + r * .38), (cx + r * .5, cy - r * .35)], fill=GREEN, width=10, joint="curve")
                else:
                    d.line([(cx - r * .5, cy - r * .5), (cx + r * .5, cy + r * .5)], fill=RED, width=12)
                    d.line([(cx - r * .5, cy + r * .5), (cx + r * .5, cy - r * .5)], fill=RED, width=12)
        if t < t_reveal:
            q = 1 - seg(t, 0.2, t_reveal); by = y + h + 60
            d.rounded_rectangle([mg, by, W - mg, by + 22], 11, fill=(255, 255, 255, 110))
            if q > 0.02: d.rounded_rectangle([mg, by, mg + int((W - 2 * mg) * q), by + 22], 11, fill=ACC2 + (255,))
        base.alpha_composite(lay)
        z = 1.0 + 0.05 * ease_io(seg(t, 0, t_reveal)) + 0.012 * math.sin(t * 2.2)
        dx, dy = shake(t, t_reveal, 0.3, 14)
        return punch(base, z, dx, dy)
    f.headline_until = 0.3
    return f
