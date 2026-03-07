import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright

# Configuration
FUND_URLS = {
    "hdfc-mid-cap": "https://www.indmoney.com/mutual-funds/hdfc-mid-cap-fund-direct-plan-growth-option-3097",
    "hdfc-flexi-cap": "https://www.indmoney.com/mutual-funds/hdfc-flexi-cap-fund-direct-plan-growth-option-3184",
    "absl-quant": "https://www.indmoney.com/mutual-funds/aditya-birla-sun-life-quant-fund-direct-growth-1046035",
    "absl-elss": "https://www.indmoney.com/mutual-funds/aditya-birla-sun-life-elss-tax-saver-direct-plan-growth-21308",
    "edelweiss-nifty-next-50": "https://www.indmoney.com/mutual-funds/edelweiss-nifty-next-50-index-fund-direct-growth-1042502"
}

# Get the absolute path to the root data directory
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"

async def scrape_fund(browser, name, url):
    print(f"Scraping {name}: {url}...")
    # Create context with a real-world user agent and viewport
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 800}
    )
    page = await context.new_page()
    try:
        # Navigate to the page
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(5)  # Wait for initial load
        
        # Capture initial content (often contains NAV and summary)
        
        # Try to click 'Overview' tab to load more details
        try:
            overview_tab = page.get_by_text("Overview", exact=True)
            if await overview_tab.is_visible():
                await overview_tab.click()
                await asyncio.sleep(2)
        except Exception as e:
            print(f"[{name}] Overview tab not found or couldn't click: {e}")

        # Try to click 'About' tab to load fund manager and description
        try:
            about_tab = page.get_by_text("About", exact=True)
            if await about_tab.is_visible():
                await about_tab.click()
                await asyncio.sleep(2)
        except Exception as e:
            print(f"[{name}] About tab not found or couldn't click: {e}")

        # Final content capture
        content = await page.content()
        
        file_path = os.path.join(RAW_DATA_DIR, f"{name}.html")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Saved {name} to {file_path}")
    except Exception as e:
        print(f"Error scraping {name}: {e}")
    finally:
        await context.close()

async def main():
    if not os.path.exists(RAW_DATA_DIR):
        os.makedirs(RAW_DATA_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        tasks = []
        for name, url in FUND_URLS.items():
            tasks.append(scrape_fund(browser, name, url))
        
        await asyncio.gather(*tasks)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
