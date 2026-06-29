import shlex
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Protocol

from app.config import Settings
from app.external import UpstreamServiceError


class AudioTranscriber(Protocol):
    def transcribe_audio(self, filename: str, content: bytes, content_type: str) -> str: ...


def transcribe_audio(
    settings: Settings,
    fallback: AudioTranscriber,
    filename: str,
    content: bytes,
    content_type: str,
) -> str:
    if settings.transcription_command:
        return transcribe_with_command(settings.transcription_command, filename, content, settings.provider_timeout_seconds)
    return fallback.transcribe_audio(filename, content, content_type)


def transcribe_with_command(command: str, filename: str, content: bytes, timeout_seconds: float) -> str:
    suffix = Path(filename).suffix or ".audio"
    with NamedTemporaryFile(suffix=suffix) as audio_file:
        audio_file.write(content)
        audio_file.flush()
        try:
            completed = subprocess.run(
                command_args(command, audio_file.name),
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise UpstreamServiceError(service="Local transcription", detail="command failed") from error
    if completed.returncode != 0:
        raise UpstreamServiceError(service="Local transcription", detail="command failed")
    transcript = completed.stdout.strip()
    if transcript:
        return transcript
    raise UpstreamServiceError(service="Local transcription", detail="empty transcript")


def command_args(command: str, audio_path: str) -> list[str]:
    parts = shlex.split(command)
    if not parts:
        raise UpstreamServiceError(service="Local transcription", detail="command missing")
    expanded = [part.replace("{audio_path}", audio_path) for part in parts]
    return expanded if expanded != parts else [*expanded, audio_path]
