import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# Base URL and headers
BASE_URL = "https://www.construction.co.uk/construction_directory.aspx"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
}

# Fetch the page
def fetch_batch_links():
    print("Fetching batch links...")
    res = requests.get(BASE_URL, headers=HEADERS, timeout=15)
    
    if res.status_code != 200:
        raise Exception(f"Failed to fetch main page: Status code {res.status_code}")

    soup = BeautifulSoup(res.text, "html.parser")

    batch_divs = soup.find_all("div", class_="col-md-4 d-flex no-wrap align-items-center")
    batch_links = []

    for div in batch_divs:
        a_tag = div.find("a")
        if a_tag and a_tag.get("href"):
            href = a_tag["href"]
            full_url = "https://www.construction.co.uk" + href
            batch_links.append(full_url)

    return batch_links

# Save to Excel
def save_to_excel(links, filename="batch_links.xlsx"):
    df = pd.DataFrame({"Batch Link": links})
    df.to_excel(filename, index=False)
    print(f"✅ Saved {len(links)} batch links to {filename}")

# Main execution
if __name__ == "__main__":
    links = fetch_batch_links()
    save_to_excel(links)
