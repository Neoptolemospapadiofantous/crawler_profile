import sys
import types
import importlib.util
from pathlib import Path

import pytest

package_name = 'ninegag'
if package_name not in sys.modules:
    pkg = types.ModuleType(package_name)
    pkg.__path__ = []
    sys.modules[package_name] = pkg

# Create dummy 'requests' module to satisfy import in processor
if 'requests' not in sys.modules:
    sys.modules['requests'] = types.ModuleType('requests')

spec = importlib.util.spec_from_file_location(
    'ninegag.processor',
    Path(__file__).resolve().parents[2] / 'src/ninegag/processor.py'
)
processor = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = processor
spec.loader.exec_module(processor)
VideoProcessor = processor.VideoProcessor


@pytest.mark.parametrize(
    'text,expected',
    [
        ('simple', 'simple'),
        ("O'Reilly", "O\\'Reilly"),
        (
            'a [text], with: special (chars) #1\nNew line\rTest',
            'a \\[text\\]\, with\\: special \\(chars\\) \\#1 New line Test',
        ),
    ],
)
def test_escape_text(text: str, expected: str) -> None:
    vp = VideoProcessor()
    assert vp._escape_text(text) == expected
