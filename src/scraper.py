import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import logging

def scrape_chapter(
    url: str,
    output_dir: str = "data/raw",
    screenshot_dir: str = "data/screenshots",
    timeout_ms: int = 10000,
) -> dict:
    # Scrape text and screenshot from a book chapter URL
      
    
            
   
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(screenshot_dir).mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        
        ## Launch browser (headless=True for production)
        
        browser = p.chromium.launch(headless=True)  # Set to True later
        page = browser.new_page()
        
        try:
            # Navigate to URL and wait for content
            page.goto(url, timeout=timeout_ms)
            page.wait_for_selector("div.mw-parser-output")  ##wikisource content container
            
            # Take screenshot
            chapter_name = url.split("/")[-1]
            screenshot_path = f"{screenshot_dir}/{chapter_name}.png"
            page.screenshot(path=screenshot_path, full_page=True)
            
            # Extract text
            soup = BeautifulSoup(page.content(), "html.parser")
            content_div = soup.find("div", class_="mw-parser-output")
            text = content_div.get_text(separator="\n", strip=True)
            
            # Save raw text
            output_path = f"{output_dir}/{chapter_name}.txt"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)
            
            return {
                "text": text,
                "screenshot_path": screenshot_path,
                "output_path": output_path,
            }
            
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return None
            
        finally:
            browser.close()


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("❌ Error: Please provide a chapter URL as an argument.")
        sys.exit(1)

    url = sys.argv[1]
    result = scrape_chapter(url)

    if result:
        print(f"✅ Scraped text saved to: {result['output_path']}")
        print(f"✅ Screenshot saved to: {result['screenshot_path']}")
    else:
        print("❌ Scraping failed.")

    
