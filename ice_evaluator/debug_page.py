import asyncio
from playwright.async_api import async_playwright

async def debug():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        await page.goto("http://127.0.0.1:5000")
        await page.wait_for_timeout(2000)
        
        # Poora page content dekho
        content = await page.content()
        
        # Sirf body text
        body_text = await page.evaluate("() => document.body.innerText")
        
        print("=" * 50)
        print("PAGE TITLE:", await page.title())
        print("=" * 50)
        print("BODY TEXT:")
        print(body_text)
        print("=" * 50)
        print("URL:", page.url)
        print("=" * 50)
        
        # Check for key elements
        has_form = await page.query_selector('form')
        has_input = await page.query_selector('input[name="username"]')
        has_denied = "Access Denied" in content
        
        print(f"Has Form: {has_form is not None}")
        print(f"Has Username Input: {has_input is not None}")
        print(f"'Access Denied' in page: {has_denied}")
        
        await page.screenshot(path="debug_screenshot.png")
        print("\n📸 Screenshot saved: debug_screenshot.png")
        
        await browser.close()

asyncio.run(debug())