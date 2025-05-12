import requests
from bs4 import BeautifulSoup
import csv
import time
import random
import os
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm  # <--- Add this import at the top
import re

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

BASE_URL = "https://www.construction.co.uk"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
}

BATCH_CHECKPOINT_FILE = "batch_checkpoint.csv"
RESULTS_FILE = "construction_companies.csv"
THREADS = 20
SAVE_EVERY_N_BATCHES = 10

# Utilities

def save_checkpoint(batch_links_done):
    with open(BATCH_CHECKPOINT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for link in batch_links_done:
            writer.writerow([link])

def load_checkpoint():
    if not os.path.exists(BATCH_CHECKPOINT_FILE):
        return set()
    with open(BATCH_CHECKPOINT_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f)

def append_results(data):
    file_exists = os.path.isfile(RESULTS_FILE)
    with open(RESULTS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Company Name", "Email", "Source URL"])  # add source link column
        writer.writerows(data)


# Scraping functions

def get_batch_links():
    url = f"{BASE_URL}/construction_directory.aspx"
    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")
    batch_divs = soup.find_all("div", class_="col-md-4 d-flex no-wrap align-items-center")
    batch_links = [a.find("a")['href'] for a in batch_divs if a.find("a")]
    return batch_links

def get_company_links(batch_link):
    company_links = []
    page_num = 1

    while True:
        page_url = batch_link
        if page_num > 1:
            page_url += f"?pagenum={page_num}"

        res = requests.get(page_url, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")
        company_blocks = soup.find_all("div", class_="col companyListButtons")

        if not company_blocks:
            break  # No more companies on this page
        
        for block in company_blocks:
            listing_link = block.find("div", class_="companyListListingLink")
            if listing_link and listing_link.find("a"):
                href = listing_link.find("a")['href']
                company_links.append(href)
        
        print(f"  Found {len(company_blocks)} companies on page {page_num} of batch.")
        page_num += 1
        time.sleep(random.uniform(1, 2))  # polite

    return company_links


def get_company_info(company_link):
    try:
        res = requests.get(company_link, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")

        # Company Name
        name_tag = soup.find("h2", class_="listingTitle text-md-start text-center")
        company_name = name_tag.find("span").text.strip() if name_tag else "N/A"

        # Email (new smart decoding)
        email = "N/A"
        email_span = soup.find("span", id="cphMain_lblCLEmail")

        if email_span:
            # Try direct <a> mailto first
            a_tag = email_span.find("a", href=True)
            if a_tag and a_tag['href'].startswith("mailto:"):
                email = a_tag['href'].replace("mailto:", "").split("?")[0].strip()
            else:
                # If no direct <a>, then decode from <script>
                script_tag = email_span.find("script")
                if script_tag:
                    # Extract inside emrp('xxxxx',...)
                    match = re.search(r"emrp\('([^']+)'", script_tag.string)
                    if match:
                        obfuscated_text = match.group(1)
                        email = decode_emrp(obfuscated_text)

        return (company_name, email, company_link)
    
    except Exception as e:
        print(f"Failed to scrape {company_link}: {e}")
        return ("N/A", "N/A", company_link)

# Main Workflow

def main():
    start_time = time.time()

    all_batch_links = get_batch_links()
    print(f"Found {len(all_batch_links)} batch links.")

    completed_batches = load_checkpoint()
    batches_to_do = [link for link in all_batch_links if (BASE_URL + link) not in completed_batches]

    print(f"{len(batches_to_do)} batches left to process.")

    current_results = []
    batches_done_counter = 0

    for batch_url in tqdm(batches_to_do, desc="Processing Batches"):
        full_batch_url = batch_url if batch_url.startswith("http") else BASE_URL + batch_url
        print(f"\nScraping batch: {full_batch_url}")

        company_links = get_company_links(full_batch_url)
        print(f"  Found {len(company_links)} companies in this batch.")

        full_company_links = [link if link.startswith("http") else BASE_URL + link for link in company_links]

        # Multithread the company scraping
        with ThreadPoolExecutor(max_workers=THREADS) as executor:
            batch_results = list(tqdm(executor.map(get_company_info, full_company_links), total=len(full_company_links), desc="  Scraping Companies"))

        current_results.extend(batch_results)

        completed_batches.add(full_batch_url)
        batches_done_counter += 1

        if batches_done_counter % SAVE_EVERY_N_BATCHES == 0:
            print(f"Saving after {batches_done_counter} batches...")
            save_checkpoint(completed_batches)
            append_results(current_results)
            current_results = []

        # After processing one batch
        elapsed_time = time.time() - start_time
        companies_scraped = len(current_results)
        if companies_scraped > 0:
            avg_time_per_company = elapsed_time / companies_scraped
            estimated_total_time = avg_time_per_company * 157000
            remaining_time = estimated_total_time - elapsed_time

            print(f"⏳ Scraped {companies_scraped} companies so far.")
            print(f"⚡ Average time per company: {avg_time_per_company:.3f} seconds")
            print(f"🕐 Estimated total time: {estimated_total_time/3600:.2f} hours")
            print(f"⌛ Estimated remaining time: {remaining_time/3600:.2f} hours")

        time.sleep(random.uniform(2, 5))


    # Final save
    if current_results:
        append_results(current_results)
    save_checkpoint(completed_batches)

    print("\nAll batches completed! Data saved to construction_companies.csv.")

if __name__ == "__main__":
    main()
