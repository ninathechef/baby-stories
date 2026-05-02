#!/usr/bin/env python3
"""Generate sentence and word audio for Baby Stories using Piper.

This script reads the story text from index.html, then writes generated audio
to audio/pageX.wav and audio/words/<word>.wav. If ffmpeg is installed, it also
creates matching MP3 files for the app.

Usage:
  python3 scripts/generate_piper_audio.py --model /path/to/model.onnx

Requirements:
  - piper executable on PATH
  - Piper voice model (.onnx) and matching .json config
  - Optional: ffmpeg for MP3 conversion
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "index.html"
OUTPUT_DIR = ROOT / "audio"
WORDS_DIR = OUTPUT_DIR / "words"


def extract_story_data(html_text: str) -> tuple[list[str], list[str]]:
    page_texts = re.findall(r'text:\s*"([^"]+)"', html_text)

    word_texts = []
    for raw in re.findall(r'<span class="word">(.*?)</span>', html_text, flags=re.S):
        word = re.sub(r"[^A-Za-z' ]", "", raw).strip().lower()
        word = re.sub(r"\s+", " ", word)
        if word and word not in word_texts:
            word_texts.append(word)

    return page_texts, word_texts


def sanitize_filename(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower().strip()).strip("-")
    return slug or "audio"


def run_piper(text: str, wav_path: Path, model_path: Path) -> None:
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    piper_cmd = [
        "piper",
        "--model",
        str(model_path),
        "--output_file",
        str(wav_path),
    ]

    subprocess.run(
        piper_cmd,
        input=text + "\n",
        text=True,
        check=True,
    )


def convert_to_mp3(wav_path: Path, mp3_path: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return

    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(wav_path),
            "-codec:a",
            "libmp3lame",
            "-q:a",
            "4",
            str(mp3_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Path to a Piper .onnx model")
    parser.add_argument(
        "--skip-words",
        action="store_true",
        help="Generate only page sentence audio",
    )
    parser.add_argument(
        "--skip-pages",
        action="store_true",
        help="Generate only individual word audio",
    )
    args = parser.parse_args()

    model_path = Path(args.model).expanduser().resolve()
    if not model_path.exists():
        raise SystemExit(f"Model not found: {model_path}")

    if not HTML_PATH.exists():
        raise SystemExit(f"Missing story file: {HTML_PATH}")

    html_text = HTML_PATH.read_text(encoding="utf-8")
    page_texts, word_texts = extract_story_data(html_text)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    WORDS_DIR.mkdir(parents=True, exist_ok=True)

    manifest = {
        "pages": page_texts,
        "words": word_texts,
        "model": str(model_path),
    }
    (OUTPUT_DIR / "piper-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )

    if not args.skip_pages:
        for idx, text in enumerate(page_texts, start=1):
            wav_path = OUTPUT_DIR / f"page{idx}.wav"
            mp3_path = OUTPUT_DIR / f"page{idx}.mp3"
            run_piper(text, wav_path, model_path)
            convert_to_mp3(wav_path, mp3_path)

    if not args.skip_words:
        for word in word_texts:
            wav_path = WORDS_DIR / f"{sanitize_filename(word)}.wav"
            mp3_path = WORDS_DIR / f"{sanitize_filename(word)}.mp3"
            run_piper(word, wav_path, model_path)
            convert_to_mp3(wav_path, mp3_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())