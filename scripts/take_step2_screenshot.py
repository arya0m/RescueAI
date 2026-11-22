import os
import asyncio
from playwright.async_api import async_playwright

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/home/hr10j44t/Downloads/RescueAI/.cache/ms-playwright"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()
        
        # Navigate to Streamlit
        await page.goto("http://localhost:8501", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
        
        # Capture full page screenshot of the shell
        os.makedirs("reports/audit_screenshots", exist_ok=True)
        await page.screenshot(path="reports/audit_screenshots/step2_shell.png", full_page=True)
        print("Captured step2_shell.png successfully")
        
        # Also let's click on Classify Message in sidebar to verify navigation
        classify_link = page.locator("text=Classify Message").first
        if await classify_link.is_visible():
            await classify_link.click()
            await page.wait_for_timeout(2000)
            await page.screenshot(path="reports/audit_screenshots/step2_classify_shell.png", full_page=True)
            print("Captured step2_classify_shell.png successfully")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
