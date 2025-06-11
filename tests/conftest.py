import sys
import types
import json
from pathlib import Path

# Ensure src/ is on sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

# Minimal 'requests' stub
if "requests" not in sys.modules:
    requests = types.ModuleType("requests")

    def dummy_get(*args, **kwargs):
        raise RuntimeError("requests.get should be patched in tests")

    requests.get = dummy_get
    sys.modules["requests"] = requests

# Minimal 'pydantic' and 'pydantic_settings' stubs
if "pydantic" not in sys.modules:
    pydantic = types.ModuleType("pydantic")

    def Field(default=None, **kwargs):
        return default

    def field_validator(*args, **kwargs):
        def decorator(fn):
            return fn
        return decorator

    pydantic.Field = Field
    pydantic.field_validator = field_validator
    sys.modules["pydantic"] = pydantic

if "pydantic_settings" not in sys.modules:
    ps = types.ModuleType("pydantic_settings")

    class BaseSettings:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    SettingsConfigDict = dict

    ps.BaseSettings = BaseSettings
    ps.SettingsConfigDict = SettingsConfigDict
    sys.modules["pydantic_settings"] = ps

# Minimal 'structlog' stub
if "structlog" not in sys.modules:
    structlog = types.ModuleType("structlog")

    class DummyLogger:
        def __getattr__(self, name):
            def _(*args, **kwargs):
                return None
            return _

    class LoggerFactory:
        def __call__(self, *args, **kwargs):
            return DummyLogger()

    structlog.stdlib = types.ModuleType("structlog.stdlib")
    structlog.stdlib.filter_by_level = lambda *a, **k: None
    structlog.stdlib.add_logger_name = lambda *a, **k: None
    structlog.stdlib.add_log_level = lambda *a, **k: None
    structlog.stdlib.PositionalArgumentsFormatter = lambda: None
    structlog.stdlib.LoggerFactory = LoggerFactory

    structlog.processors = types.ModuleType("structlog.processors")
    structlog.processors.TimeStamper = lambda fmt=None: (lambda *a, **k: None)
    structlog.processors.StackInfoRenderer = lambda *a, **k: None
    structlog.processors.format_exc_info = lambda *a, **k: None
    structlog.processors.JSONRenderer = lambda: (lambda *a, **k: None)

    structlog.dev = types.ModuleType("structlog.dev")
    structlog.dev.ConsoleRenderer = lambda: (lambda *a, **k: None)

    structlog.configure = lambda *a, **k: None
    structlog.get_logger = lambda name=None: DummyLogger()

    sys.modules["structlog"] = structlog
    sys.modules["structlog.stdlib"] = structlog.stdlib
    sys.modules["structlog.processors"] = structlog.processors
    sys.modules["structlog.dev"] = structlog.dev

# Minimal 'yaml' stub using JSON for simplicity
if "yaml" not in sys.modules:
    yaml = types.ModuleType("yaml")

    def safe_load(stream):
        try:
            return json.load(stream)
        except Exception:
            return {"root": {}}

    def safe_dump(data, stream):
        json.dump(data, stream)

    yaml.safe_load = safe_load
    yaml.safe_dump = safe_dump
    sys.modules["yaml"] = yaml

# Minimal 'selenium' stub
if "selenium" not in sys.modules:
    selenium = types.ModuleType("selenium")
    webdriver = types.ModuleType("selenium.webdriver")

    class DummyDriver:
        def __init__(self, *args, **kwargs):
            pass

        def get(self, url):
            pass

        def quit(self):
            pass

    webdriver.Chrome = DummyDriver
    selenium.webdriver = webdriver
    sys.modules["selenium"] = selenium
    sys.modules["selenium.webdriver"] = webdriver
    sys.modules["selenium.webdriver.chrome"] = types.ModuleType(
        "selenium.webdriver.chrome"
    )
    chrome_options = types.ModuleType("selenium.webdriver.chrome.options")

    class Options:
        def __init__(self):
            self.args = []

        def add_argument(self, arg):
            self.args.append(arg)

    chrome_options.Options = Options
    sys.modules["selenium.webdriver.chrome.options"] = chrome_options
    # Common submodules used in crawler
    common = types.ModuleType("selenium.webdriver.common")
    by_mod = types.ModuleType("selenium.webdriver.common.by")

    class By:
        ID = "id"

    by_mod.By = By
    common.by = by_mod
    sys.modules["selenium.webdriver.common"] = common
    sys.modules["selenium.webdriver.common.by"] = by_mod
    support = types.ModuleType("selenium.webdriver.support")
    support.ui = types.ModuleType("selenium.webdriver.support.ui")
    support.expected_conditions = types.ModuleType(
        "selenium.webdriver.support.expected_conditions"
    )
    sys.modules["selenium.webdriver.support"] = support
    sys.modules["selenium.webdriver.support.ui"] = support.ui
    sys.modules["selenium.webdriver.support.expected_conditions"] = (
        support.expected_conditions
    )

# Stub ninegag.crawler to avoid selenium dependency
if "ninegag.crawler" not in sys.modules:
    crawler_mod = types.ModuleType("ninegag.crawler")
    from dataclasses import dataclass
    from pathlib import Path
    from typing import List, Dict, Optional
    from datetime import datetime

    @dataclass
    class VideoData:
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

    class NineGagCrawler:
        def __init__(self, headless: bool = True) -> None:
            pass

        def crawl_category(
            self, category: str, scroll_times: int = 3
        ) -> List[VideoData]:
            return []

        def close(self) -> None:
            pass

    crawler_mod.VideoData = VideoData
    crawler_mod.NineGagCrawler = NineGagCrawler
    sys.modules["ninegag.crawler"] = crawler_mod
