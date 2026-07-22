import io
from DrissionPage import ChromiumPage, ChromiumOptions
import pandas as pd
from datetime import datetime

def scrape_rack_prices():
    co = ChromiumOptions()
    co.no_imgs(False)  # Keep images enabled for Cloudflare Turnstile
    
    page = ChromiumPage(co)
    
    try:
        print("Navigating to Petro-Canada rack prices...")
        page.get("https://www.petro-canada.ca/en/business/rack-prices")
        
        print("Waiting for table to load...")
        # Wait up to 20s for the table container to appear
        page.wait.eles_loaded("css:table.rack-pricing__table", timeout=20)
        
        # Locate table element
        table_ele = page.ele("css:table.rack-pricing__table") or page.ele("tag:table")
        
        if table_ele:
            # Get raw HTML string
            html_table = table_ele.html
            
            # Wrap the HTML string with io.StringIO so Pandas parses it as HTML, not a file path
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