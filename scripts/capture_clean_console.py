import os
import asyncio
from playwright.async_api import async_playwright

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/home/hr10j44t/Downloads/RescueAI/.cache/ms-playwright"

ARTIFACT_DIR = "/home/hr10j44t/.gemini/antigravity/brain/92e66071-db58-4e3d-b155-e231ef34d3b2/live_map_verification"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 1200})
        page = await context.new_page()

        print("Navigating to http://localhost:8501 ...")
        await page.goto("http://localhost:8501", wait_until="networkidle", timeout=35000)
        await page.wait_for_timeout(5000)
        os.makedirs(ARTIFACT_DIR, exist_ok=True)

        # 1. Full view showing unified map and message log dataframe
        p1 = os.path.join(ARTIFACT_DIR, "1_unified_single_real_world_map_full.png")
        await page.screenshot(path=p1)
        print("Captured 1_unified_single_real_world_map_full.png")

        # 2. Switch to Recent Disaster News Wire tab
        wire_tab = page.locator("text=Recent Disaster News Wire (Live Feeds)").first
        if await wire_tab.is_visible():
            await wire_tab.click()
            await page.wait_for_timeout(2500)
            p2 = os.path.join(ARTIFACT_DIR, "3_recent_news_wire_tab_full.png")
            await page.screenshot(path=p2)
            print("Captured 3_recent_news_wire_tab_full.png")

        await browser.close()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(main())
