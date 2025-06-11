from click.testing import CliRunner
from pathlib import Path

from src.cli import main


def test_template_register_invokes_register(monkeypatch, tmp_path):
    called = {}

    def fake_register(p):
        called['path'] = p

    monkeypatch.setattr('ninegag_batch_uploader.register_template', fake_register)

    runner = CliRunner()
    template_dir = tmp_path / 'tpl'
    template_dir.mkdir()
    result = runner.invoke(main, ['template', 'register', str(template_dir)])

    assert result.exit_code == 0
    assert called['path'] == Path(template_dir)
    assert 'Registered template' in result.output
