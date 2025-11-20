"""
Netmeds Scraper using Selenium
Saves HTML after JavaScript loads, then parses it
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
import os

# Medicine URLs
MEDICINE_DATA = {
    "Paracip 500mg": "https://www.netmeds.com/products?q=paracetamol%20500mg",
    "Crocin Advance": "https://www.netmeds.com/products?q=Crocin%20Advance",
    "Dolo 650mg": "https://www.netmeds.com/products?q=Dolo%20650mg",
    "Azithral 500": "https://www.netmeds.com/products?q=Azithral%20500",
    "Pan 40": "https://www.netmeds.com/products?q=Pan%2040",
    "Calpol 650mg": "https://www.netmeds.com/products?q=Calpol%20650mg",
    "Augmentin 625": "https://www.netmeds.com/products?q=Augmentin%20625",
    "Betadine Gargle": "https://www.netmeds.com/products?q=Betadine%20Gargle",
    "Combiflam": "https://www.netmeds.com/products?q=Combiflam",
    "Sinarest": "https://www.netmeds.com/products?q=Sinarest"
}

class NetmedsSeleniumScraper:
    def __init__(self):
        print("🚀 Initializing Netmeds Scraper...")
        
        # Setup Chrome options
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # Initialize driver
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        self.driver.maximize_window()
        self.scraped_data = []
        
        # Create folders
        os.makedirs('../html_pages_selenium', exist_ok=True)
        os.makedirs('../data', exist_ok=True)
    
    def scrape_medicine(self, medicine_name, url):
        """Scrape a single medicine page"""
        try:
            print(f"\n🔍 Scraping: {medicine_name}")
            print(f"   URL: {url}")
            
            # Load the page
            self.driver.get(url)
            
            # Wait for content to load
            print("   ⏳ Waiting for page to load...")
            time.sleep(8)  # Give time for JavaScript to load
            
            # Scroll down to trigger lazy loading
            self.driver.execute_script("window.scrollTo(0, 1000);")
            time.sleep(2)
            
            # Save the fully loaded HTML
            html_content = self.driver.page_source
            filename = f"../html_pages_selenium/{medicine_name.replace(' ', '_')}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"   💾 Saved HTML to: {filename}")
            
            # Parse the page
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Debug: Save a snippet to see what we have
            print(f"   🔎 Analyzing page content...")
            
            # Try to find ANY product elements with various selectors
            # Look for common patterns in e-commerce sites
            possible_selectors = [
                ('div', {'class': 'product'}),
                ('div', {'class': 'item'}),
                ('div', {'data-sku': True}),
                ('article', {}),
                ('li', {'class': 'product'}),
            ]
            
            products = []
            for tag, attrs in possible_selectors:
                products = soup.find_all(tag, attrs)
                if products:
                    print(f"   ✅ Found {len(products)} products using {tag} tag")
                    break
            
            if not products:
                # Try searching for price elements directly
                print(f"   🔍 Searching for price elements...")
                price_elements = soup.find_all(string=lambda t: '₹' in str(t) if t else False)
                
                if price_elements:
                    print(f"   💰 Found {len(price_elements)} price elements")
                    # Extract up to 3 unique prices
                    found_prices = []
                    for i, price_elem in enumerate(price_elements[:10]):
                        price_text = price_elem.strip()
                        if price_text and price_text not in found_prices:
                            found_prices.append(price_text)
                            
                            # Try to find product name nearby
                            parent = price_elem.find_parent()
                            product_title = 'Product'
                            
                            if parent:
                                # Look for nearby text that might be product name
                                for sibling in parent.find_all(['span', 'div', 'h3', 'h2', 'a']):
                                    text = sibling.get_text(strip=True)
                                    if text and len(text) > 10 and '₹' not in text:
                                        product_title = text[:100]
                                        break
                            
                            self.scraped_data.append({
                                'medicine_name': medicine_name,
                                'website': 'Netmeds',
                                'price': price_text,
                                'availability': 'In Stock',
                                'product_title': product_title,
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                            
                            print(f"   ✅ [{len(found_prices)}] {product_title[:40]} - {price_text}")
                            
                            if len(found_prices) >= 3:
                                break
                    
                    if found_prices:
                        return
            
            # If we found product containers, extract from them
            if products:
                count = 0
                for product in products[:3]:
                    try:
                        # Extract product name
                        name_elem = product.find(['h2', 'h3', 'h4', 'a', 'span'])
                        product_title = name_elem.get_text(strip=True) if name_elem else 'Product'
                        
                        # Extract price
                        price_elem = product.find(string=lambda t: '₹' in str(t) if t else False)
                        price = price_elem.strip() if price_elem else 'N/A'
                        
                        if price != 'N/A':
                            self.scraped_data.append({
                                'medicine_name': medicine_name,
                                'website': 'Netmeds',
                                'price': price,
                                'availability': 'In Stock',
                                'product_title': product_title[:100],
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                            
                            count += 1
                            print(f"   ✅ [{count}] {product_title[:40]} - {price}")
                    except Exception as e:
                        continue
                
                if count > 0:
                    return
            
            # If nothing found
            print(f"   ⚠️ No products extracted for {medicine_name}")
            self.scraped_data.append({
                'medicine_name': medicine_name,
                'website': 'Netmeds',
                'price': 'N/A',
                'availability': 'Not Found',
                'product_title': 'N/A',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            self.scraped_data.append({
                'medicine_name': medicine_name,
                'website': 'Netmeds',
                'price': 'N/A',
                'availability': 'Error',
                'product_title': 'N/A',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
    
    def save_to_csv(self):
        """Save data to CSV"""
        try:
            if not self.scraped_data:
                print("\n⚠️ No data to save!")
                return
            
            df = pd.DataFrame(self.scraped_data)
            filename = f'../data/netmeds_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            df.to_csv(filename, index=False, encoding='utf-8')
            
            print(f"\n{'='*60}")
            print(f"💾 Data saved to: {filename}")
            print(f"📊 Total records: {len(self.scraped_data)}")
            print(f"{'='*60}")
            
            # Display preview
            print("\n📋 Preview of scraped data:")
            print(df.to_string())
            
        except Exception as e:
            print(f"❌ Error saving CSV: {str(e)}")
    
    def close(self):
        """Close browser"""
        try:
            self.driver.quit()
            print("\n✅ Browser closed!")
        except:
            pass
    
    def run(self):
        """Main execution"""
        print("="*60)
        print("🏥 NETMEDS SCRAPER - SELENIUM VERSION")
        print("="*60)
        
        try:
            for medicine_name, url in MEDICINE_DATA.items():
                self.scrape_medicine(medicine_name, url)
                time.sleep(3)  # Polite delay
            
            self.save_to_csv()
            
        except KeyboardInterrupt:
            print("\n⚠️ Interrupted by user!")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
        finally:
            self.close()

if __name__ == "__main__":
    scraper = NetmedsSeleniumScraper()
    scraper.run()