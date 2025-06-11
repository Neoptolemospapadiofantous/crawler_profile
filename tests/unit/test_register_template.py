import json
from pathlib import Path

import pytest

from ninegag_batch_uploader import register_template, REGISTRY_PATH


@pytest.mark.usefixtures("tmp_path")
def test_register_template_reads_manifest(tmp_path, monkeypatch):
    registry_file = tmp_path / "registry.json"
    monkeypatch.setattr("ninegag_batch_uploader.REGISTRY_PATH", registry_file)

    register_template(Path("templates/FunnyIntro"))

    assert registry_file.exists()
    with registry_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    assert "FunnyIntro" in data
    assert data["FunnyIntro"]["channels"] == ["ChannelA"]
    assert data["FunnyIntro"]["steps"] == []
