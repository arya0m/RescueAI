import os
import asyncio
from playwright.async_api import async_playwright

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/home/hr10j44t/Downloads/RescueAI/.cache/ms-playwright"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 1100})
        page = await context.new_page()
        
        await page.goto("http://localhost:8000/docs", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)
        
        os.makedirs("reports/api_docs", exist_ok=True)
        await page.screenshot(path="reports/api_docs/fastapi_docs.png", full_page=True)
        print("Captured reports/api_docs/fastapi_docs.png successfully")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
