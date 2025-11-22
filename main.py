#!/usr/bin/env python3
import sys
import asyncio
import json
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

async def main():
    if len(sys.argv) != 2:
        sys.exit(1)
    url = sys.argv[1]

    print(r"""
 ██████╗███████╗██████╗  █████╗ ████████╗ █████╗ 
██╔════╝██╔════╝██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗
██║     █████╗  ██║  ██║███████║   ██║   ███████║
██║     ██╔══╝  ██║  ██║██╔══██║   ██║   ██╔══██║
╚██████╗██║     ██████╔╝██║  ██║   ██║   ██║  ██║
 ╚═════╝╚═╝     ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝
    """)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()
        await stealth_async(page)

        await page.add_init_script("""
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
        """)

        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(18)

        data = await page.evaluate("() => window.cf || {}")
        cookies = await context.cookies()
        cf_cookies = {c["name"]: c["value"] for c in cookies 
                     if any(x in c["name"] for x in ["cf", "__cf", "clearance"])}

        result = {
            "url": url,
            "sitekey": data.get("sitekey", ""),
            "cData": data.get("cData", ""),
            "action": data.get("action", ""),
            "chlPageData": data.get("chlPageData", ""),
            "cookies": cf_cookies
        }

        with open("cf_extracted.json", "w") as f:
            json.dump(result, f, indent=2)

        print("all extracted → cf_extracted.json")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
