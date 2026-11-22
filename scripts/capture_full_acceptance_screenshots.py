import os
import asyncio
from playwright.async_api import async_playwright

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/home/hr10j44t/Downloads/RescueAI/.cache/ms-playwright"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Viewport: 1440x900 as required by the brief
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()
        
        print("Navigating to http://localhost:8501 ...")
        await page.goto("http://localhost:8501", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
        
        os.makedirs("reports/console_acceptance", exist_ok=True)
        
        # 1. Capture clean 1440x900 view with user pins and dark map
        await page.screenshot(path="reports/console_acceptance/1_console_main_view.png")
        print("Captured 1_console_main_view.png")
        
        # 2. Toggle "Offline map"
        offline_cb = page.locator("text=Offline map").first
        if await offline_cb.is_visible():
            await offline_cb.click()
            await page.wait_for_timeout(2000)
            await page.screenshot(path="reports/console_acceptance/2_offline_map_mode.png")
            print("Captured 2_offline_map_mode.png")
            # Toggle back to online map
            await offline_cb.click()
            await page.wait_for_timeout(1500)
            
        # 3. Select an event from "Pick event" and classify a test message
        textarea = page.locator("textarea").first
        await textarea.fill("URGENT: Flood waters breaching levee, rescue boats needed immediately")
        
        pick_event_radio = page.locator("text=Pick event").first
        await pick_event_radio.click()
        await page.wait_for_timeout(400)
        
        classify_btn = page.locator("button:has-text('Classify')").first
        await classify_btn.click()
        await page.wait_for_timeout(3000)
        
        # 4. Capture open modal dialog
        await page.screenshot(path="reports/console_acceptance/3_modal_dialog_detail.png")
        print("Captured 3_modal_dialog_detail.png")
        
        # Click "Flag" button in dialog to test status action
        flag_btn = page.locator("button:has-text('Flag')").first
        if await flag_btn.is_visible():
            await flag_btn.click()
            await page.wait_for_timeout(1500)
            print("Clicked Flag status action")
            
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(1500)
        
        # 5. Capture console after flagged message added
        await page.screenshot(path="reports/console_acceptance/4_console_after_flagged.png")
        print("Captured 4_console_after_flagged.png")

        await browser.close()
        print("Done capturing acceptance screenshots.")

if __name__ == "__main__":
    asyncio.run(main())
