#!/usr/bin/env python3
"""Transcription mot à mot avec faster-whisper.

Usage: transcribe.py <video_ou_audio> <sortie.json> [--model small] [--lang fr]

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
    args = ap.parse_args()

    from faster_whisper import WhisperModel  # import tardif: lourd

    device = "cuda" if os.environ.get("WHISPER_DEVICE") == "cuda" else "cpu"
    compute = "float16" if device == "cuda" else "int8"
    model = WhisperModel(args.model, device=device, compute_type=compute)

    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "a.wav")
        extract_audio(args.src, wav)
        segments, info = model.transcribe(
            wav,
            language=args.lang,
            word_timestamps=True,
            vad_filter=False,  # on garde les hésitations: c'est le monteur qui décide
        )
        words, segs = [], []
        for s in segments:
            segs.append({"start": round(s.start, 3), "end": round(s.end, 3), "text": s.text.strip()})
            for w in s.words or []:
                words.append({"w": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3),
                              "p": round(w.probability, 3)})

    json.dump({"language": info.language, "duration": round(info.duration, 3),
               "words": words, "segments": segs}, open(args.out, "w"), ensure_ascii=False, indent=1)
    print(f"{len(words)} mots, langue={info.language}, durée={info.duration:.1f}s -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
