#!/usr/bin/env python3
import sys
import asyncio
import json
import re
from playwright.async_api import async_playwright
from playwright_stealth import Stealth


async def main():
    if len(sys.argv) != 2:
        sys.exit(1)
    url = sys.argv[1]

    print(
        r"""
 ██████╗███████╗██████╗  █████╗ ████████╗ █████╗
██╔════╝██╔════╝██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗
██║     █████╗  ██║  ██║███████║   ██║   ███████║
██║     ██╔══╝  ██║  ██║██╔══██║   ██║   ██╔══██║
╚██████╗██║     ██████╔╝██║  ██║   ██║   ██║  ██║
 ╚═════╝╚═╝     ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝
    """
    )

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()
        # Note: Using Stealth class with apply_stealth_async() method for newer playwright-stealth versions
        # Older versions used stealth_async() function directly
        stealth = Stealth()
        await stealth.apply_stealth_async(page)

        # Track site key from network requests
        site_key_from_network = None

        async def handle_response(response):
            nonlocal site_key_from_network
            url = response.url
            # Look for site key in Turnstile URLs (0x...)
            if "turnstile" in url.lower() and "0x" in url:
                match = re.search(r"/(0x[A-Za-z0-9_-]{20,})/", url)
                if match and not site_key_from_network:
                    site_key_from_network = match.group(1)
                    print(f"Found site key in network request: {site_key_from_network}")

        page.on("response", handle_response)

        await page.add_init_script(
            """
            window.cf = {};
            const i = setInterval(() => {
                if (window.turnstile && !window.cf_captured) {
                    clearInterval(i);
                    const orig = window.turnstile.render;
                    window.turnstile.render = (a, b) => {
                        window.cf = {
                            sitekey: b.sitekey || '',
                            cData: b.cData || '',
                            action: b.action || '',
                            chlPageData: b.chlPageData || ''
                        };
                        window.cf_captured = true;
                        return orig.call(this, a, b);
                    };
                }
            }, 100);
        """
        )

        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(30)  # Wait longer for Turnstile to initialize

        # Check if hook was triggered
        hook_triggered = await page.evaluate("() => window.cf_captured || false")
        print(f"Hook triggered: {hook_triggered}")

        # Check if turnstile exists
        turnstile_exists = await page.evaluate("() => typeof turnstile !== 'undefined'")
        print(f"Turnstile object exists: {turnstile_exists}")

        widget_data = {}
        if turnstile_exists:
            widget_count = await page.evaluate(
                "() => turnstile._widgets ? turnstile._widgets.length : 0"
            )
            print(f"Widget count: {widget_count}")

            # Try to extract site key from widget state or config
            widget_data = await page.evaluate(
                """
                () => {
                    var result = {};
                    if (turnstile._widgets && turnstile._widgets.length > 0) {
                        var widget = turnstile._widgets[0];
                        result.sitekey = widget.sitekey || widget._sitekey || '';
                        result.cData = widget.cData || '';
                        result.action = widget.action || '';
                        result.chlPageData = widget.chlPageData || '';
                    }
                    // Also check _config
                    if (turnstile._config) {
                        if (!result.sitekey && turnstile._config.sitekey) {
                            result.sitekey = turnstile._config.sitekey;
                        }
                    }
                    return result;
                }
            """
            )
            print(f"Widget data: {widget_data}")

        data = await page.evaluate("() => window.cf || {}")

        # Merge widget data if found
        if widget_data.get("sitekey"):
            data.update(widget_data)

        # Use site key from network request if found (prioritize network extraction as most reliable)
        if site_key_from_network and not data.get("sitekey"):
            data["sitekey"] = site_key_from_network
            print(f"Using site key from network request: {data['sitekey']}")

        # If still no site key, try to extract from page source
        if not data.get("sitekey"):
            # First check for data-sitekey attribute (cheaper than fetching full page content)
            data_sitekey = await page.evaluate(
                """
                () => {
                    var elem = document.querySelector('[data-sitekey]');
                    return elem ? elem.getAttribute('data-sitekey') : null;
                }
            """
            )
            if data_sitekey and re.match(r"^0x[A-Za-z0-9_-]{20,}$", data_sitekey):
                data["sitekey"] = data_sitekey
                print(f"Found site key in data-sitekey: {data['sitekey'][:30]}...")
            else:
                # Only fetch page source if attribute check failed
                page_source = await page.content()
                # Look for Turnstile site key (0x...) - standardized to {20,} for consistency
                sitekey_match = re.search(
                    r'sitekey["\']?\s*[:=]\s*["\'](0x[A-Za-z0-9_-]{20,})["\']',
                    page_source,
                    re.IGNORECASE,
                )
                if sitekey_match:
                    data["sitekey"] = sitekey_match.group(1)
                    print(f"Found site key in page source: {data['sitekey'][:30]}...")
        cookies = await context.cookies()
        cf_cookies = {
            c["name"]: c["value"]
            for c in cookies
            if any(x in c["name"] for x in ["cf", "__cf", "clearance"])
        }

        result = {
            "url": url,
            "sitekey": data.get("sitekey", ""),
            "cData": data.get("cData", ""),
            "action": data.get("action", ""),
            "chlPageData": data.get("chlPageData", ""),
            "cookies": cf_cookies,
        }

        with open("cf_extracted.json", "w") as f:
            json.dump(result, f, indent=2)

        print("all extracted → cf_extracted.json")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
