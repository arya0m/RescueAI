import os
import asyncio
from playwright.async_api import async_playwright

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/home/hr10j44t/Downloads/RescueAI/.cache/ms-playwright"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Exactly 1440x900 viewport as required by the brief
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()
        
        print("Navigating to http://localhost:8501 ...")
        await page.goto("http://localhost:8501", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
        
        os.makedirs("reports/console_screenshots", exist_ok=True)
        
        # 1. Capture initial console view at 1440x900
        await page.screenshot(path="reports/console_screenshots/1_console_initial_1440x900.png")
        print("Captured 1_console_initial_1440x900.png")
        
        # 2. Type message: "people trapped on roof need boat rescue" with Pick event -> Hurricane Harvey
        textarea = page.locator("textarea").first
        await textarea.wait_for(timeout=15000)
        await textarea.fill("people trapped on roof need boat rescue, water level rising rapidly")
        
        # Click "Pick event" radio
        pick_event_radio = page.locator("text=Pick event").first
        if await pick_event_radio.is_visible():
            await pick_event_radio.click()
            await page.wait_for_timeout(500)
            
        # Click Classify button
        classify_btn = page.locator("button:has-text('Classify')").first
        await classify_btn.click()
        await page.wait_for_timeout(3500)
        
        # 3. Capture modal detail dialog view
        await page.screenshot(path="reports/console_screenshots/2_detail_dialog.png")
        print("Captured 2_detail_dialog.png")
        
        # Close dialog by pressing Escape
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(1500)
        
        # 4. Capture console view after classification (with user pin and log row)
        await page.screenshot(path="reports/console_screenshots/3_console_after_classify.png")
        print("Captured 3_console_after_classify.png")

        # 5. Test clicking an event or selecting log row
        log_row = page.locator("div[data-testid='stDataFrame']").first
        if await log_row.is_visible():
            await log_row.click(position={"x": 100, "y": 60})
            await page.wait_for_timeout(2000)
            await page.screenshot(path="reports/console_screenshots/4_row_selection_dialog.png")
            print("Captured 4_row_selection_dialog.png")
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(1000)
            
        await browser.close()
        print("All test screenshots captured successfully.")

if __name__ == "__main__":
    asyncio.run(main())
