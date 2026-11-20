#!/usr/bin/env python3
"""Transcription Gemini mot à mot. usage: gtr.py audio.opus out.json dur_s"""
import base64, json, os, sys, urllib.request
src, out, dur = sys.argv[1], sys.argv[2], sys.argv[3]
a = base64.b64encode(open(src, "rb").read()).decode()
prompt = (f"Audio ({dur} s): a Moroccan man (Mehdi) films a face-camera Facebook ad, Darija mixed with French. He often restarts sentences (retakes). "
          "Transcribe EVERY word in order, including retakes and false starts. Darija in Latin letters (kifach, 3ndek, 9lil, 7ta), French in French, numbers as digits. "
          "Each word: start/end as strings \"M:SS.ss\". Group words into segments (one sentence or phrase each). Mark retake=true for a segment he abandons and re-says right after. "
          "Return ONLY JSON: list of {\"text\":..., \"retake\": bool, \"words\": [{\"w\":..., \"start\":\"M:SS.ss\", \"end\":\"M:SS.ss\"}]}.")
body = {"contents": [{"parts": [{"inline_data": {"mime_type": "audio/ogg", "data": a}}, {"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0}}
req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent",
                             data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
t = json.load(urllib.request.urlopen(req, timeout=900))["candidates"][0]["content"]["parts"][0]["text"]
s = lambda x: int(x.split(":")[0]) * 60 + float(x.split(":")[1]) if isinstance(x, str) else float(x)
segs = json.loads(t)
for g in segs:
    for w in g["words"]: w["start"], w["end"] = round(s(w["start"]), 2), round(s(w["end"]), 2)
    print(f"{g['words'][0]['start']:6.2f}-{g['words'][-1]['end']:6.2f} {'R ' if g.get('retake') else '  '}{g['text']}")
json.dump(segs, open(out, "w"), ensure_ascii=False, indent=0)
