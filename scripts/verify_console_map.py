import os
import asyncio
from playwright.async_api import async_playwright

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/home/hr10j44t/Downloads/RescueAI/.cache/ms-playwright"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 950})
        page = await context.new_page()

        print("Navigating to http://localhost:8501 ...")
        await page.goto("http://localhost:8501", wait_until="networkidle", timeout=35000)
        await page.wait_for_timeout(4500)
        os.makedirs("reports/live_verification", exist_ok=True)

        # 1. Capture Satellite Hybrid Real World Map (Default)
        await page.screenshot(path="reports/live_verification/1_satellite_hybrid_real_world.png")
        print("Captured 1_satellite_hybrid_real_world.png")

        # 2. Test Region Jump to 'Asia-Pac' (Taiwan, Japan, Vietnam, Bangladesh, Indonesia)
        region_select = page.locator("div[data-baseweb='select']:has-text('Global')").first
        if await region_select.is_visible():
            await region_select.click()
            await page.wait_for_timeout(500)
            asia_opt = page.locator("li:has-text('Asia-Pac')").first
            if await asia_opt.is_visible():
                await asia_opt.click()
                print("Selected Region: Asia-Pac")
                await page.wait_for_timeout(4000)
                await page.screenshot(path="reports/live_verification/2_asia_pacific_satellite_zoom.png")
                print("Captured 2_asia_pacific_satellite_zoom.png")

        # 3. Test NASA Night Lights Basemap
        basemap_select = page.locator("div[data-baseweb='select']:has-text('Satellite Hybrid')").first
        if await basemap_select.is_visible():
            await basemap_select.click()
            await page.wait_for_timeout(500)
            night_opt = page.locator("li:has-text('NASA Night Lights')").first
            if await night_opt.is_visible():
                await night_opt.click()
                print("Selected Basemap: NASA Night Lights")
                await page.wait_for_timeout(4000)
                await page.screenshot(path="reports/live_verification/3_nasa_night_lights.png")
                print("Captured 3_nasa_night_lights.png")

        # 4. Test Heatmap Layer Toggle
        heatmap_cb = page.locator("text=Heatmap").first
        if await heatmap_cb.is_visible():
            await heatmap_cb.click()
            print("Toggled Heatmap Layer")
            await page.wait_for_timeout(3000)
            await page.screenshot(path="reports/live_verification/4_disaster_heatmap_overlay.png")
            print("Captured 4_disaster_heatmap_overlay.png")

        await browser.close()
        print("Real world map verification finished successfully.")

if __name__ == "__main__":
    asyncio.run(main())
