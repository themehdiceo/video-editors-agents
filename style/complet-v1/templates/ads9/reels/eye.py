"""Outil œil : pour chaque coupe, 3 images de la source avant la fin du passage (e-0,4 / e-0,2 / e) + 2 au début. usage: eye.py nom -> nom/eye.jpg"""
import json, subprocess, sys, os
H = os.path.dirname(os.path.abspath(__file__)); n = sys.argv[1]
segs = json.load(open(f"{H}/{n}/segs.json")); fr = []
for i, (s, e) in enumerate(segs):
    for t in (s, s + 0.15, e - 0.4, e - 0.2, e - 0.03):
        f = f"{H}/{n}/eye_{len(fr):03d}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(t, 0):.2f}", "-i", f"{H}/{n}.mov", "-frames:v", "1", "-vf",
                        f"scale=180:-2,drawtext=text='{i} {'D' if t < s + 0.2 else 'F'} {t:.2f}':x=4:y=4:fontsize=18:fontcolor=yellow:box=1:boxcolor=black", f], check=True)
        fr.append(f)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{H}/{n}/eye_%03d.jpg", "-vf", "tile=5x" + str(len(segs)), "-frames:v", "1", f"{H}/{n}/eye.jpg"], check=True)
for f in fr: os.remove(f)
print(f"{H}/{n}/eye.jpg")
