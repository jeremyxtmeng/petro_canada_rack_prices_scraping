import asyncio
import csv
from datetime import datetime
from playwright.async_api import async_playwright

async def scrape_rack_prices():
    async with async_playwright() as p:
        # Launch Chromium with anti-bot overrides
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            locale="en-CA"
        )
        
        page = await context.new_page()
        
        # Override navigator.webdriver flag
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        try:
            print("Navigating to Petro-Canada rack prices...")
            await page.goto(
                "https://www.petro-canada.ca/en/business/rack-prices", 
                wait_until="domcontentloaded", 
                timeout=60000
            )
            
            # 1. Wait broadly for any table element to appear in DOM
            print("Waiting for page content to render...")
            await page.wait_for_selector("table", timeout=30000)

            # 2. Extract table headers and body data in browser context
            data = await page.evaluate("""() => {
                const table = document.querySelector('table');
                if (!table) return null;

                const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.innerText.strip ? th.innerText.strip() : th.innerText.trim());
                const rows = Array.from(table.querySelectorAll('tbody tr')).map(tr => {
                    const location = tr.querySelector('th')?.innerText.trim() || tr.querySelector('td')?.innerText.trim() || '';
                    const cells = Array.from(tr.querySelectorAll('td')).map(td => td.innerText.trim());
                    // If location was in <th>, include it as first column
                    return tr.querySelector('th') ? [location, ...cells] : cells;
                });

                return { headers, rows };
            }""")

            if not data or not data["rows"]:
                print("Failed to locate tabular data on page.")
                return

            headers = data["headers"]
            rows_data = data["rows"]

            # 3. Export data to CSV
            date_str = datetime.now().strftime("%Y-%m-%d")
            filename = f"petro_canada_rack_prices_{date_str}.csv"

            with open(filename, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows_data)

            print(f"Success! Exported {len(rows_data)} locations to '{filename}'.")

        except Exception as e:
            print(f"Scraping failed: {e}")
            # Take screenshot on failure to debug visually
            await page.screenshot(path="error_screenshot.png")
            print("Saved 'error_screenshot.png' for inspection.")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_rack_prices())