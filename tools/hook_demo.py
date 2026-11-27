"""Worked examples of the opening formats in lib/hooks.py, using the backgrounds of two published Reels.

python3 tools/hook_demo.py stills <outdir>   -> one contact sheet per format (t = 0, 0.3, 0.8, 1.5, 2.1 s)
python3 tools/hook_demo.py mp4 <out.mp4>     -> silent preview, the openings back to back
"""
import os, sys, subprocess, importlib.util
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
from lib.engine import *
from lib.hooks import *
from PIL import Image

def load(folder):
    p = os.path.join(ROOT, "reels", folder, "render.py")
    sp = importlib.util.spec_from_file_location("r_" + folder.replace("-", "_"), p)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m

stove = load("2026-11-23-glass-stovetop")
D_HOOK = 2.2
# wipe-first: one pass across the burnt burner; caption after the motion has started
WIPE = make_wipe_hook(stove.DIRTY, stove.CLEAN, [(40, 1520), (330, 1420), (620, 1480), (880, 1370), (1070, 1280)],
                      ["Burnt-on gunk?", "Don't scrub it"], radius=230,
                      tool=lambda im, x, y: razor_scraper(im, x, y, ang=-20), caption_y=SAFE_TOP + 170)
# A or B: both answers are things people really do; the right one is the Reel's own tip
QUIZ = make_quiz_hook(stove.DIRTY, stove.CLEAN, "Burnt glass stovetop?", "Scrub pad", "Razor scraper", "b",
                      mark_xy=(310, 1440), y=780)
DEMOS = [("wipe_open", WIPE), ("quiz_open", QUIZ)]

if __name__ == "__main__":
    mode, out = sys.argv[1], sys.argv[2]
    if mode == "stills":
        os.makedirs(out, exist_ok=True)
        ts = (0.0, 0.3, 0.8, 1.5, 2.1)
        for name, fn in DEMOS:
            sheet = Image.new("RGB", (540 * len(ts), 960))
            for i, t in enumerate(ts):
                sheet.paste(fn(t, D_HOOK).convert("RGB").resize((540, 960), Image.LANCZOS), (540 * i, 0))
            sheet.save(os.path.join(out, f"{name}.jpg"), quality=88)
    else:
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
               "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", out]
        pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for name, fn in DEMOS:
            for k in range(int((D_HOOK + 0.6) * FPS)):
                pr.stdin.write(fn(min(k / FPS, D_HOOK), D_HOOK).convert("RGB").tobytes())
        pr.stdin.close(); pr.wait()
