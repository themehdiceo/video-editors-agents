#!/usr/bin/env python3
"""Transcription mot à mot avec faster-whisper.

Usage: transcribe.py <video_ou_audio> <sortie.json> [--model small] [--lang fr|ar|auto]
                     [--prompt "noms, mots du sujet"] [--progress progress.log]

Darija : utiliser --model large-v3-turbo --lang ar (small/base/medium donnent du bruit).

Sortie JSON:
{"language": "fr", "duration": 61.2,
 "words": [{"w": "Bonjour", "start": 0.42, "end": 0.81, "p": 0.98}, ...],
 "segments": [{"start": 0.42, "end": 3.1, "text": "..."}]}
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile


MODEL_ALIASES = {  # faster-whisper < 1.1 ne connaît pas ces noms courts
    "turbo": "mobiuslabsgmbh/faster-whisper-large-v3-turbo",
    "large-v3-turbo": "mobiuslabsgmbh/faster-whisper-large-v3-turbo",
}


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
    args = ap.parse_args()
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
