import re
import sys
import types
import importlib.util
from pathlib import Path
import pytest


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
    def __init__(self, attrs, html=""):
        self.attrs = attrs
        self.html = html

    def get_attribute(self, name):
        return self.attrs.get(name)

    def find_elements(self, by, selector):
        driver = DummyDriver(self.html)
        return driver.find_elements(by, selector)


class DummyDriver:
    def __init__(self, html: str):
        self.html = html
        self.scrolled = 0
    def find_elements(self, by, selector):
        results = []
        if selector == "#list-view-2 .stream-container":
            m = re.search(r'<div[^>]*id="list-view-2"[^>]*>(.*?)</div>', self.html, re.DOTALL)
            if m:
                inner = m.group(1)
                m2 = re.search(r'<div[^>]*class="[^\"]*stream-container[^\"]*"[^>]*>(.*?)</div>', inner, re.DOTALL)
                if m2:
                    results.append(DummyElement({}, m2.group(1)))
            return results
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
            pattern = (r'<div[^>]*class="[^\\"]*post-container[^\\"]*"[^>]*(data-entry-id|data-post-id)="([^\\"]+)"')
            for m in re.finditer(pattern, self.html):
                attr = m.group(1)
                results.append(DummyElement({attr: m.group(2)}))
        elif selector == "div[class*='post-item']":
            pattern = (r'<div[^>]*class="[^\\"]*post-item[^\\"]*"[^>]*(data-entry-id|data-post-id)="([^\\"]+)"')
            for m in re.finditer(pattern, self.html):
                attr = m.group(1)
                results.append(DummyElement({attr: m.group(2)}))
        return results

    def execute_script(self, script):
        self.scrolled += 1


def test_extract_all_videos_detects_posts(monkeypatch):
    crawler_mod = load_crawler_module()
    html = (
        '<div id="list-view-2"><div class="stream-container">'
        '<article data-entry-id="a1"></article>'
        '<div data-entry-id="c3"></div>'
        '<article id="jsid-post-b2"></article>'
        '<div data-post-id="d4"></div>'
        '<div class="post-container" data-entry-id="e5" data-post-id="e5"></div>'
        '<div class="item post-item" data-entry-id="f6" data-post-id="f6"></div>'
        '</div></div>'
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
    assert set(ids) == {"a1", "b2", "c3", "d4", "e5", "f6"}


def test_extract_all_videos_scrolls_when_container_missing(monkeypatch):
    crawler_mod = load_crawler_module()
    driver = DummyDriver("")
    crawler = crawler_mod.NineGagCrawler.__new__(crawler_mod.NineGagCrawler)
    crawler.driver = driver

    monkeypatch.setattr(crawler_mod.time, "sleep", lambda *a: None)

    log_msgs = []

    class Logger:
        def debug(self, msg, *args):
            log_msgs.append(msg % args if args else msg)
        def info(self, *a, **k):
            pass
        def warning(self, *a, **k):
            pass
        def error(self, *a, **k):
            pass

    monkeypatch.setattr(crawler_mod, "logger", Logger())

    videos = crawler._extract_all_videos("hot")
    assert videos == []
    assert driver.scrolled >= 3
    assert any("attempt" in m for m in log_msgs)


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


def test_init_with_directory_path(monkeypatch, tmp_path):
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

    dir_path = tmp_path / "driver"
    dir_path.mkdir()
    crawler_mod.NineGagCrawler(driver_path=str(dir_path))

    expected = str(dir_path / "chromedriver.exe")
    assert recorded["path"] == expected


def test_init_with_executable_path(monkeypatch, tmp_path):
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

    exe_name = "chromedriver.exe" if crawler_mod.os.name == "nt" else "chromedriver"
    exe_path = tmp_path / exe_name
    exe_path.write_text("")
    crawler_mod.NineGagCrawler(driver_path=str(exe_path))
    assert recorded["path"] == str(exe_path)


def test_env_var_directory(monkeypatch, tmp_path):
    crawler_mod = load_crawler_module()
    recorded = {}

    def fake_chrome(*args, **kwargs):
        recorded["path"] = kwargs["service"].path
        class D:
            def execute_script(self, *a, **k):
                pass
        return D()

    monkeypatch.setattr(crawler_mod.webdriver, "Chrome", fake_chrome)

    dir_path = tmp_path / "driver"
    dir_path.mkdir()
    monkeypatch.setenv("CHROMEDRIVER_PATH", str(dir_path))

    crawler_mod.NineGagCrawler()

    expected = str(dir_path / "chromedriver.exe")
    assert recorded["path"] == expected


def test_env_var_executable(monkeypatch, tmp_path):
    crawler_mod = load_crawler_module()
    recorded = {}

    def fake_chrome(*args, **kwargs):
        recorded["path"] = kwargs["service"].path
        class D:
            def execute_script(self, *a, **k):
                pass
        return D()

    monkeypatch.setattr(crawler_mod.webdriver, "Chrome", fake_chrome)

    exe_name = "chromedriver.exe" if crawler_mod.os.name == "nt" else "chromedriver"
    exe_path = tmp_path / exe_name
    exe_path.write_text("")
    monkeypatch.setenv("CHROMEDRIVER_PATH", str(exe_path))

    crawler_mod.NineGagCrawler()
    assert recorded["path"] == str(exe_path)


def test_init_logs_error_on_download_failure(monkeypatch):
    crawler_mod = load_crawler_module()
    logged = {}

    class Logger:
        def error(self, msg, *args):
            logged["msg"] = msg % args if args else msg

        def info(self, *a, **k):
            pass

        def debug(self, *a, **k):
            pass

        def warning(self, *a, **k):
            pass

    monkeypatch.setattr(crawler_mod, "logger", Logger())

    def fail_install(self):
        raise RuntimeError("boom")

    monkeypatch.setattr(crawler_mod.ChromeDriverManager, "install", fail_install)
    monkeypatch.delenv("CHROMEDRIVER_PATH", raising=False)

    with pytest.raises(RuntimeError):
        crawler_mod.NineGagCrawler()

    assert "CHROMEDRIVER_PATH" in logged.get("msg", "")
