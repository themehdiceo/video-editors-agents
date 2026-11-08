#!/usr/bin/env python3
"""Assemble le short final à partir d'un plan de montage JSON.

Usage: compose.py <plan.json>

plan.json :
{
  "aroll": "work/aroll_cut.mp4",
  "out": "out/final.mp4",
  "format": {"w": 1080, "h": 1920, "fps": 30},
  "crop_x": 0.5,                      # position horizontale du recadrage 9:16 (0=gauche, 1=droite)
  "broll": [                          # temps sur la timeline montée
    {"file": "broll/a.mp4", "at": 2.0, "dur": 2.6, "src_start": 0.0,
     "layout": "full" | "top",        # top = B-roll en haut, A-roll en bas (50/50)
     "volume": 0.0},                  # 0 = muet
  ],
  "overlays": [                       # vidéos avec alpha (.mov ProRes 4444 / .webm VP9) ou PNG
    {"file": "gfx/title.mov", "at": 0.0, "dur": 2.0, "x": 0, "y": 0}
  ],
  "subtitles": "work/subs.ass",
  "music": {"file": "assets/music/x.mp3", "volume": 0.12, "duck": true, "start": 0.0},
  "sfx": [{"file": "assets/sfx/whoosh.mp3", "at": 2.0, "volume": 0.6}],
  "loudness": -14
}
"""
import json
import os
import subprocess
import sys


def probe_duration(f):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", f], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def has_audio(f):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
                          "stream=index", "-of", "csv=p=0", f], capture_output=True, text=True)
    return bool(out.stdout.strip())


def cover(label_in, w, h, label_out, crop_x=0.5, fps=30):
    """Mise à l'échelle 'cover' puis recadrage à w x h."""
    return (f"[{label_in}]scale={w}:{h}:force_original_aspect_ratio=increase,"
            f"crop={w}:{h}:(iw-{w})*{crop_x}:(ih-{h})/2,setsar=1,fps={fps}[{label_out}];")


def main() -> int:
    plan = json.load(open(sys.argv[1]))
    base_dir = os.path.dirname(os.path.abspath(sys.argv[1]))
    P = lambda p: p if os.path.isabs(p) else os.path.join(base_dir, p)

    fmt = plan.get("format", {})
    W, H, FPS = fmt.get("w", 1080), fmt.get("h", 1920), fmt.get("fps", 30)
    aroll = P(plan["aroll"])
    total = probe_duration(aroll)
    cx = plan.get("crop_x", 0.5)

    inputs = ["-i", aroll]
    g = []
    g.append("[0:v]split=2[a_full_src][a_half_src];")
    g.append(cover("a_full_src", W, H, "base", cx, FPS))
    g.append(cover("a_half_src", W, H // 2, "ahalf", cx, FPS))
    cur = "base"
    idx = 1
    audio_mix = ["[0:a]aresample=48000[voice]"]
    extra_audio = []

    half_windows = []
    for i, b in enumerate(plan.get("broll", [])):
        inputs += ["-ss", str(b.get("src_start", 0)), "-t", str(b["dur"]), "-i", P(b["file"])]
        at, dur = float(b["at"]), float(b["dur"])
        lay = b.get("layout", "full")
        bh = H if lay == "full" else H // 2
        g.append(f"[{idx}:v]setpts=PTS-STARTPTS+{at}/TB[b{i}raw];")
        g.append(cover(f"b{i}raw", W, bh, f"b{i}", 0.5, FPS))
        en = f"between(t,{at},{at + dur})"
        g.append(f"[{cur}][b{i}]overlay=0:0:eof_action=pass:enable='{en}'[v{i}];")
        cur = f"v{i}"
        if lay == "top":
            half_windows.append(en)
        vol = float(b.get("volume", 0))
        if vol > 0 and has_audio(P(b["file"])):
            ms = int(at * 1000)
            extra_audio.append(f"[{idx}:a]aresample=48000,volume={vol},adelay={ms}|{ms}[ba{i}]")
        idx += 1

    if half_windows:
        en = "+".join(half_windows)
        g.append(f"[{cur}][ahalf]overlay=0:{H // 2}:enable='{en}'[vsplit];")
        cur = "vsplit"
    else:
        g.append("[ahalf]nullsink;")

    for i, o in enumerate(plan.get("overlays", [])):
        f = P(o["file"])
        if f.lower().endswith((".png", ".jpg", ".jpeg")):
            inputs += ["-loop", "1", "-t", str(o["at"] + o["dur"]), "-i", f]
        else:
            inputs += ["-i", f]
        at, dur = float(o["at"]), float(o["dur"])
        g.append(f"[{idx}:v]setpts=PTS-STARTPTS+{at}/TB,format=rgba[o{i}];")
        g.append(f"[{cur}][o{i}]overlay={o.get('x', 0)}:{o.get('y', 0)}:eof_action=pass:"
                 f"enable='between(t,{at},{at + dur})'[ov{i}];")
        cur = f"ov{i}"
        idx += 1

    if plan.get("subtitles"):
        subs = P(plan["subtitles"]).replace(":", r"\:").replace("'", r"\'")
        fontsdir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts")
        g.append(f"[{cur}]subtitles='{subs}':fontsdir='{fontsdir}'[vsub];")
        cur = "vsub"
    g.append(f"[{cur}]format=yuv420p[vout];")

    music = plan.get("music")
    if music:
        inputs += ["-stream_loop", "-1", "-ss", str(music.get("start", 0)), "-i", P(music["file"])]
        mv = float(music.get("volume", 0.12))
        audio_mix.append(f"[{idx}:a]aresample=48000,volume={mv},atrim=0:{total},"
                         f"afade=t=out:st={max(0, total - 1.5)}:d=1.5[mus]")
        if music.get("duck", True):
            audio_mix[0] = "[0:a]aresample=48000,asplit=2[voice][vkey]"
            audio_mix.append("[mus][vkey]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[musd]")
            mus_label = "[musd]"
        else:
            mus_label = "[mus]"
        extra_audio.insert(0, None)  # placeholder pour garder l'ordre
        extra_audio[0] = mus_label
        idx += 1

    for i, s in enumerate(plan.get("sfx", [])):
        inputs += ["-i", P(s["file"])]
        ms = int(float(s["at"]) * 1000)
        extra_audio.append(f"[{idx}:a]aresample=48000,volume={s.get('volume', 0.6)},adelay={ms}|{ms}[sfx{i}]")
        idx += 1

    labels = ["[voice]"]
    for e in extra_audio:
        if e.startswith("["):
            if e.endswith("]") and ";" not in e and "=" not in e:
                labels.append(e)  # label de musique déjà défini
                continue
            audio_mix.append(e)
            labels.append(e[e.rindex("["):])
    lufs = plan.get("loudness", -14)
    audio_mix.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0:duration=first,"
                     f"loudnorm=I={lufs}:TP=-1.0:LRA=11[aout]")

    graph = "".join(g) + ";".join(audio_mix)
    out = P(plan["out"])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", graph,
           "-map", "[vout]", "-map", "[aout]", "-t", str(total),
           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-profile:v", "high",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", out]
    if os.environ.get("COMPOSE_DEBUG"):
        print(" ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"Rendu OK : {out} ({total:.1f}s, {W}x{H})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
