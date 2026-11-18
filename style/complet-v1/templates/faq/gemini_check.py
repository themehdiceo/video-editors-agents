#!/usr/bin/env python3
"""Réécoute du montage par Gemini (accord de Mehdi le 2026-11-18) : reprises, souffles, hésitations.
usage: gemini_check.py audio.opus out.json   (clé GEMINI_API_KEY dans ~/.claude/secrets.env)"""
import base64, json, os, sys, urllib.request
src, out = sys.argv[1], sys.argv[2]
a = base64.b64encode(open(src, "rb").read()).decode()
prompt = ("Audio: a Moroccan man speaking Darija mixed with French (an already edited video, background music under the voice). "
          "Find every remaining editing mistake: (1) repeated words or restarted phrases (he starts a phrase, stops, and says it again), "
          "(2) audible breaths, sighs, blowing air, mouth noises, (3) hesitations like euh/ah, (4) a word cut in the middle. "
          "Timestamps in SECONDS from the start (e.g. 101.4, not 1:41). "
          "Return ONLY JSON: a list of {\"start\": s, \"end\": s, \"type\": \"repeat|breath|hesitation|cut_word\", \"text\": \"what is heard, Latin-script darija\"}. "
          "Return [] if the edit is clean.")
body = {"contents": [{"parts": [{"inline_data": {"mime_type": "audio/ogg", "data": a}}, {"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0}}
req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent",
                             data=json.dumps(body).encode(),
                             headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
t = json.load(urllib.request.urlopen(req, timeout=600))["candidates"][0]["content"]["parts"][0]["text"]
open(out, "w").write(t)
print(t)
