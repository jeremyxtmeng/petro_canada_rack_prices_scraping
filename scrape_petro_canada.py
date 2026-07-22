import io
import shutil
from DrissionPage import ChromiumPage, ChromiumOptions
import pandas as pd
from datetime import datetime

def scrape_rack_prices():
    co = ChromiumOptions()
    
    # 1. Enable headless mode (Correct DrissionPage v4 syntax)
    co.headless(True)
    
    # 2. Override default Headless user-agent so Cloudflare treats it as a standard desktop browser
    co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    
    # 3. Linux sandbox & CI environment flags
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-gpu')
    co.set_argument('--disable-dev-shm-usage')
    
    # 4. Point to system-installed Chrome binary if detected in PATH
    chrome_path = shutil.which("google-chrome") or shutil.which("google-chrome-stable")
    if chrome_path:
        co.set_browser_path(chrome_path)
    
    # Keep images enabled for Cloudflare Turnstile verification
    co.no_imgs(False)
    
    print("Launching Chromium instance...")
    page = ChromiumPage(co)
    
    try:
        print("Navigating to Petro-Canada rack prices...")
        page.get("https://www.petro-canada.ca/en/business/rack-prices")
        
        print("Waiting for table to load...")
        page.wait.eles_loaded("css:table.rack-pricing__table", timeout=25)
        
        table_ele = page.ele("css:table.rack-pricing__table") or page.ele("tag:table")
        
        if table_ele:
            html_table = table_ele.html
            dfs = pd.read_html(io.StringIO(html_table))
            
            if dfs:
                df = dfs[0]
                date_str = datetime.now().strftime("%Y-%m-%d")
                csv_filename = f"petro_canada_rack_prices_{date_str}.csv"
                
                df.to_csv(csv_filename, index=False)
                print(f"Success! Exported {len(df)} rows to '{csv_filename}'.")
            else:
                print("Could not parse table HTML into DataFrame.")
        else:
            print("Failed to locate table on the page.")

    except Exception as e:
        print(f"Error encountered: {e}")
    finally:
        page.quit()

if __name__ == "__main__":
    scrape_rack_prices()
