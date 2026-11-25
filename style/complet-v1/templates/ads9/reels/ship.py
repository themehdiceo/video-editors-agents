"""Vérifie (0 BLANC, Gemini 0 mot coupé) et compresse pour le fil. usage: ship.py nom... -> imprime les chemins prêts"""
import json, subprocess, sys, os, re
H = os.path.dirname(os.path.abspath(__file__)); NAMES = json.load(open(f"{H}/names.json")); os.makedirs(f"{H}/../out/fil5", exist_ok=True)
for n in sys.argv[1:]:
    b = open(f"{H}/log_{n}.txt").read().count("BLANC")
    try: pr = [p for p in json.load(open(f"{H}/gck_{n}.txt"))["problems"] if not re.search("breath|stutter|repeat|jump cut", p["issue"], re.I)]
    except Exception as e: pr = [str(e)]
    if b or pr: print("KO", n, b, pr); continue
    o = f"{H}/../out/fil5/{NAMES[n]} v5.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{H}/../out/{NAMES[n]} (apercu).mp4", "-c:v", "libx264", "-crf", "27", "-preset", "fast", "-maxrate", "2.6M", "-bufsize", "5M", "-c:a", "aac", "-b:a", "128k", o], check=True)
    print("OK", os.path.abspath(o))
