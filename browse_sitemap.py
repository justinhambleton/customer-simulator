import sys
import requests
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_page_title(url: str):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    try:
        driver.get(url)
        title = driver.title
    except Exception as e:
        title = f"Error fetching title: {e}"
    finally:
        driver.quit()

    return url, title

def browse_sitemap_concurrently(sitemap_url: str, max_workers: int = 2, max_urls: int = 10):
    # Fetch the sitemap XML
    response = requests.get(sitemap_url)

    if response.status_code != 200:
        print(f"Failed to fetch sitemap: {response.status_code}")
        return

    # Parse the sitemap XML
    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as e:
        print(f"Failed to parse XML: {e}")
        return

    urls = [url.text for url in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]

    # Randomly select up to max_urls URLs
    if len(urls) > max_urls:
        urls = random.sample(urls, max_urls)

    # Use ThreadPoolExecutor to fetch titles concurrently
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(fetch_page_title, url): url for url in urls}
        for future in as_completed(future_to_url):
            url, title = future.result()
            print(f"Title of the page at {url} is: {title}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python browse_sitemap.py <SITEMAP_URL>")
    else:
        sitemap_url = sys.argv[1]
        browse_sitemap_concurrently(sitemap_url)
