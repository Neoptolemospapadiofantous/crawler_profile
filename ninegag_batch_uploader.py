"""Batch uploader for 9GAG videos.

This script crawls 9GAG for videos posted on a specific date,
processes them using predefined templates, and uploads the
rendered results to configured channels.

The code provides a minimal, demonstration-level
implementation. Network and browser interactions may need
additional error handling for production use.
"""

from __future__ import annotations

import json
import subprocess
from argparse import ArgumentParser
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests
import yaml
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from core.logging import get_logger_manager, get_logger

# Local modules
from ninegag.crawler import NineGagCrawler

get_logger_manager()
logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass
class VideoMeta:
    """Metadata about a video to upload."""

    url: str
    title: str
    downloaded_path: Optional[Path] = None


# Template registry stored in JSON
REGISTRY_PATH = Path("templates_registry.json")


def _load_registry() -> Dict[str, Dict[str, object]]:
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_registry(registry: Dict[str, Dict[str, object]]) -> None:
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def register_template(template_dir: Path) -> None:
    """Register a template by reading its manifest file."""
    manifest_path = template_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    name = manifest.get("name", template_dir.name)
    channels = manifest.get("channels", [])
    steps = manifest.get("steps", [])
    asset = manifest.get("asset")

    registry = _load_registry()
    registry[name] = {
        "path": str(template_dir),
        "channels": channels,
        "steps": steps,
    }
    if asset:
        registry[name]["asset"] = str(template_dir / asset)
    _save_registry(registry)
    logger.info("Registered template '%s'", name)


def crawl_9gag_videos(date_str: str, driver_path: Optional[str] = None) -> List[VideoMeta]:
    """Crawl 9GAG for videos on the given date."""
    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    crawler = NineGagCrawler(headless=True, driver_path=driver_path)
    results: List[VideoMeta] = []
    try:
        logger.info("Crawling 9GAG for videos on %s", target_date.isoformat())
        videos = crawler.crawl_category("hot", scroll_times=5)
        download_dir = Path("downloads") / date_str
        download_dir.mkdir(parents=True, exist_ok=True)
        for video in videos:
            if video.published:
                if video.published.date() != target_date:
                    continue
            else:
                logger.warning(
                    "Video %s has no published date; including anyway", video.post_id
                )
            video_path = download_dir / f"{video.post_id}.mp4"
            if not video_path.exists():
                try:
                    r = requests.get(video.mobile_url, stream=True, timeout=15)
                    r.raise_for_status()
                    with open(video_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                except Exception as exc:  # pragma: no cover - network dependent
                    logger.error("Failed downloading %s: %s", video.mobile_url, exc)
                    continue
            results.append(
                VideoMeta(
                    url=video.mobile_url, title=video.title, downloaded_path=video_path
                )
            )
    finally:
        crawler.close()
    logger.info("Found %d videos", len(results))
    return results


def apply_template(video_path: Path, template_name: str) -> Path:
    """Render the specified template onto a video."""
    registry = _load_registry()
    if template_name not in registry:
        raise ValueError(f"Template '{template_name}' not registered")
    template_info = registry[template_name]
    template_path = Path(template_info["path"])
    asset_path = Path(template_info.get("asset", template_path))
    output = video_path.with_name(f"{video_path.stem}_{template_name}.mp4")
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-i",
        str(asset_path),
        "-filter_complex",
        "[0:v][1:v] overlay=0:0",
        "-c:a",
        "copy",
        str(output),
    ]
    logger.info("Applying template '%s' to %s", template_name, video_path.name)
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except Exception as exc:  # pragma: no cover - ffmpeg dependent
        logger.error("Template application failed: %s", exc)
        raise
    return output


def upload_to_channel(processed_videos: List[Path], channel_name: str) -> None:
    """Upload processed videos using a Selenium profile."""
    config_path = Path("channels.yml")
    if not config_path.exists():
        logger.error("channels.yml not found")
        return
    with open(config_path, "r", encoding="utf-8") as f:
        channels = yaml.safe_load(f) or {}
    channel_cfg = channels.get(channel_name)
    if not channel_cfg:
        logger.error("Channel '%s' not configured", channel_name)
        return
    profile_path = channel_cfg.get("profile")
    options = Options()
    if profile_path:
        options.add_argument(f"--user-data-dir={profile_path}")
    driver = webdriver.Chrome(options=options)
    try:
        for video in processed_videos:
            logger.info("Uploading %s to %s", video.name, channel_name)
            driver.get(channel_cfg.get("upload_url", "about:blank"))
            # Actual upload steps depend on the platform and are not implemented
    finally:
        driver.quit()
        logger.info("Upload session finished for %s", channel_name)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = ArgumentParser(description="Batch upload 9GAG videos")
    parser.add_argument("--date", required=True, help="Date of posts YYYY-MM-DD")
    parser.add_argument("--template", required=True, help="Template name")
    parser.add_argument(
        "--driver-path",
        help="Path to ChromeDriver executable (overrides CHROMEDRIVER_PATH)",
    )
    args = parser.parse_args()

    logger.info("Starting ninegag_batch_uploader for date=%s template=%s", args.date, args.template)

    videos = crawl_9gag_videos(args.date, driver_path=args.driver_path)
    processed: List[Path] = []
    for video in videos:
        if video.downloaded_path:
            try:
                processed.append(apply_template(video.downloaded_path, args.template))
            except Exception:
                continue
    registry = _load_registry()
    template_info = registry.get(args.template, {})
    channels = template_info.get("channels", [])
    for channel in channels:
        upload_to_channel(processed, channel)

    logger.info("ninegag_batch_uploader completed successfully")


if __name__ == "__main__":
    logger.info("Launching ninegag_batch_uploader script")
    try:
        main()
    except Exception as exc:
        logger.error("ninegag_batch_uploader failed: %s", exc)
        raise
