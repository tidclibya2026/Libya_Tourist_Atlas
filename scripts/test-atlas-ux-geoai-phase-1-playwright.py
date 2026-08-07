import asyncio
import json
import socket
import subprocess
import sys
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]

def free_port():
    sock = socket.socket(); sock.bind(("127.0.0.1", 0)); port = sock.getsockname()[1]; sock.close(); return port

async def main():
    port = free_port()
    server = subprocess.Popen([sys.executable, "-m", "http.server", str(port)], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    errors = []
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(viewport={"width": 1280, "height": 820})
            page.on("console", lambda msg: errors.append(f"console:{msg.type}:{msg.text}") if msg.type == "error" else None)
            page.on("pageerror", lambda exc: errors.append(f"pageerror:{exc}"))
            await page.goto(f"http://127.0.0.1:{port}/index.html", wait_until="domcontentloaded")
            await page.wait_for_timeout(1000)
            async def check(name, ok): print(f"{name} = {'PASS' if ok else 'FAIL'}"); return ok
            results = []
            results.append(await check("ATLAS_LOAD", await page.locator("#map").count() == 1))
            results.append(await check("HEADER_VISIBLE", await page.locator(".topbar").is_visible()))
            results.append(await check("LOGO_VISIBLE", await page.locator(".brand-lockup").is_visible()))
            results.append(await check("TAGLINE_VISIBLE", await page.locator(".brand-strip").is_visible()))
            results.append(await check("MAP_VISIBLE", await page.locator("#map").is_visible()))
            results.append(await check("SMART_SEARCH_VISIBLE", await page.locator("#searchInput").is_visible()))
            results.append(await check("LAYER_EXPLORER_VISIBLE", await page.locator("#layerList").is_visible()))
            results.append(await check("GEOAI_BUTTON_VISIBLE", await page.locator("#geoaiButton").is_visible()))
            await page.locator("#geoaiButton").click(); await page.wait_for_timeout(100)
            results.append(await check("GEOAI_PANEL_OPENS", await page.locator("#geoaiPanel").get_attribute("open") is not None))
            for prompt, layer in [("اعرض الفنادق", "hotels"), ("اعرض مواقع التراث العالمي", "heritage"), ("استكشف أكاكوس", "akakus"), ("show investment", "investment")]:
                await page.locator("#geoaiInput").fill(prompt); await page.locator("#geoaiForm button").click(); await page.wait_for_timeout(550)
                results.append(await check(f"GEOAI_{layer.upper()}_INTENT", await page.locator(f"[data-id='{layer}']").is_checked()))
            for width, height in [(375,812),(390,844),(430,932)]:
                await page.set_viewport_size({"width": width, "height": height}); await page.wait_for_timeout(100)
                overflow = await page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1")
                results.append(await check(f"MOBILE_{width}_NO_HORIZONTAL_OVERFLOW", not overflow))
                results.append(await check(f"MOBILE_{width}_GEOAI_VISIBLE", await page.locator("#geoaiButton").is_visible()))
            await browser.close()
    finally:
        server.terminate(); server.wait(timeout=5)
    print("NO_CONSOLE_ERRORS =", "PASS" if not errors else "FAIL")
    if errors: print("ERRORS =", json.dumps(errors, ensure_ascii=False))
    failed = len(errors) + sum(1 for r in results if not r)
    print("NO_PAGE_ERRORS =", "PASS" if not errors else "FAIL")
    print("FAILED =", failed)
    if failed: raise SystemExit(1)

if __name__ == "__main__": asyncio.run(main())
