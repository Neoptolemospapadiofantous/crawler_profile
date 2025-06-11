import sys
import types

sys.modules.setdefault("openai", types.ModuleType("openai"))

from ninegag.processor import VideoProcessor
from ninegag.crawler import VideoData


class DummyResp:
    def raise_for_status(self):
        pass

    def iter_content(self, chunk_size=8192):
        yield b"data"


def test_download_video_passes_timeout(tmp_path, monkeypatch):
    recorded = {}

    def fake_get(url, stream=True, timeout=None):
        recorded["timeout"] = timeout
        return DummyResp()

    monkeypatch.setattr("ninegag.processor.requests.get", fake_get)

    video = VideoData(
        post_id="abc",
        title="t",
        video_url="http://example.com/video.mp4",
        mobile_url="http://example.com/video.mp4",
        thumbnail_url="",
        author="a",
        tags=[],
        stats={},
        category="test",
    )

    proc = VideoProcessor(request_timeout=12)
    proc.output_dir = tmp_path
    path = proc.download_video(video)

    assert recorded["timeout"] == 12
    assert path is not None and path.exists()
