#!/usr/bin/env python3
"""
main.py - Complete 9GAG Video Creator with AI Integration
"""

import os
import re
import json
import time
import asyncio
import hashlib
import subprocess
import random
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
import logging

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Other imports
import requests
import openai
from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class VideoData:
    """Video information from 9GAG"""
    post_id: str
    title: str
    video_url: str
    mobile_url: str
    thumbnail_url: str
    author: str
    tags: List[str]
    stats: Dict[str, int]
    duration: Optional[str] = None
    category: str = ""
    extracted_at: datetime = field(default_factory=datetime.now)


class NineGagCrawler:
    """Selenium-based 9GAG crawler with updated selectors"""
    
    def __init__(self, headless: bool = True):
        self.videos = []
        self.driver = None
        self.headless = headless
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome driver with optimal settings"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        )

        try:
            driver_path = ChromeDriverManager().install()
            if os.name == 'nt':
                driver_folder = os.path.dirname(driver_path)
                chromedriver_path = os.path.join(driver_folder, "chromedriver.exe")
            else:
                chromedriver_path = driver_path
            
            service = Service(chromedriver_path)

            self.driver = webdriver.Chrome(
                service=service,
                options=chrome_options
            )
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            logger.info("Chrome driver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {e}")
            raise
    
    def crawl_category(self, category: str, scroll_times: int = 3) -> List[VideoData]:
        """Crawl a specific 9GAG category"""
        url = f"https://9gag.com/interest/{category}"
        logger.info(f"Crawling {category} category: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(3)
            
            try:
                cookie_button = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="cookie-banner-accept"]')
                cookie_button.click()
                time.sleep(1)
            except Exception:
                pass
            
            for i in range(scroll_times):
                logger.info(f"Scrolling... {i+1}/{scroll_times}")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            videos = self._extract_all_videos(category)
            logger.info(f"Found {len(videos)} videos in {category}")
            
            return videos
        
        except Exception as e:
            logger.error(f"Error crawling {category}: {e}")
            return []
    
    def _extract_all_videos(self, category: str) -> List[VideoData]:
        """Extract all videos from current page"""
        videos = []
        
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'article[id^="jsid-post-"]'))
            )
        except TimeoutException:
            logger.error("Page failed to load articles within timeout")
            return videos
        
        articles = self.driver.find_elements(By.CSS_SELECTOR, 'article[id^="jsid-post-"]')
        logger.info(f"Found {len(articles)} articles on page")
        
        for article in articles:
            try:
                video_data = self._extract_video_from_article(article, category)
                if video_data:
                    videos.append(video_data)
                    logger.debug(f"Extracted video: {video_data.title}")
            except Exception as e:
                logger.error(f"Error extracting video: {e}")
                continue
        
        return videos
    
    def _extract_video_from_article(self, article, category: str) -> Optional[VideoData]:
        """Extract video data from article element"""
        try:
            post_id = article.get_attribute('id').replace('jsid-post-', '')
            if not post_id:
                logger.debug("No post ID found")
                return None
            
            title = "Untitled"
            try:
                title_elem = article.find_element(By.CSS_SELECTOR, 'header h2')
                if title_elem:
                    title = title_elem.text
            except Exception:
                logger.debug(f"No title found for post {post_id}")
            
            is_video = False
            video_url = None
            mobile_url = None
            thumbnail = ""
            
            try:
                video_elem = article.find_element(By.TAG_NAME, 'video')
                is_video = True
                thumbnail = video_elem.get_attribute('poster') or ''
                sources = video_elem.find_elements(By.TAG_NAME, 'source')
                for source in sources:
                    src = source.get_attribute('src')
                    if not src:
                        continue
                    src_type = source.get_attribute('type') or ''
                    if 'mp4' in src_type or src.endswith('.mp4'):
                        if '460sv' in src:
                            mobile_url = src
                        else:
                            video_url = src
                    elif not video_url:
                        video_url = src
            except Exception:
                try:
                    video_container = article.find_element(By.CSS_SELECTOR, '.video-post')
                    if video_container:
                        is_video = True
                        logger.debug(f"Found video-post container for {post_id}")
                except Exception:
                    pass
            
            if not is_video:
                logger.debug(f"Post {post_id} is not a video")
                return None
            
            if not video_url and post_id:
                video_url = f"https://img-9gag-fun.9cache.com/photo/{post_id}_460sv.mp4"
                mobile_url = f"https://img-9gag-fun.9cache.com/photo/{post_id}_460svav1.mp4"
                if not thumbnail:
                    thumbnail = f"https://img-9gag-fun.9cache.com/photo/{post_id}_460s.jpg"
            
            author = "Unknown"
            try:
                author_elem = article.find_element(By.CSS_SELECTOR, '.ui-post-creator__author')
                if author_elem:
                    author = author_elem.text
            except Exception:
                logger.debug(f"No author found for post {post_id}")
            
            tags = []
            try:
                tag_elems = article.find_elements(By.CSS_SELECTOR, '.post-tags a')
                for tag_elem in tag_elems:
                    tag_text = tag_elem.text.strip()
                    if tag_text:
                        tags.append(tag_text)
            except Exception:
                logger.debug(f"No tags found for post {post_id}")
            
            stats = self._extract_stats(article)
            
            duration = None
            try:
                duration_elem = article.find_element(By.CSS_SELECTOR, '.length')
                if duration_elem:
                    duration = duration_elem.text
            except Exception:
                pass
            
            video_data = VideoData(
                post_id=post_id,
                title=title,
                video_url=video_url or "",
                mobile_url=mobile_url or video_url or "",
                thumbnail_url=thumbnail,
                author=author,
                tags=tags,
                stats=stats,
                duration=duration,
                category=category
            )
            
            logger.debug(f"Successfully extracted video: {post_id} - {title[:30]}...")
            return video_data
        
        except Exception as e:
            logger.error(f"Error extracting video data: {e}")
            return None
    
    def _extract_stats(self, article) -> Dict[str, int]:
        """Extract engagement statistics"""
        stats = {'upvotes': 0, 'comments': 0}
        
        try:
            try:
                upvote_elem = article.find_element(By.CSS_SELECTOR, 'span.upvote')
                if upvote_elem and upvote_elem.text:
                    stats['upvotes'] = self._parse_number(upvote_elem.text)
            except Exception:
                try:
                    upvote_container = article.find_element(By.CSS_SELECTOR, '.btn-vote')
                    spans = upvote_container.find_elements(By.TAG_NAME, 'span')
                    for span in spans:
                        if span.text and span.text.strip() and 'comment' not in span.text.lower():
                            stats['upvotes'] = self._parse_number(span.text)
                            break
                except Exception:
                    pass
            
            try:
                comment_elem = article.find_element(By.CSS_SELECTOR, 'a.comment span:first-child')
                if comment_elem and comment_elem.text:
                    stats['comments'] = self._parse_number(comment_elem.text)
            except Exception:
                try:
                    comment_link = article.find_element(By.CSS_SELECTOR, 'a.comment')
                    spans = comment_link.find_elements(By.TAG_NAME, 'span')
                    for span in spans:
                        text = span.text.strip()
                        if text and text.isdigit() or 'k' in text.lower() or 'm' in text.lower():
                            stats['comments'] = self._parse_number(text)
                            break
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"Error extracting stats: {e}")
        
        return stats
    
    def _parse_number(self, text: str) -> int:
        """Parse number with K/M notation"""
        if not text or not isinstance(text, str):
            return 0
            
        text = text.strip().upper()
        if not text:
            return 0
        try:
            cleaned = re.sub(r'[^\d.KM]', '', text)
            if 'K' in cleaned:
                number = cleaned.replace('K', '').strip()
                return int(float(number) * 1000)
            elif 'M' in cleaned:
                number = cleaned.replace('M', '').strip()
                return int(float(number) * 1000000)
            else:
                numbers = re.findall(r'\d+', text)
                if numbers:
                    return int(numbers[0])
                return 0
        except (ValueError, AttributeError):
            return 0
    
    def close(self):
        if self.driver:
            self.driver.quit()
            logger.info("Driver closed")


class AIContentGenerator:
    """AI-powered content generation using OpenAI"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        openai.api_key = api_key
        self.cache_dir = Path('.ai_cache')
        self.cache_dir.mkdir(exist_ok=True)
    
    async def generate_new_title(self, video: VideoData) -> str:
        title_styles = [
            "clickbait question",
            "shocking revelation",
            "emotional story",
            "relatable moment",
            "unexpected twist"
        ]
        style = random.choice(title_styles)
        prompt = f"""
        Create a {style} style title for this {video.category} video.
        Original context: {video.title}
        Engagement: {video.stats['upvotes']} likes
        Just give me the title, nothing else.
        """
        try:
            response = await self._get_ai_response(prompt, temperature=0.9, max_tokens=30)
            return response.strip().strip('"').strip("'")
        except Exception as e:
            logger.error(f"Title generation failed: {e}")
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
            "Comparison hook"
        ]
        pattern = random.choice(hook_patterns)
        tones = ["funny", "shocking", "heartwarming", "mysterious", "relatable", "epic"]
        tone = random.choice(tones)
        prompt = f"""
        Create a {tone} {pattern} hook for this {video.category} video.
        Video: {video.title}
        Stats: {video.stats['upvotes']} likes, {video.stats['comments']} comments
        Pattern: {pattern}
        Tone: {tone}
        Just give me the hook, nothing else.
        """
        try:
            response = await self._get_ai_response(prompt, temperature=0.95, max_tokens=30)
            hook = response.strip().strip('"')
            if len(hook) > 60:
                hook = hook[:57] + "..."
            return hook
        except Exception as e:
            logger.error(f"AI hook generation failed: {e}")
            return "You need to see this 👀"
    
    async def generate_subtitle(self, video: VideoData, hook: str) -> str:
        strategies = [
            "social_proof",
            "urgency",
            "exclusivity",
            "curiosity_gap",
            "warning",
            "promise"
        ]
        strategy = random.choice(strategies)
        prompt = f"""
        Create a {strategy} subtitle for this video.
        Hook: "{hook}"
        Video: {video.title}
        Likes: {video.stats['upvotes']}
        Comments: {video.stats['comments']}
        Just give me the subtitle, nothing else.
        """
        try:
            response = await self._get_ai_response(prompt, temperature=0.9, max_tokens=25)
            subtitle = response.strip().strip('"')
            if len(subtitle) > 40:
                subtitle = subtitle[:37] + "..."
            return subtitle
        except Exception as e:
            logger.error(f"AI subtitle generation failed: {e}")
            return "📱 Breaking the internet"
    
    async def generate_description(self, video: VideoData, hook: str) -> str:
        prompt = f"""
        Write a 2-3 sentence description for this {video.category} video.
        Hook: "{hook}"
        Title: {video.title}
        Just give me the description, nothing else.
        """
        try:
            response = await self._get_ai_response(prompt, temperature=0.8, max_tokens=80)
            return response.strip()
        except Exception as e:
            logger.error(f"Description generation failed: {e}")
            return f"This is the {video.category} content that broke the internet."
    
    async def generate_hashtags(self, video: VideoData, count: int = 10) -> List[str]:
        prompt = f"""
        Generate {count} viral hashtags for this {video.category} video.
        Title: {video.title}
        One hashtag per line, include the # symbol.
        Just give me the hashtags, nothing else.
        """
        try:
            response = await self._get_ai_response(prompt, temperature=0.7, max_tokens=100)
            hashtags = [line.strip() for line in response.split('\n') if line.strip().startswith('#')]
            return hashtags[:count]
        except Exception as e:
            logger.error(f"Hashtag generation failed: {e}")
            return [f"#{video.category}"]
    
    async def analyze_category(self, videos: List[VideoData]) -> Dict:
        top_videos = sorted(videos, key=lambda v: v.stats['upvotes'], reverse=True)[:5]
        titles = [v.title for v in top_videos]
        all_tags = list(set(tag for v in top_videos for tag in v.tags))
        avg_likes = sum(v.stats['upvotes'] for v in top_videos) / len(top_videos) if top_videos else 0
        prompt = f"""
        Analyze these top {videos[0].category} videos for success patterns:
        Top titles: {json.dumps(titles[:3])}
        Popular tags: {json.dumps(all_tags[:10])}
        Average likes: {avg_likes:.0f}
        Give me 3-4 sentences with actionable insights.
        """
        try:
            response = await self._get_ai_response(prompt, temperature=0.3, max_tokens=150)
            return {
                "analysis": response,
                "top_tags": all_tags[:10],
                "avg_engagement": avg_likes,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Category analysis failed: {e}")
            return {"analysis": "Analysis failed", "error": str(e)}
    
    async def _get_ai_response(self, prompt: str, temperature: float = 0.8, max_tokens: int = 100) -> str:
        cache_key = hashlib.md5(f"{prompt}{temperature}{max_tokens}".encode()).hexdigest()
        cache_file = self.cache_dir / f"{cache_key}.txt"
        use_cache = "Generate" not in prompt
        if use_cache and cache_file.exists():
            age = time.time() - cache_file.stat().st_mtime
            if age < 3600:
                return cache_file.read_text()
        for attempt in range(3):
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a viral social media expert. Create unique, engaging content."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                result = response.choices[0].message.content
                if use_cache:
                    cache_file.write_text(result)
                return result
            except openai.error.RateLimitError as e:
                if attempt < 2:
                    wait_time = (attempt + 1) * 20
                    logger.warning(f"Rate limit hit, waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise e
            except Exception as e:
                logger.error(f"OpenAI API error: {e}")
                if attempt < 2:
                    time.sleep(5)
                else:
                    raise e
        raise Exception("Failed to get AI response after 3 attempts")


class VideoProcessor:
    """Process videos with templates"""
    
    def __init__(self):
        self.output_dir = Path('./output')
        self.output_dir.mkdir(exist_ok=True)
    
    def download_video(self, video: VideoData) -> Optional[Path]:
        download_dir = self.output_dir / 'downloads' / video.category
        download_dir.mkdir(parents=True, exist_ok=True)
        filepath = download_dir / f"{video.post_id}.mp4"
        if filepath.exists():
            logger.info(f"Video already downloaded: {video.post_id}")
            return filepath
        try:
            response = requests.get(video.mobile_url, stream=True)
            response.raise_for_status()
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info(f"Downloaded: {video.post_id}")
            return filepath
        except Exception as e:
            logger.error(f"Download failed for {video.post_id}: {e}")
            return None
    
    def create_templated_video(self, video_path: Path, video_data: VideoData, hook: str, subtitle: str, template: str = "modern") -> Optional[Path]:
        output_dir = self.output_dir / 'templated' / video_data.category
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{video_data.post_id}_{template}.mp4"
        templates = {
            "modern": {
                "bg_color": "black",
                "hook_bg": "black@0.7",
                "text_color": "white",
                "accent": "#FF0066",
                "hook_size": 72,
                "subtitle_size": 48
            }
        }
        config = templates.get(template, templates["modern"])
        cmd = [
            'ffmpeg', '-y',
            '-i', str(video_path),
            '-filter_complex',
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color={config['bg_color']}[scaled];"
            f"[scaled]drawbox=x=0:y=40:w=1080:h=150:color={config['hook_bg']}:t=fill[bg1];"
            f"[bg1]drawtext=text='{self._escape_text(hook)}':fontsize={config['hook_size']}:fontcolor={config['text_color']}:x=(w-text_w)/2:y=80:shadowcolor=black@0.8:shadowx=3:shadowy=3[text1];"
            f"[text1]drawbox=x=0:y=210:w=1080:h=100:color={config['hook_bg']}:t=fill[bg2];"
            f"[bg2]drawtext=text='{self._escape_text(subtitle)}':fontsize={config['subtitle_size']}:fontcolor={config['accent']}:x=(w-text_w)/2:y=240:shadowcolor=black@0.8:shadowx=2:shadowy=2",
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-movflags', '+faststart',
            '-t', '30',
            str(output_path)
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"Created templated video: {output_path.name}")
                return output_path
            else:
                logger.error(f"FFmpeg error: {result.stderr}")
                return None
        except Exception as e:
            logger.error(f"Failed to create video: {e}")
            return None
    
    def _escape_text(self, text: str) -> str:
        replacements = [
            ('\\', '\\\\'),
            ("'", "\\'"),
            ('"', '\\"'),
            (':', '\\:'),
            (',', '\\,'),
            ('[', '\\['),
            (']', '\\]'),
            (';', '\\;'),
            ('=', '\\='),
            ('%', '\\%'),
            ('$', '\\$'),
            ('#', '\\#'),
            ('&', '\\&'),
            ('(', '\\('),
            (')', '\\)'),
            ('{', '\\{'),
            ('}', '\\}'),
            ('\n', ' '),
            ('\r', ' '),
        ]
        result = text
        for old, new in replacements:
            result = result.replace(old, new)
        return result


class NineGagVideoCreator:
    """Main orchestrator for the video creation pipeline"""
    
    def __init__(self, openai_key: str):
        self._create_directories()
        self.crawler = NineGagCrawler(headless=True)
        self.ai_generator = AIContentGenerator(openai_key)
        self.processor = VideoProcessor()
        self.results_dir = Path('./results')
    
    def _create_directories(self):
        directories = [
            "output",
            "output/downloads",
            "output/templated",
            "results",
            "summaries",
            ".ai_cache"
        ]
        for dir_path in directories:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        logger.info("✅ All directories created")
    
    async def create_daily_content(self, category: str, count: int = 10):
        logger.info(f"Creating content for: {category}")
        videos = self.crawler.crawl_category(category, scroll_times=5)
        if not videos:
            logger.error("No videos found!")
            return []
        category_context = await self.ai_generator.analyze_category(videos)
        videos.sort(key=lambda v: v.stats['upvotes'], reverse=True)
        selected_videos = videos[:count]
        results = []
        for i, video in enumerate(selected_videos, 1):
            logger.info(f"[{i}/{len(selected_videos)}] Processing: {video.title[:50]}...")
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
                output_path = self.processor.create_templated_video(
                    video_path, video, hook, subtitle, template
                )
                if output_path:
                    result = {
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
                        "created_at": datetime.now().isoformat()
                    }
                    results.append(result)
                    logger.info("✅ Video created successfully!")
            except Exception as e:
                logger.error(f"Failed to process video: {e}")
        self._save_results(results, category)
        if results:
            self._generate_summary_report(results, category)
        logger.info(f"Created {len(results)} videos successfully!")
        return results
    
    def _generate_summary_report(self, results: List[Dict], category: str):
        summary_dir = Path('./summaries')
        summary_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        summary_file = summary_dir / f"{category}_summary_{timestamp}.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"9GAG Video Creator Summary\n")
            f.write(f"Category: {category}\n")
            f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Videos Created: {len(results)}\n")
            f.write(f"Total Original Engagement: {sum(r['stats']['upvotes'] for r in results):,} likes\n\n")
            for i, result in enumerate(results, 1):
                f.write(f"\n{i}. {result['new_title']}\n")
                f.write(f"   Original: {result['original_title']}\n")
                f.write(f"   Hook: {result['hook']}\n")
                f.write(f"   Subtitle: {result['subtitle']}\n")
                f.write(f"   Description: {result['description']}\n")
                f.write(f"   Top Hashtags: {' '.join(result['hashtags'][:5])}\n")
                f.write(f"   Stats: {result['stats']['upvotes']:,} likes, {result['stats']['comments']:,} comments\n")
                f.write(f"   Template: {result['template']}\n")
                f.write(f"   Source: {result['source_url']}\n")
        logger.info(f"Summary report saved to: {summary_file}")
    
    def _save_results(self, results: List[Dict], category: str):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = self.results_dir / f"{category}_{timestamp}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                "category": category,
                "created_at": datetime.now().isoformat(),
                "total_videos": len(results),
                "total_engagement": sum(r['stats']['upvotes'] for r in results),
                "videos": results
            }, f, indent=2, ensure_ascii=False)
        logger.info(f"Results saved to: {results_file}")
    
    def cleanup(self):
        self.crawler.close()


async def main():
    import argparse
    parser = argparse.ArgumentParser(description='9GAG Video Creator with AI')
    parser.add_argument('--category', default='cats', help='Category to crawl')
    parser.add_argument('--count', type=int, default=5, help='Number of videos')
    parser.add_argument('--api-key', help='OpenAI API key')
    args = parser.parse_args()
    api_key = args.api_key or os.getenv('OPENAI_API_KEY')
    if not api_key:
        env_path = Path('.env')
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    if line.startswith('OPENAI_API_KEY='):
                        api_key = line.split('=', 1)[1].strip().strip('"').strip("'")
                        break
    if not api_key:
        logger.error("Please provide OpenAI API key via --api-key, OPENAI_API_KEY env var, or .env file")
        return
    creator = NineGagVideoCreator(api_key)
    try:
        await creator.create_daily_content(args.category, args.count)
    finally:
        creator.cleanup()


if __name__ == '__main__':
    asyncio.run(main())
