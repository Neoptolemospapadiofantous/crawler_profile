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
            VideoData(
                post_id="nopub",
                title="No Date",
                video_url="http://example.com/video3.mp4",
                mobile_url="http://example.com/video3.mp4",
                thumbnail_url="",
                author="tester",
                tags=[],
                stats={"upvotes": 1, "comments": 0},
                published=None,
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
    extra = tmp_path / "downloads" / "2023-01-01" / "nopub.mp4"
    skipped = tmp_path / "downloads" / "2023-01-01" / "xyz.mp4"
    assert len(results) == 2
    names = {r.downloaded_path.name for r in results}
    assert names == {"abc.mp4", "nopub.mp4"}
    assert expected.exists()
    assert extra.exists()
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
    import types

    monkeypatch.chdir(tmp_path)
    channels = {
        "MyChannel": {"profile": "profile_dir", "upload_url": "http://example.com"}
    }
    with open("channels.yml", "w", encoding="utf-8") as f:
        yaml.safe_dump(channels, f)

    actions = []

    class DummyElement:
        def __init__(self, name):
            self.name = name

        def send_keys(self, value):
            actions.append(("send_keys", value))

        def click(self):
            actions.append(("click", self.name))

        def clear(self):
            actions.append(("clear", self.name))

    class DummyDriver:
        def __init__(self, options=None):
            actions.append(("init", None))

        def get(self, url):
            actions.append(("get", url))

        def find_element(self, by, value):
            actions.append(("find", value))
            return DummyElement(value)

        def quit(self):
            actions.append(("quit", None))

    class DummyOptions:
        def __init__(self):
            self.args = []

        def add_argument(self, arg):
            self.args.append(arg)

    class FakeWait:
        def __init__(self, driver, timeout):
            self.driver = driver

        def until(self, condition):
            return condition(self.driver)

    FakeBy = types.SimpleNamespace(CSS_SELECTOR="css", NAME="name")
    FakeEC = types.SimpleNamespace(
        presence_of_element_located=lambda loc: lambda drv: drv.find_element(*loc),
        element_to_be_clickable=lambda loc: lambda drv: drv.find_element(*loc),
    )

    monkeypatch.setattr("ninegag_batch_uploader.webdriver.Chrome", DummyDriver)
    monkeypatch.setattr("ninegag_batch_uploader.Options", DummyOptions)
    monkeypatch.setattr("ninegag_batch_uploader.WebDriverWait", FakeWait)
    monkeypatch.setattr("ninegag_batch_uploader.By", FakeBy)
    monkeypatch.setattr("ninegag_batch_uploader.EC", FakeEC)

    paths = [tmp_path / "a.mp4", tmp_path / "b.mp4"]
    for p in paths:
        p.write_text("x")

    upload_to_channel(paths, "MyChannel")

    send_keys_actions = [a for a in actions if a[0] == "send_keys"]
    assert len(send_keys_actions) == len(paths)
    assert ("click", "tp-yt-paper-radio-button[name='UNLISTED']") in actions
    assert actions[0][0] == "init"
    assert actions[-1][0] == "quit"
