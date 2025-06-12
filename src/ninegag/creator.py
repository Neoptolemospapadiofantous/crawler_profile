"""High level orchestration for creating 9GAG videos."""

from __future__ import annotations

import json
from core.logging import get_logger, log_method_calls
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from .ai import AIContentGenerator
from .crawler import NineGagCrawler, VideoData
from .processor import VideoProcessor


logger = get_logger(__name__)


class NineGagVideoCreator:
    """Combine crawling, AI generation and processing."""

    @log_method_calls
    def __init__(self, openai_key: str) -> None:
        self._create_directories()
        self.crawler = NineGagCrawler(headless=True)
        self.ai_generator = AIContentGenerator(openai_key)
        self.processor = VideoProcessor()
        self.results_dir = Path("./results")

    @log_method_calls
    def _create_directories(self) -> None:
        for dir_path in [
            "output",
            "output/downloads",
            "output/templated",
            "results",
            "summaries",
            ".ai_cache",
        ]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        logger.info("All directories created")

    @log_method_calls
    async def create_daily_content(self, category: str, count: int = 10) -> List[Dict]:
        logger.info("Creating content for: %s", category)
        videos = self.crawler.crawl_category(category, scroll_times=5)
        if not videos:
            logger.error("No videos found!")
            return []
        await self.ai_generator.analyze_category(videos)
        videos.sort(key=lambda v: v.stats["upvotes"], reverse=True)
        selected_videos = videos[:count]
        results: List[Dict] = []
        for i, video in enumerate(selected_videos, 1):
            logger.info("[%s/%s] Processing: %s", i, len(selected_videos), video.title[:50])
            try:
                new_title = await self.ai_generator.generate_new_title(video)
                hook = await self.ai_generator.generate_hook(video)
                subtitle = await self.ai_generator.generate_subtitle(video, hook)
                description = await self.ai_generator.generate_description(video, hook)
                hashtags = await self.ai_generator.generate_hashtags(video, count=15)
                video_path = self.processor.download_video(video)
                if not video_path:
                    continue
                template = "modern"
                output_path = self.processor.create_templated_video(video_path, video, hook, subtitle, template)
                if output_path:
                    results.append(
                        {
                            "video_id": video.post_id,
                            "original_title": video.title,
                            "new_title": new_title,
                            "hook": hook,
                            "subtitle": subtitle,
                            "description": description,
                            "hashtags": hashtags,
                            "template": template,
                            "output_path": str(output_path),
                            "stats": video.stats,
                            "author": video.author,
                            "tags": video.tags,
                            "source_url": f"https://9gag.com/gag/{video.post_id}",
                            "created_at": datetime.now().isoformat(),
                        }
                    )
                    logger.info("Video created successfully!")
            except Exception as exc:  # pragma: no cover - network/dependency
                logger.error("Failed to process video: %s", exc)
        self._save_results(results, category)
        if results:
            self._generate_summary_report(results, category)
        logger.info("Created %d videos successfully!", len(results))
        return results

    @log_method_calls
    def _generate_summary_report(self, results: List[Dict], category: str) -> None:
        summary_dir = Path("./summaries")
        summary_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = summary_dir / f"{category}_summary_{timestamp}.txt"
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write("9GAG Video Creator Summary\n")
            f.write(f"Category: {category}\n")
            f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Videos Created: {len(results)}\n")
            f.write(
                f"Total Original Engagement: {sum(r['stats']['upvotes'] for r in results):,} likes\n\n"
            )
            for i, result in enumerate(results, 1):
                f.write(f"\n{i}. {result['new_title']}\n")
                f.write(f"   Original: {result['original_title']}\n")
                f.write(f"   Hook: {result['hook']}\n")
                f.write(f"   Subtitle: {result['subtitle']}\n")
                f.write(f"   Description: {result['description']}\n")
                f.write(f"   Top Hashtags: {' '.join(result['hashtags'][:5])}\n")
                f.write(
                    f"   Stats: {result['stats']['upvotes']:,} likes, {result['stats']['comments']:,} comments\n"
                )
                f.write(f"   Template: {result['template']}\n")
                f.write(f"   Source: {result['source_url']}\n")
        logger.info("Summary report saved to: %s", summary_file)

    @log_method_calls
    def _save_results(self, results: List[Dict], category: str) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.results_dir / f"{category}_{timestamp}.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "category": category,
                    "created_at": datetime.now().isoformat(),
                    "total_videos": len(results),
                    "total_engagement": sum(r["stats"]["upvotes"] for r in results),
                    "videos": results,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
        logger.info("Results saved to: %s", results_file)

    @log_method_calls
    def cleanup(self) -> None:
        self.crawler.close()

