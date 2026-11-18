#!/usr/bin/env python3
"""Musique sous la voix, réglage validé VSL v6 (style/vsl-v1/STYLE.md) : voix intacte,
musique à ~9 LU sous la voix au départ, fondu sur 30 s jusqu'à ~13 LU sous la voix, puis stable.
Ducking léger (threshold 0.02, ratio 2). Fondu d'entrée 1 s, de sortie 1 s.
Usage: mix_lu.py video music out [--start 9] [--end 13] [--ramp 30]
"""
import argparse, re, subprocess

ap = argparse.ArgumentParser()
ap.add_argument("video"); ap.add_argument("music"); ap.add_argument("out")
ap.add_argument("--start", type=float, default=9.0)
ap.add_argument("--end", type=float, default=13.0)
ap.add_argument("--ramp", type=float, default=30.0)
ap.add_argument("--split", type=float, help="à partir de cet instant : 2e partie, mesurée à part")
ap.add_argument("--under2", type=float, default=24.0, help="dB sous la voix de la 2e partie (très bas)")
a = ap.parse_args()


def lufs(path, dur=None, ss=None):
    cmd = ["ffmpeg", "-v", "info", "-nostats"] + (["-ss", str(ss)] if ss else []) + (["-t", str(dur)] if dur else []) + ["-i", path, "-vn", "-af", "ebur128", "-f", "null", "-"]
    txt = subprocess.run(cmd, capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", txt)[-1])


dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", a.video]))
ch = int(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=channels", "-of", "csv=p=0", a.video]))
v, m = lufs(a.video, a.split), lufs(a.music, dur)
g0, g1 = v - a.start - m, v - a.end - m          # gains (dB) départ / régime
gain = f"pow(10,({g0}+({g1}-{g0})*min(t/{a.ramp},1))/20)"
if a.split:                                       # 2e partie (autre prise de son) : musique à peine audible
    v2 = lufs(a.video, ss=a.split)
    g2 = v2 - a.under2 - lufs(a.music, ss=a.split, dur=dur - a.split)
    gain = f"if(lt(t,{a.split - 1}),{gain},if(lt(t,{a.split}),{gain}+({'pow(10,%s/20)' % g2}-{gain})*(t-{a.split - 1}),pow(10,{g2}/20)))"
    print(f"partie 2 : voix {v2:.1f} LUFS -> gain {g2:+.1f} dB")
up = "pan=stereo|c0=c0|c1=c0," if ch == 1 else ""
graph = (
    f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=0:{dur},volume='{gain}':eval=frame,"
    f"afade=t=in:d=1,afade=t=out:st={dur - 1:.2f}:d=1[mu];"
    f"[0:a]{up}aformat=sample_rates=48000:channel_layouts=stereo,asplit[v1][v2];"
    f"[mu][v1]sidechaincompress=threshold=0.02:ratio=2:attack=30:release=400[duck];"
    f"[v2][duck]amix=inputs=2:normalize=0:duration=first[a]"
)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-stream_loop", "-1", "-i", a.music,
                "-filter_complex", graph, "-map", "0:v", "-map", "[a]", "-c:v", "copy",
                "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", a.out], check=True)
print(f"voix {v:.1f} LUFS, musique {m:.1f} LUFS -> gain {g0:+.1f} puis {g1:+.1f} dB -> {a.out}")
