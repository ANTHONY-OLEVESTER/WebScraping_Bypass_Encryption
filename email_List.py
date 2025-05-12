import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
import random
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configs
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
}
BASE_URL = "https://www.construction.co.uk"
THREADS = 20
SAVE_EVERY = 20  # Save every 20 companies

def decode_emrp(text):
    decoded = ''
    for char in text:
        if char == '/':
            decoded += '.'
        elif char == 'A':
            decoded += '@'
        else:
            decoded += chr(ord(char) - 1)
    return decoded

def fetch_company_info(company_relative_link, retries=3):
    """Fetch company info, retry if both name/email are missing."""
    company_url = company_relative_link
    if not company_relative_link.startswith("http"):
        company_url = BASE_URL + company_relative_link

    for attempt in range(retries):
        try:
            res = requests.get(company_url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")

            # Company Name
            name_tag = soup.find("h2", class_="listingTitle text-md-start text-center")
            company_name = name_tag.find("span").text.strip() if name_tag else "N/A"

            # Email
            email = "N/A"
            email_span = soup.find("span", id="cphMain_lblCLEmail")
            if email_span:
                a_tag = email_span.find("a", href=True)
                if a_tag and a_tag['href'].startswith("mailto:"):
                    email = a_tag['href'].replace("mailto:", "").split("?")[0].strip()
                else:
                    script_tag = email_span.find("script")
                    if script_tag:
                        match = re.search(r"emrp\('([^']+)'", script_tag.string)
                        if match:
                            obfuscated_text = match.group(1)
                            email = decode_emrp(obfuscated_text)

            # Retry if completely empty
            if company_name == "N/A" and email == "N/A":
                if attempt < retries - 1:
                    print(f"⚠️ Press the button manually — retrying {company_url} after 10 seconds...")
                    time.sleep(10)
                    continue
                else:
                    return {"Company Name": "Dead Link", "Email": "Dead Link", "Company Link": company_url}

            return {"Company Name": company_name, "Email": email, "Company Link": company_url}
        
        except Exception as e:
            print(f"⚠️ Error on {company_url}: {e}")
            if attempt < retries - 1:
                print("🔁 Retrying after 10 seconds...")
                time.sleep(10)
            else:
                return {"Company Name": "Dead Link", "Email": "Dead Link", "Company Link": company_url}

def main():
    # Load links
    company_df = pd.read_excel("company_links.xlsx")
    company_links = company_df.iloc[:, 0].dropna().tolist()

    all_info = []
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = []
        for i, link in enumerate(company_links):
            futures.append(executor.submit(fetch_company_info, link))

            # Save after every SAVE_EVERY companies
            if len(futures) >= SAVE_EVERY:
                for future in tqdm(as_completed(futures), total=len(futures), desc=f"Scraping batch {i//SAVE_EVERY}"):
                    result = future.result()
                    all_info.append(result)

                    # Time estimate
                    elapsed = time.time() - start_time
                    scraped = len(all_info)
                    speed = scraped / elapsed
                    remaining = (len(company_links) - scraped) / speed
                    if scraped % 100 == 0:
                        print(f"⏳ {scraped}/{len(company_links)} scraped. Remaining: {remaining/3600:.2f} hours")

                # Save immediately
                df = pd.DataFrame(all_info)
                df.to_excel("output.xlsx", index=False)
                print(f"💾 Saved {scraped} companies to output.xlsx")
                
                futures = []  # Clear futures for next batch

        # Process leftover futures
        for future in tqdm(as_completed(futures), total=len(futures), desc="Final batch"):
            result = future.result()
            all_info.append(result)

    # Final save
    df = pd.DataFrame(all_info)
    df.to_excel("output.xlsx", index=False)
    print("\n✅ All companies saved to output.xlsx!")

if __name__ == "__main__":
    main()
