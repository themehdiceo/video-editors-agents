#!/usr/bin/env python3
"""Coupe l'A-roll à partir d'une liste de passages à GARDER.

Usage: cut.py <source> <keep.json> <sortie.mp4> [--silences silences.json] [--pad 0.06] [--hw] [--audio-only]

keep.json: {"keep": [{"start": 0.40, "end": 4.95, "why": "hook"}, ...]}

- Chaque bord est "accroché" au silence le plus proche (forme d'onde) pour ne
  jamais couper un mot : un début recule dans le silence précédent, une fin
  avance dans le silence suivant, sans dépasser `pad` secondes de silence gardé.
- Micro-fondu audio de 15 ms à chaque raccord pour éviter les clics.
- Écrit aussi <sortie>.timemap.json : correspondance ancien temps -> nouveau temps
  (utilisé par subtitles.py et compose.py).
"""
import argparse
import json
import subprocess
import sys


def snap(keep, silences, pad):
    out = []
    for k in keep:
        s, e = float(k["start"]), float(k["end"])
        for z in silences:
            # début tombant dans un silence ou juste après : on démarre `pad` avant la fin du silence
            if z["start"] - 0.05 <= s <= z["end"] + 0.08:
                s = max(z["start"], z["end"] - pad)
            # fin tombant dans un silence ou juste avant : on finit `pad` après le début du silence
            if z["start"] - 0.08 <= e <= z["end"] + 0.05:
                e = min(z["end"], z["start"] + pad)
        if e - s > 0.08:
            out.append({**k, "start": round(s, 3), "end": round(e, 3)})
    # fusionne les chevauchements
    out.sort(key=lambda r: r["start"])
    merged = []
    for r in out:
        if merged and r["start"] <= merged[-1]["end"] + 0.02:
            merged[-1]["end"] = max(merged[-1]["end"], r["end"])
        else:
            merged.append(dict(r))
    return merged


SR = 48000


def cut_audio(src, ranges, out, enc):
    """Décode le son UNE fois, colle les passages (fondu 15 ms à chaque raccord), encode. Quelques secondes."""
    import array, tempfile, wave, os
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-map", "0:a:0", "-ac", "2", "-ar", str(SR),
                          "-f", "s16le", "-"], capture_output=True, check=True).stdout
    x = array.array("h"); x.frombytes(raw)
    y = array.array("h")
    fade = int(0.015 * SR)
    for r in ranges:
        seg = x[int(round(r["start"] * SR)) * 2:int(round(r["end"] * SR)) * 2]
        n = len(seg) // 2
        f = min(fade, n // 2)
        for k in range(f):
            g = k / f
            for c in (0, 1):
                seg[2 * k + c] = int(seg[2 * k + c] * g)
                seg[2 * (n - 1 - k) + c] = int(seg[2 * (n - 1 - k) + c] * g)
        y.extend(seg)
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    with wave.open(tmp, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(y.tobytes())
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmp, *enc, out], check=True)
    os.remove(tmp)


def fast_cut(a, ranges, total):
    """Chaque passage lu seul (-ss, rien d'autre n'est décodé) et encodé par la puce du Mac, 6 en parallèle.
    Image seule par passage, son collé d'un bloc (pas de clic AAC aux raccords), puis assemblage sans réencodage."""
    import os, tempfile, time
    from concurrent.futures import ThreadPoolExecutor
    import ffprogress
    d = tempfile.mkdtemp(prefix="cut_", dir=os.path.dirname(os.path.abspath(a.out)))
    tags = ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709"] if a.vf else []
    # tpad + -frames:v : chaque passage a EXACTEMENT round(durée × 30) images, sinon l'image dérive du son (2,8 s sur 205 passages).
    vf = "fps=30,tpad=stop_mode=clone:stop=3" + ("," + a.vf if a.vf else "")
    log, t0, done = ffprogress.find_log(a.out), time.time(), [0.0]

    def one(i):
        r = ranges[i]
        o = os.path.join(d, f"{i:04d}.mp4")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-hwaccel", "videotoolbox", "-ss", f"{r['start']:.4f}",
                        "-i", a.src, "-frames:v", str(round((r["end"] - r["start"]) * 30)), "-an", "-vf", vf,
                        "-c:v", "h264_videotoolbox", "-b:v", "24M", "-profile:v", "high", *tags, o], check=True)
        done[0] += r["end"] - r["start"]
        return o

    with ThreadPoolExecutor(6) as ex:
        fut_a = ex.submit(cut_audio, a.src, ranges, os.path.join(d, "a.m4a"), ["-c:a", "aac", "-b:a", "192k"])
        outs = list(ex.map(one, range(len(ranges))))
        fut_a.result()
    lst = os.path.join(d, "list.txt")
    open(lst, "w").write("".join(f"file '{o}'\n" for o in outs))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", os.path.join(d, "a.m4a"),
                    "-map", "0:v", "-map", "1:a", "-c", "copy", "-movflags", "+faststart", a.out], check=True)
    for f in os.listdir(d):
        os.remove(os.path.join(d, f))
    os.rmdir(d)
    if log:
        open(log, "a").write(f"Découpe rapide : terminé en {(time.time() - t0) / 60:.0f} min\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("keep")
    ap.add_argument("out")
    ap.add_argument("--silences")
    ap.add_argument("--pad", type=float, default=0.06)
    ap.add_argument("--vf", help="filtre vidéo ajouté après le montage (ex. tone-map HDR -> SDR bt709)")
    ap.add_argument("--hw", action="store_true", help="décodage + encodage matériel du Mac (videotoolbox), 2-4x plus vite")
    ap.add_argument("--audio-only", action="store_true",
                    help="découpe le son seul (opus) en quelques secondes : pour la relecture Gemini, même timemap")
    a = ap.parse_args()

    keep = json.load(open(a.keep))["keep"]
    sil = json.load(open(a.silences))["silences"] if a.silences else []
    ranges = snap(keep, sil, a.pad) if sil else keep

    parts, labels = [], []
    for i, r in enumerate(ranges):
        d = r["end"] - r["start"]
        fo = max(0.0, d - 0.015)
        parts.append(f"[0:v]trim=start={r['start']}:end={r['end']},setpts=PTS-STARTPTS[v{i}];")
        parts.append(f"[0:a]atrim=start={r['start']}:end={r['end']},asetpts=PTS-STARTPTS,"
                     f"afade=t=in:d=0.015,afade=t=out:st={fo:.3f}:d=0.015[a{i}];")
        labels.append(f"[v{i}][a{i}]")
    import ffprogress
    if a.audio_only or a.hw:
        # Bornes calées sur la grille 30 i/s : son et image gardent EXACTEMENT la même durée (pas de dérive).
        ranges = [{**r, "start": round(round(r["start"] * 30) / 30, 4), "end": round(round(r["end"] * 30) / 30, 4)}
                  for r in ranges]
        ranges = [r for r in ranges if r["end"] > r["start"]]
    total = sum(r["end"] - r["start"] for r in ranges)
    if a.audio_only:
        # Gemini n'écoute que le son : quelques secondes au lieu d'une découpe vidéo de 6 min.
        cut_audio(a.src, ranges, a.out, ["-ac", "1", "-c:a", "libopus", "-b:a", "48k"])
    elif a.hw:
        fast_cut(a, ranges, total)
    else:
        # Ancien chemin (un seul graphe trim/concat) : lent, chaque passage met en mémoire toute la source.
        graph = "".join(parts) + "".join(labels) + f"concat=n={len(ranges)}:v=1:a=1[vc][a];[vc]fps=30{',' + a.vf if a.vf else ''}[v]"
        tags = ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709"] if a.vf else []
        ffprogress.run(["ffmpeg", "-y", "-loglevel", "error", "-i", a.src, "-filter_complex", graph,
                        "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
                        *tags, "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", a.out],
                       total, ffprogress.find_log(a.out), "Découpe")

    t, tm = 0.0, []
    for r in ranges:
        tm.append({"src_start": r["start"], "src_end": r["end"], "dst_start": round(t, 3)})
        t += r["end"] - r["start"]
    json.dump({"ranges": tm, "duration": round(t, 3)}, open(a.out + ".timemap.json", "w"), indent=1)
    print(f"{len(ranges)} passages gardés, durée finale {t:.1f}s -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
