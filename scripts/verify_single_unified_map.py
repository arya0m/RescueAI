import os
import shutil
import asyncio
from playwright.async_api import async_playwright

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/home/hr10j44t/Downloads/RescueAI/.cache/ms-playwright"

ARTIFACT_DIR = "/home/hr10j44t/.gemini/antigravity/brain/92e66071-db58-4e3d-b155-e231ef34d3b2/live_map_verification"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 950})
        page = await context.new_page()

        print("Navigating to http://localhost:8501 ...")
        await page.goto("http://localhost:8501", wait_until="networkidle", timeout=35000)
        await page.wait_for_timeout(5000)
        os.makedirs("reports/live_verification", exist_ok=True)
        os.makedirs(ARTIFACT_DIR, exist_ok=True)

        # 1. Capture the single unified photorealistic real-world operational map
        p1 = "reports/live_verification/1_unified_single_real_world_map.png"
        await page.screenshot(path=p1)
        shutil.copy(p1, os.path.join(ARTIFACT_DIR, "1_unified_single_real_world_map.png"))
        print("Captured 1_unified_single_real_world_map.png")

        # 2. Test 1-Click Operational Scenario Preset ("Casualty Trap (Harvey)")
        chip = page.locator("button:has-text('Casualty Trap (Harvey)')").first
        if await chip.is_visible():
            await chip.click()
            await page.wait_for_timeout(1000)
            classify_btn = page.locator("button:has-text('Classify')").first
            if await classify_btn.is_visible():
                await classify_btn.click()
                await page.wait_for_timeout(3000)
                p2 = "reports/live_verification/2_classified_dialog_modal.png"
                await page.screenshot(path=p2)
                shutil.copy(p2, os.path.join(ARTIFACT_DIR, "2_classified_dialog_modal.png"))
                print("Captured 2_classified_dialog_modal.png")
                
                # Close dialog
                close_btn = page.locator("button:has-text('Close')").first
                if await close_btn.is_visible():
                    await close_btn.click()
                    await page.wait_for_timeout(1500)

        # 3. Switch to Recent Disaster News Wire tab
        wire_tab = page.locator("[data-baseweb='tab']:has-text('Recent Disaster News Wire')").first
        if await wire_tab.is_visible():
            await wire_tab.click()
            await page.wait_for_timeout(2500)
            p3 = "reports/live_verification/3_recent_news_wire_tab.png"
            await page.screenshot(path=p3)
            shutil.copy(p3, os.path.join(ARTIFACT_DIR, "3_recent_news_wire_tab.png"))
            print("Captured 3_recent_news_wire_tab.png")

        # 4. Capture final clean console view
        p4 = "reports/live_verification/4_final_unified_console.png"
        await page.screenshot(path=p4)
        shutil.copy(p4, os.path.join(ARTIFACT_DIR, "4_final_unified_console.png"))
        print("Captured 4_final_unified_console.png")

        await browser.close()
        print("Single unified map verification completed.")

if __name__ == "__main__":
    asyncio.run(main())
