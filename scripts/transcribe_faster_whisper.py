#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "faster-whisper>=1.2,<2",
# ]
# ///
from pathlib import Path
import os
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: transcribe_faster_whisper.py AUDIO_PATH", file=sys.stderr)
        return 2

    audio_path = Path(sys.argv[1]).expanduser()
    if not audio_path.is_file():
        print(f"Audio file not found: {audio_path}", file=sys.stderr)
        return 2

    model_name = os.getenv("CDI_FASTER_WHISPER_MODEL", "tiny")
    device = os.getenv("CDI_FASTER_WHISPER_DEVICE", "cpu")
    compute_type = os.getenv("CDI_FASTER_WHISPER_COMPUTE_TYPE", "int8")
    language = os.getenv("CDI_FASTER_WHISPER_LANGUAGE") or None

    from faster_whisper import WhisperModel

    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    segments, _ = model.transcribe(str(audio_path), language=language)
    transcript = " ".join(segment.text.strip() for segment in segments).strip()
    if not transcript:
        print("No speech was transcribed.", file=sys.stderr)
        return 1

    print(transcript)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
