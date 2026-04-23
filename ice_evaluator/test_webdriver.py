import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        page = await browser.new_page()
        
        # CDP session se override
        cdp = await page.context.new_cdp_session(page)
        await cdp.send("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false,
                });
            """
        })
        
        await page.goto("http://127.0.0.1:5000")
        await page.wait_for_timeout(2000)
        
        webdriver = await page.evaluate("() => navigator.webdriver")
        print(f"navigator.webdriver = {webdriver}")
        
        content = await page.content()
        if "Access Denied" in content:
            print("❌ Bot Detected!")
        else:
            print("✅ Bot Bypassed!")
        
        await browser.close()

asyncio.run(test())