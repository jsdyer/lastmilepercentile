"""Exercise the built starter at a project subpath in Chromium."""
import os
import json
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
                # Browser checks use only local data. A speed test is always replaced with a fixture.
                page.route("https://**/*", lambda route: route.abort())
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
                status = json.loads((ROOT / "dist/data/status.json").read_text())
                month = status["end"]
                for slug, asn in [("vancouver-telus", "852"), ("vancouver-novus", "40029")]:
                    page.goto(f"http://127.0.0.1:{server.server_port}/example-tool/{slug}/")
                    assert page.locator('link[rel=canonical]').get_attribute('href') == f'https://coolcode.ca/lastmilepercentile/{slug}/'
                    assert page.locator('.intro .cohort-facts li').count() == 2
                    assert page.locator('.intro time').get_attribute('datetime') == month
                    assert page.locator('.intro a[href="/field-notes/vancouver-home-internet/"]').count() == 1
                    assert page.locator('script[src="/assets/tool-metrics.js"]').count() == 1
                    for direction in ("download", "upload"):
                        page.locator('#direction').select_option(direction)
                        data = json.loads((ROOT / f"dist/data/{month}-{direction}.json").read_text())
                        row = next((r for r in data if r[0] == "BC" and r[1] == "Vancouver" and str(r[2]) == asn), None)
                        page.wait_for_function("asn => document.querySelector('#asn').value === asn && !document.querySelector('#city').disabled", arg=asn)
                        assert page.locator("#city").input_value() == "Vancouver"
                        if row:
                            sample = f"{row[4]:,} {direction} tests"
                            page.wait_for_function("sample => document.querySelector('#result-text').textContent.includes(sample)", arg=sample)
                            assert sample in page.locator('.cohort-facts').inner_text()
                        else:
                            assert "No qualifying" in page.locator('#status').inner_text()
                        source = next(x for x in status['months'] if x['month'] == month)['sources'][direction]['url']
                        assert page.locator('#source-file').get_attribute('href') == source
                        assert page.locator('.cohort-facts').get_by_role('link', name=f'M-Lab {direction} data (Parquet)').get_attribute('href') == source
                assert not errors,errors
                browser.close()
            print("Browser checks passed for cohort selection, bands, upload, month and mobile layout")
        finally:
            server.shutdown()


if __name__ == "__main__":
    main()
