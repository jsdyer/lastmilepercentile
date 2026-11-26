"""Exercise the built starter at a project subpath in Chromium."""
import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import tempfile
import threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    screenshots = ROOT / "browser-checks"
    screenshots.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        shutil.copytree(ROOT / "dist", Path(temporary) / "example-tool")
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=temporary))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH'))
                page = browser.new_page(viewport={"width": 1280, "height": 1000})
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(f"http://127.0.0.1:{server.server_port}/example-tool/")
                page.locator("#band").wait_for()
                assert "tests on" in page.locator("#result-text").inner_text()
                latest=page.locator("#month").input_value()
                if latest == "2026-09":
                    assert page.locator("#band").inner_text() == "Between P25 and P50"
                    assert "6,331" in page.locator("#result-text").inner_text()
                    page.select_option("#region","NS")
                    page.select_option("#city","Halifax")
                    page.select_option("#asn","11260")
                    assert "4,898" in page.locator("#result-text").inner_text()
                    assert page.locator("#band").inner_text() == "Between P50 and P75"
                page.select_option("#direction","upload")
                page.wait_for_function("document.querySelector('#result-text').textContent.includes('upload tests')")
                page.fill("#speed","0")
                assert page.locator("#band").inner_text().startswith(("Below", "At"))
                assert page.locator("#chart .bar").count()==9
                page.select_option("#month",index=1)
                page.locator("#results").wait_for()
                page.screenshot(path=str(screenshots / "desktop.png"), full_page=True)
                page.set_viewport_size({"width": 390, "height": 844})
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                page.screenshot(path=str(screenshots / "mobile.png"), full_page=True)
                assert not errors, errors
                page.goto(f"http://127.0.0.1:{server.server_port}/example-tool/halifax-eastlink/")
                if latest == "2026-09":
                    page.wait_for_function("document.querySelector('#asn').value === '11260'")
                    assert "Halifax" in page.locator("#context").inner_text()
                page.evaluate("""() => { window.ndt7.test=async (cfg,handlers)=>{
                    if(!cfg.userAcceptedDataPolicy)throw Error('missing consent');
                    handlers.downloadComplete({LastClientMeasurement:{MeanClientMbps:125.2}});
                    handlers.uploadComplete({LastServerMeasurement:{TCPInfo:{ElapsedTime:2000,BytesReceived:15000}}});
                    return 0;
                }; }""")
                page.locator("#test-start").click()
                assert float(page.locator("#speed").input_value()) == 125.2
                page.locator("#direction").select_option("upload")
                assert float(page.locator("#speed").input_value()) == 60
                assert not errors,errors
                browser.close()
            print("Browser checks passed for cohort selection, bands, upload, month and mobile layout")
        finally:
            server.shutdown()


if __name__ == "__main__":
    main()
