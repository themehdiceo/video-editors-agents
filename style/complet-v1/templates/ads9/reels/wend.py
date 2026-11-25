"""Fin réelle des mots sur un extrait court (Gemini précis à ±0,05 s). usage: wend.py src.mov t0 t1"""
import base64, json, os, subprocess, sys, urllib.request
src, a, b = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]); tmp = f"/tmp/claude-501/wend.opus"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a), "-t", str(b - a), "-i", src, "-ac", "1", "-c:a", "libopus", "-b:a", "32k", tmp], check=True)
body = {"contents": [{"parts": [{"inline_data": {"mime_type": "audio/ogg", "data": base64.b64encode(open(tmp, "rb").read()).decode()}}, {"text": "Transcribe word by word with precise start/end times in seconds from the start of this clip. JSON only {words:[{w,start,end}]}"}]}], "generationConfig": {"responseMimeType": "application/json", "temperature": 0}}
r = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent", data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
d = json.loads(json.load(urllib.request.urlopen(r))["candidates"][0]["content"]["parts"][0]["text"])
print([(w["w"], round(w["start"] + a, 2), round(w["end"] + a, 2)) for w in d["words"]][-4:])
