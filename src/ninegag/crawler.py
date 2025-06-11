"""9GAG crawling utilities."""

from __future__ import annotations

import logging
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager


logger = logging.getLogger(__name__)


@dataclass
class VideoData:
    """Information about a 9GAG video post."""

    post_id: str
    title: str
    video_url: str
    mobile_url: str
    thumbnail_url: str
    author: str
    tags: List[str]
    stats: Dict[str, int]
    published: Optional[datetime] = None
    duration: Optional[str] = None
    category: str = ""
    extracted_at: datetime = field(default_factory=datetime.now)


class NineGagCrawler:
    """Crawl 9GAG video posts using Selenium."""

    def __init__(self, headless: bool = True, driver_path: Optional[str] = None) -> None:
        self.videos: List[VideoData] = []
        self.driver: Optional[webdriver.Chrome] = None
        self.headless = headless
        self.driver_path = driver_path
        self.setup_driver()

    def setup_driver(self) -> None:
        """Initialize the Chrome driver."""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )

        driver_path = self.driver_path or os.getenv("CHROMEDRIVER_PATH")
        if not driver_path:
            driver_path = ChromeDriverManager().install()

        chromedriver_path = (
            driver_path
            if os.name != "nt"
            else os.path.join(os.path.dirname(driver_path), "chromedriver.exe")
        )
        service = Service(chromedriver_path)

        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        logger.info("Chrome driver initialized successfully")

    def crawl_category(self, category: str, scroll_times: int = 3) -> List[VideoData]:
        """Return a list of videos from a 9GAG category."""

        url = f"https://9gag.com/interest/{category}"
        logger.info("Crawling %s", url)

        self.driver.get(url)
        time.sleep(3)

        try:
            cookie_button = self.driver.find_element(
                By.CSS_SELECTOR, '[data-testid="cookie-banner-accept"]'
            )
            cookie_button.click()
            time.sleep(1)
        except Exception:
            pass

        for _ in range(scroll_times):
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            time.sleep(2)

        return self._extract_all_videos(category)

    def _extract_all_videos(self, category: str) -> List[VideoData]:
        videos: List[VideoData] = []
        selectors = ["article[data-entry-id]", 'article[id^="jsid-post-"]']

        try:
            WebDriverWait(self.driver, 10).until(
                lambda d: any(
                    d.find_elements(By.CSS_SELECTOR, sel) for sel in selectors
                )
            )
        except TimeoutException:
            logger.error("Page failed to load articles within timeout")
            return videos

        articles = []
        for sel in selectors:
            articles.extend(self.driver.find_elements(By.CSS_SELECTOR, sel))

        seen: set[str] = set()
        unique_articles = []
        for art in articles:
            pid = (
                art.get_attribute("data-entry-id")
                or art.get_attribute("id")
                or ""
            )
            if pid and pid not in seen:
                seen.add(pid)
                unique_articles.append(art)

        articles = unique_articles

        for article in articles:
            video_data = self._extract_video_from_article(article, category)
            if video_data:
                videos.append(video_data)

        logger.info("Found %d videos", len(videos))
        return videos

    def _extract_video_from_article(
        self, article, category: str
    ) -> Optional[VideoData]:
        try:
            post_id = (
                article.get_attribute("data-entry-id")
                or article.get_attribute("id")
                or ""
            )
            post_id = post_id.replace("jsid-post-", "")
            if not post_id:
                return None

            title = "Untitled"
            try:
                title_elem = article.find_element(By.CSS_SELECTOR, "header h2")
                if title_elem:
                    title = title_elem.text
            except Exception:
                pass

            is_video = False
            video_url = None
            mobile_url = None
            thumbnail = ""

            try:
                video_elem = article.find_element(By.TAG_NAME, "video")
                is_video = True
                thumbnail = video_elem.get_attribute("poster") or ""
                sources = video_elem.find_elements(By.TAG_NAME, "source")
                for source in sources:
                    src = source.get_attribute("src")
                    if not src:
                        continue
                    src_type = source.get_attribute("type") or ""
                    if "mp4" in src_type or src.endswith(".mp4"):
                        if "460sv" in src:
                            mobile_url = src
                        else:
                            video_url = src
                    elif not video_url:
                        video_url = src
            except Exception:
                try:
                    article.find_element(By.CSS_SELECTOR, ".video-post")
                    is_video = True
                except Exception:
                    pass

            if not is_video:
                return None

            if not video_url:
                video_url = f"https://img-9gag-fun.9cache.com/photo/{post_id}_460sv.mp4"
                mobile_url = (
                    f"https://img-9gag-fun.9cache.com/photo/{post_id}_460svav1.mp4"
                )
                if not thumbnail:
                    thumbnail = (
                        f"https://img-9gag-fun.9cache.com/photo/{post_id}_460s.jpg"
                    )

            author = "Unknown"
            try:
                author_elem = article.find_element(
                    By.CSS_SELECTOR, ".ui-post-creator__author"
                )
                if author_elem:
                    author = author_elem.text
            except Exception:
                pass

            tags: List[str] = []
            try:
                tag_elems = article.find_elements(By.CSS_SELECTOR, ".post-tags a")
                for tag_elem in tag_elems:
                    tag_text = tag_elem.text.strip()
                    if tag_text:
                        tags.append(tag_text)
            except Exception:
                pass

            stats = self._extract_stats(article)

            duration = None
            try:
                duration_elem = article.find_element(By.CSS_SELECTOR, ".length")
                if duration_elem:
                    duration = duration_elem.text
            except Exception:
                pass

            published = None
            try:
                time_elem = article.find_element(By.TAG_NAME, "time")
                if time_elem:
                    dt = (
                        time_elem.get_attribute("datetime")
                        or time_elem.get_attribute("content")
                        or time_elem.get_attribute("title")
                        or time_elem.text
                    )
                    published = self._parse_date(dt)
            except Exception:
                try:
                    meta_elem = article.find_element(
                        By.CSS_SELECTOR, "meta[itemprop='uploadDate']"
                    )
                    if meta_elem:
                        published = self._parse_date(meta_elem.get_attribute("content"))
                except Exception:
                    pass

            return VideoData(
                post_id=post_id,
                title=title,
                video_url=video_url or "",
                mobile_url=mobile_url or video_url or "",
                thumbnail_url=thumbnail,
                author=author,
                tags=tags,
                stats=stats,
                published=published,
                duration=duration,
                category=category,
            )
        except Exception as exc:  # pragma: no cover - Selenium dependent
            logger.error("Error extracting video data: %s", exc)
            return None

    def _extract_stats(self, article) -> Dict[str, int]:
        stats = {"upvotes": 0, "comments": 0}
        try:
            try:
                upvote_elem = article.find_element(By.CSS_SELECTOR, "span.upvote")
                if upvote_elem and upvote_elem.text:
                    stats["upvotes"] = self._parse_number(upvote_elem.text)
            except Exception:
                try:
                    upvote_container = article.find_element(
                        By.CSS_SELECTOR, ".btn-vote"
                    )
                    spans = upvote_container.find_elements(By.TAG_NAME, "span")
                    for span in spans:
                        if (
                            span.text
                            and span.text.strip()
                            and "comment" not in span.text.lower()
                        ):
                            stats["upvotes"] = self._parse_number(span.text)
                            break
                except Exception:
                    pass

            try:
                comment_elem = article.find_element(
                    By.CSS_SELECTOR, "a.comment span:first-child"
                )
                if comment_elem and comment_elem.text:
                    stats["comments"] = self._parse_number(comment_elem.text)
            except Exception:
                try:
                    comment_link = article.find_element(By.CSS_SELECTOR, "a.comment")
                    spans = comment_link.find_elements(By.TAG_NAME, "span")
                    for span in spans:
                        text = span.text.strip()
                        if text and (
                            text.isdigit() or "k" in text.lower() or "m" in text.lower()
                        ):
                            stats["comments"] = self._parse_number(text)
                            break
                except Exception:
                    pass
        except Exception as exc:  # pragma: no cover - Selenium dependent
            logger.debug("Error extracting stats: %s", exc)

        return stats

    def _parse_number(self, text: str) -> int:
        if not text or not isinstance(text, str):
            return 0

        text = text.strip().upper()
        if not text:
            return 0
        try:
            cleaned = re.sub(r"[^\d.KM]", "", text)
            if "K" in cleaned:
                number = cleaned.replace("K", "").strip()
                return int(float(number) * 1000)
            if "M" in cleaned:
                number = cleaned.replace("M", "").strip()
                return int(float(number) * 1_000_000)
            numbers = re.findall(r"\d+", text)
            if numbers:
                return int(numbers[0])
            return 0
        except (ValueError, AttributeError):
            return 0

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse a date string into a datetime object if possible."""
        if not date_str:
            return None
        date_str = date_str.strip()
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
        return None

    def close(self) -> None:
        if self.driver:
            self.driver.quit()
            logger.info("Driver closed")
