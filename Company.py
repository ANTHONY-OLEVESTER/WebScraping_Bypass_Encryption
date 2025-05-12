import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random
from tqdm import tqdm

BASE_URL = "https://www.construction.co.uk"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
}

def fix_link(link):
    """Fix the broken batch links."""
    if link.startswith("https://www.construction.co.ukhttps://"):
        link = link.replace("https://www.construction.co.ukhttps://", "https://")
    return link

def get_company_links(batch_link):
    company_links = []
    page_num = 1

    while True:
        page_url = batch_link
        if page_num > 1:
            page_url += f"?pagenum={page_num}"

        try:
            res = requests.get(page_url, headers=HEADERS, timeout=10)
            if res.status_code != 200:
                print(f"❌ Failed to load {page_url} with status {res.status_code}")
                break

            soup = BeautifulSoup(res.text, "html.parser")
            company_blocks = soup.find_all("div", class_="col companyListButtons")

            if not company_blocks:
                break  # No more companies

            for block in company_blocks:
                listing_link = block.find("div", class_="companyListListingLink")
                if listing_link and listing_link.find("a"):
                    href = listing_link.find("a")['href']
                    full_link = BASE_URL + href if href.startswith("/") else href
                    company_links.append(full_link)

            print(f"  ✅ Found {len(company_blocks)} companies on page {page_num} of batch.")

            page_num += 1
            time.sleep(random.uniform(1, 2))  # polite pause

        except Exception as e:
            print(f"⚠️ Error on {page_url}: {e}")
            break

    return company_links

def main():
    batch_df = pd.read_excel("batch_links.xlsx")
    batch_links = batch_df.iloc[:, 0].dropna().tolist()

    all_company_links = []
    start_time = time.time()

    for idx, batch_link in enumerate(tqdm(batch_links, desc="Processing batches"), 1):
        fixed_link = fix_link(batch_link)
        print(f"\n🔗 Scraping batch: {fixed_link}")

        links = get_company_links(fixed_link)
        all_company_links.extend(links)

        # 🔥 Immediately save progress
        temp_df = pd.DataFrame(all_company_links, columns=["CompanyLink"])
        temp_df.to_excel("company_links.xlsx", index=False)

        # Timing estimates
        elapsed = time.time() - start_time
        avg_time_per_batch = elapsed / idx
        est_batches_for_157k = 157000 / 20  # assume avg 20 companies per batch (adjust if needed)
        est_total_time = avg_time_per_batch * est_batches_for_157k
        est_remaining_time = est_total_time - elapsed

        print(f"\n⏳ Batches scraped: {idx}")
        print(f"⚡ Average time per batch: {avg_time_per_batch:.2f} seconds")
        print(f"🕐 Estimated total time for 157,000 companies: {est_total_time/3600:.2f} hours")
        print(f"⌛ Estimated remaining time: {est_remaining_time/3600:.2f} hours")

    # Save all company links
    company_df = pd.DataFrame(all_company_links, columns=["CompanyLink"])
    company_df.to_excel("company_links.xlsx", index=False)
    print("\n✅ All company links saved to company_links.xlsx!")

if __name__ == "__main__":
    main()
