import pytest
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - PyYAML not installed
    yaml = None


@pytest.mark.skipif(yaml is None, reason="PyYAML not installed")
def test_logging_yaml_loads():
    path = Path('config/logging.yaml')
    with path.open('r') as f:
        config = yaml.safe_load(f)
    assert isinstance(config, dict)
    assert 'root' in config

