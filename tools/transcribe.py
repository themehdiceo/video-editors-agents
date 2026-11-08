#!/usr/bin/env python3
"""Transcription mot à mot avec faster-whisper.

Usage: transcribe.py <video_ou_audio> <sortie.json> [--model small] [--lang fr|ar|auto]
                     [--prompt "noms, mots du sujet"] [--progress progress.log]

Moteurs :
- scribe : ElevenLabs Scribe (en ligne, très bon en darija, mots + qui parle). Utilisé automatiquement
  si ELEVENLABS_API_KEY est défini. Modèle : SCRIBE_MODEL (défaut scribe_v1).
- whisper : faster-whisper en local (gratuit). Darija : --model large-v3-turbo --lang ar.
Si Scribe échoue, on retombe sur Whisper.

Sortie JSON:
{"language": "fr", "duration": 61.2,
 "words": [{"w": "Bonjour", "start": 0.42, "end": 0.81, "p": 0.98}, ...],
 "segments": [{"start": 0.42, "end": 3.1, "text": "..."}]}
"""
import argparse
import math
import json
import re
import os
import subprocess
import sys
import tempfile


MODEL_ALIASES = {  # faster-whisper < 1.1 ne connaît pas ces noms courts
    "turbo": "mobiuslabsgmbh/faster-whisper-large-v3-turbo",
    "large-v3-turbo": "mobiuslabsgmbh/faster-whisper-large-v3-turbo",
}


def scribe(src: str, out: str, lang) -> bool:
    """ElevenLabs Speech-to-Text. Écrit le même format que Whisper (+ "speaker" par mot)."""
    import urllib.request
    import uuid
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        return False
    model = os.environ.get("SCRIBE_MODEL", "scribe_v1")
    with tempfile.TemporaryDirectory() as tmp:
        audio = os.path.join(tmp, "a.m4a")  # audio compressé : envoi plus rapide
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-vn", "-ac", "1", "-ar", "16000",
                        "-c:a", "aac", "-b:a", "48k", audio], check=True)
        data = open(audio, "rb").read()
    b = uuid.uuid4().hex
    fields = {"model_id": model, "timestamps_granularity": "word", "diarize": "true", "tag_audio_events": "true"}
    if lang:
        fields["language_code"] = lang
    body = b"".join(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
                    for k, v in fields.items())
    body += (f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="a.m4a"\r\n'
             f"Content-Type: audio/mp4\r\n\r\n").encode() + data + f"\r\n--{b}--\r\n".encode()
    req = urllib.request.Request("https://api.elevenlabs.io/v1/speech-to-text", data=body, method="POST",
                                 headers={"xi-api-key": key, "Content-Type": f"multipart/form-data; boundary={b}"})
    try:
        with urllib.request.urlopen(req, timeout=1800) as r:
            res = json.load(r)
    except Exception as e:  # noqa: BLE001  (la clé n'apparaît jamais dans le message)
        print(f"Scribe indisponible ({e}), passage à Whisper.", file=sys.stderr)
        return False
    words, segs, cur = [], [], None
    events = []  # toux, rires, raclements de gorge… (Scribe les note entre parenthèses)
    for w in res.get("words", []):
        if w.get("type") == "audio_event":
            events.append({"event": w["text"].strip(), "start": round(w["start"], 3), "end": round(w["end"], 3),
                           "speaker": w.get("speaker_id")})
            continue
        if w.get("type") != "word":
            continue
        item = {"w": w["text"].strip(), "start": round(w["start"], 3), "end": round(w["end"], 3),
                "p": round(math.exp(min(0.0, float(w.get("logprob") or 0))), 3), "speaker": w.get("speaker_id")}
        words.append(item)
        # Segments : une phrase par changement de locuteur ou ponctuation finale.
        if cur and (cur["speaker"] != item["speaker"] or cur["text"].endswith((".", "!", "?"))):
            segs.append(cur)
            cur = None
        if cur is None:
            cur = {"start": item["start"], "end": item["end"], "text": item["w"], "speaker": item["speaker"]}
        else:
            cur["end"], cur["text"] = item["end"], cur["text"] + " " + item["w"]
    if cur:
        segs.append(cur)
    dur = words[-1]["end"] if words else 0.0
    json.dump({"language": res.get("language_code"), "model": model, "engine": "scribe", "duration": dur,
               "words": words, "segments": segs, "events": events}, open(out, "w"), ensure_ascii=False, indent=1)
    coughs = sum(1 for e in events if re.search(r"cough|tou|throat|gorge|سعال|يسعل|كحة|يكح", e["event"], re.I))
    print(f"{len(events)} bruits repérés dont {coughs} toux.")
    print(f"{len(words)} mots (Scribe {model}), langue={res.get('language_code')} -> {out}")
    return True


def extract_audio(src: str, dst: str) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-vn", "-ac", "1", "-ar", "16000", dst],
        check=True,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--model", default=os.environ.get("WHISPER_MODEL", "small"))
    ap.add_argument("--lang", default=os.environ.get("WHISPER_LANG") or None)
    ap.add_argument("--prompt", default=None, help="vocabulaire attendu (noms propres, jargon)")
    ap.add_argument("--progress", default=None, help="fichier où ajouter l'avancement (toutes les ~2 min d'audio)")
    ap.add_argument("--engine", choices=["auto", "scribe", "whisper"], default="auto")
    args = ap.parse_args()
    if args.engine in ("auto", "scribe") and os.environ.get("ELEVENLABS_API_KEY"):
        # Scribe attend un code ISO 639-3 ; « ar » de Whisper n'en est pas un : on laisse la détection auto.
        lang3 = args.lang if args.lang and len(args.lang) == 3 else None
        if scribe(args.src, args.out, lang3):
            return 0
        if args.engine == "scribe":
            return 1
    model_name = args.model
    args.model = MODEL_ALIASES.get(args.model, args.model)
    if args.lang in ("auto", ""):
        args.lang = None  # détection automatique

    from faster_whisper import WhisperModel  # import tardif: lourd

    device = "cuda" if os.environ.get("WHISPER_DEVICE") == "cuda" else "cpu"
    compute = "float16" if device == "cuda" else "int8"
    model = WhisperModel(args.model, device=device, compute_type=compute)

    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "a.wav")
        extract_audio(args.src, wav)
        # On décode nous-mêmes le WAV en tableau numpy : évite av.open(metadata_errors=...)
        # qui plante quand PyAV et faster-whisper ne sont pas compatibles.
        import numpy as np
        import wave
        with wave.open(wav, "rb") as wf:
            audio = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
        segments, info = model.transcribe(
            audio,
            language=args.lang,
            word_timestamps=True,
            vad_filter=False,  # on garde les hésitations: c'est le monteur qui décide
            initial_prompt=args.prompt,
            beam_size=5,
        )
        words, segs = [], []
        next_report = 120.0
        for s in segments:
            if args.progress and s.end >= next_report:
                with open(args.progress, "a") as pf:
                    pf.write(f"Transcription : {int(s.end // 60)} min sur {int(info.duration // 60)} min\n")
                next_report += 120.0
            segs.append({"start": round(s.start, 3), "end": round(s.end, 3), "text": s.text.strip()})
            for w in s.words or []:
                words.append({"w": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3),
                              "p": round(w.probability, 3)})

    json.dump({"language": info.language, "model": model_name, "duration": round(info.duration, 3),
               "words": words, "segments": segs}, open(args.out, "w"), ensure_ascii=False, indent=1)
    print(f"{len(words)} mots, langue={info.language}, durée={info.duration:.1f}s -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
