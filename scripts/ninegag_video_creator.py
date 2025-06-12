#!/usr/bin/env python3
"""Standalone wrapper for the 9GAG video creator."""

import asyncio
import os
from argparse import ArgumentParser
from pathlib import Path
import sys

# Ensure modules can be imported when the package isn't installed
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from core.logging import get_logger_manager, get_logger
from ninegag import NineGagVideoCreator

get_logger_manager()
logger = get_logger(__name__)


def main() -> None:
    parser = ArgumentParser(description="9GAG Video Creator with AI")
    parser.add_argument("--category", default="cats", help="Category to crawl")
    parser.add_argument("--count", type=int, default=5, help="Number of videos")
    parser.add_argument("--api-key", help="OpenAI API key")
    args = parser.parse_args()

    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        env_path = Path(".env")
        if env_path.exists():
            with open(env_path, "r") as f:
                for line in f:
                    if line.startswith("OPENAI_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
    if not api_key:
        print("Please provide OpenAI API key via --api-key, OPENAI_API_KEY env var, or .env file")
        return

    logger.info("Starting ninegag_video_creator with category='%s' count=%s", args.category, args.count)
    creator = NineGagVideoCreator(api_key)

    async def _run() -> None:
        await creator.create_daily_content(args.category, args.count)

    try:
        asyncio.run(_run())
        logger.info("ninegag_video_creator completed successfully")
    except Exception as exc:
        logger.error("ninegag_video_creator failed: %s", exc)
        raise
    finally:
        creator.cleanup()


if __name__ == "__main__":
    logger.info("Launching ninegag_video_creator script")
    try:
        main()
    except Exception:
        logger.exception("ninegag_video_creator run failed")
        raise

