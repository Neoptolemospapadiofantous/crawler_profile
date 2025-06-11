from pathlib import Path
import types
from datetime import datetime

import pytest

from ninegag_batch_uploader import apply_template, crawl_9gag_videos, upload_to_channel


class DummyCrawler:
    def __init__(self, headless=True, driver_path=None):
        pass

    def crawl_category(self, category, scroll_times=5):
        from ninegag.crawler import VideoData

        return [
            VideoData(
                post_id="abc",
                title="Funny",
                video_url="http://example.com/video.mp4",
                mobile_url="http://example.com/video.mp4",
                thumbnail_url="",
                author="tester",
                tags=[],
                stats={"upvotes": 1, "comments": 0},
                published=datetime(2023, 1, 1, 12, 0, 0),
                category=category,
            ),
            VideoData(
                post_id="xyz",
                title="Other",
                video_url="http://example.com/video2.mp4",
                mobile_url="http://example.com/video2.mp4",
                thumbnail_url="",
                author="tester",
                tags=[],
                stats={"upvotes": 1, "comments": 0},
                published=datetime(2023, 1, 2, 12, 0, 0),
                category=category,
            ),
        ]

    def close(self):
        pass


class DummyResp:
    def raise_for_status(self):
        pass

    def iter_content(self, chunk_size=8192):
        yield b"data"


def test_crawl_9gag_videos_downloads_to_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("ninegag_batch_uploader.NineGagCrawler", DummyCrawler)
    monkeypatch.setattr(
        "ninegag_batch_uploader.requests.get", lambda *a, **k: DummyResp()
    )

    results = crawl_9gag_videos("2023-01-01")

    expected = tmp_path / "downloads" / "2023-01-01" / "abc.mp4"
    skipped = tmp_path / "downloads" / "2023-01-01" / "xyz.mp4"
    assert len(results) == 1
    assert results[0].downloaded_path.resolve() == expected.resolve()
    assert expected.exists()
    assert not skipped.exists()


def test_apply_template_returns_output_path(tmp_path, monkeypatch):
    video_file = tmp_path / "vid.mp4"
    video_file.write_bytes(b"input")
    template_file = tmp_path / "template.mp4"
    template_file.write_bytes(b"tmpl")
    monkeypatch.setattr(
        "ninegag_batch_uploader._load_registry",
        lambda: {
            "temp": {
                "path": str(tmp_path),
                "asset": str(template_file),
                "channels": [],
                "steps": [],
            }
        },
    )

    created = {}

    def fake_run(cmd, check=True, capture_output=True):
        created["path"] = Path(cmd[-1])
        created["path"].write_bytes(b"out")
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr("ninegag_batch_uploader.subprocess.run", fake_run)

    out = apply_template(video_file, "temp")
    assert out == video_file.with_name("vid_temp.mp4")
    assert created["path"] == out
    assert out.exists()


def test_upload_to_channel_uses_config(tmp_path, monkeypatch):
    import yaml

    monkeypatch.chdir(tmp_path)
    channels = {
        "MyChannel": {"profile": "profile_dir", "upload_url": "http://example.com"}
    }
    with open("channels.yml", "w", encoding="utf-8") as f:
        yaml.safe_dump(channels, f)

    events = []

    class DummyDriver:
        def __init__(self, options=None):
            events.append("init")

        def get(self, url):
            events.append(url)

        def quit(self):
            events.append("quit")

    class DummyOptions:
        def __init__(self):
            self.args = []

        def add_argument(self, arg):
            self.args.append(arg)

    monkeypatch.setattr("ninegag_batch_uploader.webdriver.Chrome", DummyDriver)
    monkeypatch.setattr("ninegag_batch_uploader.Options", DummyOptions)

    paths = [tmp_path / "a.mp4", tmp_path / "b.mp4"]
    for p in paths:
        p.write_text("x")

    upload_to_channel(paths, "MyChannel")

    assert events[0] == "init"
    assert events[-1] == "quit"
    assert events.count("http://example.com") == len(paths)
