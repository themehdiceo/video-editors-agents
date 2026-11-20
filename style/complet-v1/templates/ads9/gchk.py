#!/usr/bin/env python3
"""Réécoute Gemini d'un montage fini. usage: gchk.py out.opus"""
import base64, json, os, sys, urllib.request
a = base64.b64encode(open(sys.argv[1], "rb").read()).decode()
prompt = ("EDITED face-camera Facebook ad, Moroccan Darija mixed with French, light music underneath, then a silent end card. "
          "Check the editing carefully: report every word CUT OFF or clipped at its start or end, any repeated word/retake, audible breath, abrupt jump or audio glitch, with time \"M:SS.s\". "
          "Then transcribe everything in Latin letters. Return ONLY JSON {\"problems\": [{\"t\": \"M:SS.s\", \"issue\": ...}], \"transcript\": \"...\"}.")
body = {"contents": [{"parts": [{"inline_data": {"mime_type": "audio/ogg", "data": a}}, {"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0}}
req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent",
                             data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
print(json.load(urllib.request.urlopen(req, timeout=600))["candidates"][0]["content"]["parts"][0]["text"])
