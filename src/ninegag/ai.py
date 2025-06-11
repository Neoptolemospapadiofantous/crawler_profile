"""OpenAI-powered content generation for 9GAG videos."""

from __future__ import annotations

import asyncio
import hashlib
from core.logging import get_logger
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import openai

from .crawler import VideoData


logger = get_logger(__name__)


class AIContentGenerator:
    """Generate titles, hooks and descriptions using OpenAI."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        openai.api_key = api_key
        self.cache_dir = Path(".ai_cache")
        self.cache_dir.mkdir(exist_ok=True)

    async def generate_new_title(self, video: VideoData) -> str:
        title_styles = [
            "clickbait question",
            "shocking revelation",
            "emotional story",
            "relatable moment",
            "unexpected twist",
        ]
        style = random.choice(title_styles)
        prompt = (
            f"Create a {style} style title for this {video.category} video.\n"
            f"Original context: {video.title}\n"
            f"Engagement: {video.stats['upvotes']} likes\n"
            "Just give me the title, nothing else."
        )
        try:
            response = await self._get_ai_response(prompt, temperature=0.9, max_tokens=30)
            return response.strip().strip('"').strip("'")
        except Exception as exc:  # pragma: no cover - external service
            logger.error("Title generation failed: %s", exc)
            return f"This {video.category.title()} Video Changes Everything"

    async def generate_hook(self, video: VideoData) -> str:
        hook_patterns = [
            "POV format",
            "Wait for it style",
            "Emotional trigger",
            "Question hook",
            "Statement shock",
            "Challenge format",
            "Warning style",
            "Comparison hook",
        ]
        pattern = random.choice(hook_patterns)
        tones = ["funny", "shocking", "heartwarming", "mysterious", "relatable", "epic"]
        tone = random.choice(tones)
        prompt = (
            f"Create a {tone} {pattern} hook for this {video.category} video.\n"
            f"Video: {video.title}\n"
            f"Stats: {video.stats['upvotes']} likes, {video.stats['comments']} comments\n"
            f"Pattern: {pattern}\nTone: {tone}\nJust give me the hook, nothing else."
        )
        try:
            response = await self._get_ai_response(prompt, temperature=0.95, max_tokens=30)
            hook = response.strip().strip('"')
            if len(hook) > 60:
                hook = hook[:57] + "..."
            return hook
        except Exception as exc:  # pragma: no cover - external service
            logger.error("AI hook generation failed: %s", exc)
            return "You need to see this 👀"

    async def generate_subtitle(self, video: VideoData, hook: str) -> str:
        strategies = [
            "social_proof",
            "urgency",
            "exclusivity",
            "curiosity_gap",
            "warning",
            "promise",
        ]
        strategy = random.choice(strategies)
        prompt = (
            f"Create a {strategy} subtitle for this video.\n"
            f"Hook: \"{hook}\"\n"
            f"Video: {video.title}\n"
            f"Likes: {video.stats['upvotes']}\n"
            f"Comments: {video.stats['comments']}\n"
            "Just give me the subtitle, nothing else."
        )
        try:
            response = await self._get_ai_response(prompt, temperature=0.9, max_tokens=25)
            subtitle = response.strip().strip('"')
            if len(subtitle) > 40:
                subtitle = subtitle[:37] + "..."
            return subtitle
        except Exception as exc:  # pragma: no cover - external service
            logger.error("AI subtitle generation failed: %s", exc)
            return "📱 Breaking the internet"

    async def generate_description(self, video: VideoData, hook: str) -> str:
        prompt = (
            f"Write a 2-3 sentence description for this {video.category} video.\n"
            f"Hook: \"{hook}\"\nTitle: {video.title}\nJust give me the description, nothing else."
        )
        try:
            response = await self._get_ai_response(prompt, temperature=0.8, max_tokens=80)
            return response.strip()
        except Exception as exc:  # pragma: no cover - external service
            logger.error("Description generation failed: %s", exc)
            return f"This is the {video.category} content that broke the internet."

    async def generate_hashtags(self, video: VideoData, count: int = 10) -> List[str]:
        prompt = (
            f"Generate {count} viral hashtags for this {video.category} video.\n"
            f"Title: {video.title}\n"
            "One hashtag per line, include the # symbol.\n"
            "Just give me the hashtags, nothing else."
        )
        try:
            response = await self._get_ai_response(prompt, temperature=0.7, max_tokens=100)
            hashtags = [line.strip() for line in response.split("\n") if line.strip().startswith("#")]
            return hashtags[:count]
        except Exception as exc:  # pragma: no cover - external service
            logger.error("Hashtag generation failed: %s", exc)
            return [f"#{video.category}"]

    async def analyze_category(self, videos: List[VideoData]) -> Dict:
        top_videos = sorted(videos, key=lambda v: v.stats["upvotes"], reverse=True)[:5]
        titles = [v.title for v in top_videos]
        all_tags = list({tag for v in top_videos for tag in v.tags})
        avg_likes = sum(v.stats["upvotes"] for v in top_videos) / len(top_videos) if top_videos else 0
        prompt = (
            f"Analyze these top {videos[0].category} videos for success patterns:\n"
            f"Top titles: {titles[:3]}\n"
            f"Popular tags: {all_tags[:10]}\n"
            f"Average likes: {avg_likes:.0f}\n"
            "Give me 3-4 sentences with actionable insights."
        )
        try:
            response = await self._get_ai_response(prompt, temperature=0.3, max_tokens=150)
            return {
                "analysis": response,
                "top_tags": all_tags[:10],
                "avg_engagement": avg_likes,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as exc:  # pragma: no cover - external service
            logger.error("Category analysis failed: %s", exc)
            return {"analysis": "Analysis failed", "error": str(exc)}

    async def _get_ai_response(self, prompt: str, temperature: float = 0.8, max_tokens: int = 100) -> str:
        logger.debug(
            "Starting _get_ai_response temp=%s max_tokens=%s prompt='%s'",
            temperature,
            max_tokens,
            prompt[:50].replace("\n", " "),
        )

        cache_key = hashlib.md5(f"{prompt}{temperature}{max_tokens}".encode()).hexdigest()
        cache_file = self.cache_dir / f"{cache_key}.txt"
        use_cache = "Generate" not in prompt
        if use_cache and cache_file.exists():
            age = time.time() - cache_file.stat().st_mtime
            if age < 3600:
                logger.debug("Using cached AI response for key %s", cache_key)
                return cache_file.read_text()
        for attempt in range(3):  # pragma: no cover - external service
            try:
                response = await openai.ChatCompletion.acreate(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a viral social media expert. Create unique, engaging content."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                result = response.choices[0].message.content
                if use_cache:
                    cache_file.write_text(result)
                logger.debug(
                    "Received AI response of %d chars for key %s",
                    len(result),
                    cache_key,
                )
                return result
            except openai.RateLimitError:
                if attempt < 2:
                    wait_time = (attempt + 1) * 20
                    logger.warning("Rate limit hit, waiting %s seconds...", wait_time)
                    await asyncio.sleep(wait_time)
                else:
                    raise
            except Exception as exc:
                logger.error("OpenAI API error: %s", exc)
                if attempt < 2:
                    await asyncio.sleep(5)
                else:
                    raise
        logger.debug(
            "Failed to get AI response after retries for key %s",
            cache_key,
        )
        raise RuntimeError("Failed to get AI response after 3 attempts")

