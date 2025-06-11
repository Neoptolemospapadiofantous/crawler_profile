import sys
import types
import importlib.util
from pathlib import Path

import pytest

# Insert dummy parent package 'ninegag'
package_name = 'ninegag'
if package_name not in sys.modules:
    pkg = types.ModuleType(package_name)
    pkg.__path__ = []  # mark as package
    sys.modules[package_name] = pkg

modules_with_attrs = {
    "selenium": {},
    "selenium.webdriver": {},
    "selenium.webdriver.common": {},
    "selenium.webdriver.common.by": {"By": object()},
    "selenium.webdriver.support": {},
    "selenium.webdriver.support.ui": {"WebDriverWait": object()},
    "selenium.webdriver.support.expected_conditions": {"EC": object()},
    "selenium.webdriver.chrome": {},
    "selenium.webdriver.chrome.options": {"Options": object()},
    "selenium.webdriver.chrome.service": {"Service": object()},
    "selenium.common": {},
    "selenium.common.exceptions": {"TimeoutException": Exception},
    "webdriver_manager": {},
    "webdriver_manager.chrome": {"ChromeDriverManager": object()},
}
for name, attrs in modules_with_attrs.items():
    module = types.ModuleType(name)
    for attr_name, value in attrs.items():
        setattr(module, attr_name, value)
    sys.modules.setdefault(name, module)

spec = importlib.util.spec_from_file_location(
    "ninegag.crawler", Path(__file__).resolve().parents[2] / "src/ninegag/crawler.py"
)
crawler_mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = crawler_mod
spec.loader.exec_module(crawler_mod)
NineGagCrawler = crawler_mod.NineGagCrawler


def test_parse_number_basic():
    crawler = NineGagCrawler.__new__(NineGagCrawler)
    assert crawler._parse_number("123") == 123
    assert crawler._parse_number("45K") == 45000
    assert crawler._parse_number("2.5M") == 2500000
    assert crawler._parse_number("0") == 0
    assert crawler._parse_number("invalid") == 0
