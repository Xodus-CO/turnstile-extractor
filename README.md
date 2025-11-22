# Cloudflare Turnstile Extractor

Simple Python script that opens a page protected by Cloudflare Turnstile, waits for the widget to initialize, hooks turnstile.render and grabs everything you normally can't see from a normal request:

- sitekey  
- cData  
- action  
- chlPageData   

Everything gets dumped into cf_extracted.json in the current folder

### Why this exists

A lot of sites switched from hCaptcha/recaptcha to Turnstile
If you ever need to solve it manually (2captcha, capmonster, etc.) or build your own solver, you first need those four parameters, this script just pulls them out cleanly, nothing more

### How to run

```bash
pip install playwright playwright-stealth
playwright install chromium

python3 main.py https://example-protected-site.com
```
##Output
Creates cf_extracted.json with the extracted turnstile parameters

ex:

```bash
started on target → https://target.etc

sitekey      → xxxxxxx
cData        → xxxxxxx
action       → interactive
chlPageData  → xxxxxxxx-1763818211-1.3.1.1-gIKH.pU7vpxRLWj8.JmIgNZuQk3...
```

## ⚠️ Disclaimer

This script is for educational and research purposes only, I do not encourage or support any illegal activities, bypassing security measures without authorization, or violating terms of service
Use this tool responsibly and only on websites where you have explicit permission to test.

**You are solely responsible for how you use this tool.** The authors are not liable for any misuse or damage caused by this software
