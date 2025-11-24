# Cloudflare Turnstile Extractor

Simple Python script that opens a page protected by Cloudflare Turnstile, waits for the widget to initialize, and extracts everything you normally can't see from a normal request:

- sitekey  
- cData  
- action  
- chlPageData   

The script uses multiple extraction strategies with automatic fallbacks:
1. **Primary method**: Hooks `turnstile.render()` to capture parameters during widget initialization
2. **Widget state extraction**: Reads from `turnstile._widgets` and `turnstile._config` if available
3. **Network monitoring**: Captures site key from Turnstile API requests
4. **DOM attribute extraction**: Reads `data-sitekey` attribute from page elements
5. **Page source parsing**: Searches HTML source for site key patterns

Everything gets dumped into `cf_extracted.json` in the current folder

### Why this exists

A lot of sites switched from hCaptcha/recaptcha to Turnstile
If you ever need to solve it manually (2captcha, capmonster, etc.) or build your own solver, you first need those four parameters, this script just pulls them out cleanly, nothing more

### How to run

```bash
pip3 install playwright playwright-stealth
playwright install chromium

python3 main.py https://example-protected-site.com
```
## Output
Creates `cf_extracted.json` with the extracted turnstile parameters. The script provides debug output showing which extraction method succeeded:

```bash
Hook triggered: true
Turnstile object exists: true
Widget count: 1
Widget data: {'sitekey': '0x...', 'cData': '...', ...}
all extracted → cf_extracted.json
```

The output file contains:
```json
{
  "url": "https://example-protected-site.com",
  "sitekey": "0x...",
  "cData": "...",
  "action": "interactive",
  "chlPageData": "...",
  "cookies": {...}
}
```

## ⚠️ Disclaimer

This script is for educational and research purposes only, I do not encourage or support any illegal activities, bypassing security measures without authorization, or violating terms of service
Use this tool responsibly and only on websites where you have explicit permission to test.

**You are solely responsible for how you use this tool.** The authors are not liable for any misuse or damage caused by this software
