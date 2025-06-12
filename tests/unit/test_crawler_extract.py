import re
import sys
import types
import importlib.util
from pathlib import Path


def load_crawler_module():
    """Load the real crawler module with stubbed selenium deps."""
    # Stub selenium modules
    selenium = types.ModuleType("selenium")
    webdriver = types.ModuleType("selenium.webdriver")
    class DummyChrome:
        def __init__(self, *a, **k):
            self.service = k.get("service")
        def execute_script(self, script):
            pass
    webdriver.Chrome = DummyChrome

    chrome_options = types.ModuleType("selenium.webdriver.chrome.options")
    class Options:
        def __init__(self):
            pass
        def add_argument(self, arg):
            pass
        def add_experimental_option(self, name, value):
            pass
    chrome_options.Options = Options

    chrome_service = types.ModuleType("selenium.webdriver.chrome.service")
    class Service:
        def __init__(self, path):
            self.path = path
    chrome_service.Service = Service

    common = types.ModuleType("selenium.webdriver.common")
    by_mod = types.ModuleType("selenium.webdriver.common.by")
    class By:
        CSS_SELECTOR = "css"
        TAG_NAME = "tag"
        ID = "id"
    by_mod.By = By
    common.by = by_mod

    support = types.ModuleType("selenium.webdriver.support")
    ui = types.ModuleType("selenium.webdriver.support.ui")
    class DummyWait:
        def __init__(self, driver, timeout):
            self.driver = driver
        def until(self, method):
            return method(self.driver)
    ui.WebDriverWait = DummyWait
    ec = types.ModuleType("selenium.webdriver.support.expected_conditions")
    ec.presence_of_element_located = lambda locator: (lambda driver: True)
    support.ui = ui
    support.expected_conditions = ec

    exceptions = types.ModuleType("selenium.common.exceptions")
    class TimeoutException(Exception):
        pass
    exceptions.TimeoutException = TimeoutException

    modules = {
        "selenium": selenium,
        "selenium.webdriver": webdriver,
        "selenium.webdriver.chrome.options": chrome_options,
        "selenium.webdriver.chrome.service": chrome_service,
        "selenium.webdriver.common": common,
        "selenium.webdriver.common.by": by_mod,
        "selenium.webdriver.support": support,
        "selenium.webdriver.support.ui": ui,
        "selenium.webdriver.support.expected_conditions": ec,
        "selenium.common.exceptions": exceptions,
    }
    for name, mod in modules.items():
        sys.modules[name] = mod

    # Stub webdriver_manager
    wm = types.ModuleType("webdriver_manager")
    chrome_wm = types.ModuleType("webdriver_manager.chrome")
    class ChromeDriverManager:
        def install(self):
            return "/tmp/chromedriver"
    chrome_wm.ChromeDriverManager = ChromeDriverManager
    wm.chrome = chrome_wm
    sys.modules["webdriver_manager"] = wm
    sys.modules["webdriver_manager.chrome"] = chrome_wm

    spec = importlib.util.spec_from_file_location(
        "crawler_mod",
        Path(__file__).resolve().parents[2] / "src" / "ninegag" / "crawler.py",
    )
    crawler_mod = importlib.util.module_from_spec(spec)
    sys.modules["crawler_mod"] = crawler_mod
    spec.loader.exec_module(crawler_mod)
    return crawler_mod


class DummyElement:
    def __init__(self, attrs):
        self.attrs = attrs
    def get_attribute(self, name):
        return self.attrs.get(name)


class DummyDriver:
    def __init__(self, html: str):
        self.html = html
    def find_elements(self, by, selector):
        results = []
        if selector == "article[data-entry-id]":
            for m in re.finditer(r'<article[^>]*data-entry-id="([^"]+)"', self.html):
                results.append(DummyElement({"data-entry-id": m.group(1)}))
        elif selector.startswith('article[id^="jsid-post-"]'):
            for m in re.finditer(r'<article[^>]*id="(jsid-post-[^"]+)"', self.html):
                results.append(DummyElement({"id": m.group(1)}))
        elif selector == "div[data-entry-id]":
            for m in re.finditer(r'<div[^>]*data-entry-id="([^"]+)"', self.html):
                results.append(DummyElement({"data-entry-id": m.group(1)}))
        elif selector == "div[data-post-id]":
            for m in re.finditer(r'<div[^>]*data-post-id="([^"]+)"', self.html):
                results.append(DummyElement({"data-post-id": m.group(1)}))
        elif selector == "div.post-container":
            pattern = r'<div[^>]*class="[^\"]*post-container[^\"]*"[^>]*data-entry-id="([^"]+)"'
            for m in re.finditer(pattern, self.html):
                results.append(DummyElement({"data-entry-id": m.group(1)}))
        elif selector == "div[class*='post-item']":
            pattern = r'<div[^>]*class="[^\"]*post-item[^\"]*"[^>]*data-entry-id="([^"]+)"'
            for m in re.finditer(pattern, self.html):
                results.append(DummyElement({"data-entry-id": m.group(1)}))
        return results


def test_extract_all_videos_detects_posts(monkeypatch):
    crawler_mod = load_crawler_module()
    html = (
        '<article data-entry-id="a1"></article>'
        '<div data-entry-id="c3"></div>'
        '<article id="jsid-post-b2"></article>'
        '<div data-post-id="d4"></div>'
    )
    driver = DummyDriver(html)
    crawler = crawler_mod.NineGagCrawler.__new__(crawler_mod.NineGagCrawler)
    crawler.driver = driver

    def fake_extract(self, article, category):
        pid = (
            article.get_attribute("data-entry-id")
            or article.get_attribute("data-post-id")
            or article.get_attribute("id")
            or ""
        )
        pid = pid.replace("jsid-post-", "")
        return crawler_mod.VideoData(
            post_id=pid,
            title="",
            video_url="",
            mobile_url="",
            thumbnail_url="",
            author="",
            tags=[],
            stats={},
            category=category,
        )

    monkeypatch.setattr(crawler_mod.NineGagCrawler, "_extract_video_from_article", fake_extract)

    videos = crawler._extract_all_videos("hot")
    ids = [v.post_id for v in videos]
    assert set(ids) == {"a1", "b2", "c3", "d4"}


def test_init_uses_given_driver_path(monkeypatch):
    crawler_mod = load_crawler_module()
    recorded = {}

    def fake_chrome(*args, **kwargs):
        recorded["path"] = kwargs["service"].path
        class D:
            def execute_script(self, *a, **k):
                pass
        return D()

    monkeypatch.setattr(crawler_mod.webdriver, "Chrome", fake_chrome)
    monkeypatch.delenv("CHROMEDRIVER_PATH", raising=False)
    crawler_mod.NineGagCrawler(driver_path="/custom/path")
    assert recorded["path"] == "/custom/path"


def test_init_uses_env_var(monkeypatch):
    crawler_mod = load_crawler_module()
    recorded = {}
    called = {"count": 0}

    def fake_install(self):
        called["count"] += 1
        return "/tmp/unused"

    def fake_chrome(*args, **kwargs):
        recorded["path"] = kwargs["service"].path
        class D:
            def execute_script(self, *a, **k):
                pass
        return D()

    monkeypatch.setattr(crawler_mod.ChromeDriverManager, "install", fake_install)
    monkeypatch.setattr(crawler_mod.webdriver, "Chrome", fake_chrome)
    monkeypatch.setenv("CHROMEDRIVER_PATH", "/env/path")
    crawler_mod.NineGagCrawler()
    assert recorded["path"] == "/env/path"
    assert called["count"] == 0
