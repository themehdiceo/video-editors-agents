#!/usr/bin/env python3
"""Zooms x1,08 en cut (toutes les 6-9 s, sur un début de passage) + work/plan.json."""
import json
D = "jobs/20261118-062812-edit/work/"
tm = json.load(open(D + "aroll_cut.mp4.timemap.json")); dur = tm["duration"]
zooms, last, zoomed, z0 = [], 0.0, False, None
for s in [r["dst_start"] for r in tm["ranges"]][1:]:
    if s - last >= 6.0:
        if zoomed: zooms.append([round(z0, 3), round(s, 3), 1.08])
        else: z0 = s
        zoomed = not zoomed; last = s
if zoomed: zooms.append([round(z0, 3), round(dur, 3), 1.08])
plan = {"aroll": "work/aroll_cut.mp4", "out": "out/final.mp4", "format": {"w": 1920, "h": 1080, "fps": 30},
        "crop_x": 0.5, "zooms": zooms, "subtitles": "work/subs.ass", "audio_raw": True, "encoder": "videotoolbox",
        "broll": [], "overlays": [], "sfx": [], "mute": [],
        "note": "Voix d'origine intacte (audio_raw). aroll_cut.mp4 déjà tone-mappé HLG->bt709. Zooms x1.08 en cut."}
json.dump(plan, open(D + "plan.json", "w"), indent=1, ensure_ascii=False)
print(len(zooms), "zooms ; durée", round(dur, 1), "s")
