"""Video processing utilities for templating."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Optional

import requests

DEFAULT_REQUEST_TIMEOUT = 10

from .crawler import VideoData


logger = logging.getLogger(__name__)


class VideoProcessor:
    """Download videos and render templates using FFmpeg."""

    def __init__(self, request_timeout: int | float = DEFAULT_REQUEST_TIMEOUT) -> None:
        self.output_dir = Path("./output")
        self.output_dir.mkdir(exist_ok=True)
        self.request_timeout = request_timeout

    def download_video(self, video: VideoData) -> Optional[Path]:
        download_dir = self.output_dir / "downloads" / video.category
        download_dir.mkdir(parents=True, exist_ok=True)
        filepath = download_dir / f"{video.post_id}.mp4"
        if filepath.exists():
            logger.info("Video already downloaded: %s", video.post_id)
            return filepath
        try:
            response = requests.get(
                video.mobile_url, stream=True, timeout=self.request_timeout
            )
            response.raise_for_status()
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info("Downloaded: %s", video.post_id)
            return filepath
        except Exception as exc:  # pragma: no cover - network dependent
            logger.error("Download failed for %s: %s", video.post_id, exc)
            return None

    def create_templated_video(
        self,
        video_path: Path,
        video_data: VideoData,
        hook: str,
        subtitle: str,
        template: str = "modern",
    ) -> Optional[Path]:
        output_dir = self.output_dir / "templated" / video_data.category
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{video_data.post_id}_{template}.mp4"
        templates = {
            "modern": {
                "bg_color": "black",
                "hook_bg": "black@0.7",
                "text_color": "white",
                "accent": "#FF0066",
                "hook_size": 72,
                "subtitle_size": 48,
            }
        }
        config = templates.get(template, templates["modern"])
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-filter_complex",
            (
                f"[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
                f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color={config['bg_color']}[scaled];"
                f"[scaled]drawbox=x=0:y=40:w=1080:h=150:color={config['hook_bg']}:t=fill[bg1];"
                f"[bg1]drawtext=text='{self._escape_text(hook)}':fontsize={config['hook_size']}:"
                f"fontcolor={config['text_color']}:x=(w-text_w)/2:y=80:shadowcolor=black@0.8:shadowx=3:shadowy=3[text1];"
                f"[text1]drawbox=x=0:y=210:w=1080:h=100:color={config['hook_bg']}:t=fill[bg2];"
                f"[bg2]drawtext=text='{self._escape_text(subtitle)}':fontsize={config['subtitle_size']}:"
                f"fontcolor={config['accent']}:x=(w-text_w)/2:y=240:shadowcolor=black@0.8:shadowx=2:shadowy=2"
            ),
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            "-t",
            "30",
            str(output_path),
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("Created templated video: %s", output_path.name)
                return output_path
            logger.error("FFmpeg error: %s", result.stderr)
            return None
        except Exception as exc:  # pragma: no cover - ffmpeg dependent
            logger.error("Failed to create video: %s", exc)
            return None

    def _escape_text(self, text: str) -> str:
        replacements = [
            ("\\", "\\\\"),
            ("'", "\\'"),
            ('"', '\\"'),
            (":", "\\:"),
            (",", "\\,"),
            ("[", "\\["),
            ("]", "\\]"),
            (";", "\\;"),
            ("=", "\\="),
            ("%", "\\%"),
            ("$", "\\$"),
            ("#", "\\#"),
            ("&", "\\&"),
            ("(", "\\("),
            (")", "\\)"),
            ("{", "\\{"),
            ("}", "\\}"),
            ("\n", " "),
            ("\r", " "),
        ]
        result = text
        for old, new in replacements:
            result = result.replace(old, new)
        return result

