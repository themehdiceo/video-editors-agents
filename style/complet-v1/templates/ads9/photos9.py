"""Défilé de SES photos 9:16 (règle 19/11) : fond noir, chaque photo dans son format, en petit (pas d'agrandissement),
glissement façon pellicule depuis la droite + clic d'appareil photo à chaque photo, léger Ken Burns.
render(files, dur, out) -> temps des clics (s depuis le début)."""
import subprocess
from PIL import Image, ImageOps, ImageDraw, ImageFilter
W, H, FPS = 1080, 1920, 30
ease = lambda u: 1 - (1 - min(max(u, 0), 1)) ** 4


def load(f):
    im = ImageOps.exif_transpose(Image.open(f)).convert("RGB"); im.thumbnail((860, 1180), Image.LANCZOS)
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), 22, fill=255)
    im = im.convert("RGBA"); im.putalpha(m)
    sh = Image.new("RGBA", (im.width + 120, im.height + 120), (0, 0, 0, 0))
    sm = Image.new("L", sh.size, 0); sm.paste(m, (60, 80)); sh.putalpha(sm.filter(ImageFilter.GaussianBlur(28)).point(lambda v: v * 0.7))
    return im, sh


def render(files, dur, out):
    ph = [load(f) for f in files]; dn = dur / len(ph); clicks = [i * dn for i in range(len(ph))]
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "qtrle", out], stdin=subprocess.PIPE)
    for k in range(int(dur * FPS)):
        t = k / FPS; img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        i = min(int(t / dn), len(ph) - 1); u = ease((t - clicks[i]) / 0.45)
        if i > 0 and u < 1:  # la précédente recule et s'éteint
            im, sh = ph[i - 1]; a = 1 - u
            q = im.copy(); q.putalpha(q.getchannel("A").point(lambda v: int(v * a)))
            img.alpha_composite(q, (int((W - im.width) / 2 - 500 * u), int((H - im.height) / 2 - 60)))
        im, sh = ph[i]
        z = 1 + 0.04 * (t - clicks[i]) / dn
        q = im.resize((int(im.width * z), int(im.height * z)), Image.BILINEAR)
        x = (W - q.width) / 2 + 700 * (1 - u); y = (H - q.height) / 2 - 60
        img.alpha_composite(sh.resize((q.width + 120, q.height + 120)), (int(x - 60), int(y - 60)))
        img.alpha_composite(q, (int(x), int(y)))
        a = min(1, t / 0.15, (dur - t) / 0.2)
        if a < 1: img.putalpha(img.getchannel("A").point(lambda v: int(v * max(a, 0))))
        p.stdin.write(img.tobytes())
    p.stdin.close(); p.wait()
    return clicks


def click_wav(path):  # déclic d'obturateur synthétique, 90 ms
    import numpy as np, wave
    sr = 48000; n = int(0.09 * sr); t = np.arange(n) / sr; rng = np.random.default_rng(3)
    x = rng.uniform(-1, 1, n) * np.exp(-t * 70) * 0.5 + rng.uniform(-1, 1, n) * np.exp(-((t - 0.045) * 90) ** 2) * 0.35
    w = wave.open(path, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((np.clip(x, -1, 1) * 20000).astype(np.int16).tobytes()); w.close()
