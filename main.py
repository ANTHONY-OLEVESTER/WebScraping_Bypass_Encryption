import requests
from bs4 import BeautifulSoup
import csv
import time
import random


BASE_URL = "https://www.construction.co.uk"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
}

# Step 1: Get all Batch Links
def get_batch_links():
    url = f"{BASE_URL}/construction_directory.aspx"
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    batch_divs = soup.find_all("div", class_="col-md-4 d-flex no-wrap align-items-center")
    batch_links = [a.find("a")['href'] for a in batch_divs if a.find("a")]
    return batch_links

# Step 2: Get all Company Listing Links from Batch


def get_company_links(batch_link):
    res = requests.get(batch_link, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    company_blocks = soup.find_all("div", class_="col companyListButtons")
    company_links = []
    for block in company_blocks:
        listing_link = block.find("div", class_="companyListListingLink")
        if listing_link and listing_link.find("a"):
            href = listing_link.find("a")['href']
            company_links.append(href)
    return company_links

# Step 3: Extract Company Name + Email from Company Page
def get_company_info(company_link):
    res = requests.get(company_link, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    
    # Company Name
    name_tag = soup.find("h2", class_="listingTitle text-md-start text-center")
    company_name = name_tag.find("span").text.strip() if name_tag else "N/A"
    
    # Email
    email_tag = soup.find("span", id="cphMain_lblCLEmail")
    email = "N/A"
    if email_tag and email_tag.find("a"):
        email = email_tag.find("a").text.strip()
    
    return company_name, email

# MAIN
def main():
    batch_links = get_batch_links()
    print(f"Found {len(batch_links)} batch links.")

    results = []
    
    for batch_url in batch_links:
        full_batch_url = batch_url if batch_url.startswith("http") else BASE_URL + batch_url
        print(f"Scraping batch: {full_batch_url}")
        
        company_links = get_company_links(full_batch_url)
        print(f"  Found {len(company_links)} companies in this batch.")
        
        for company_relative_link in company_links:
            full_company_url = company_relative_link if company_relative_link.startswith("http") else BASE_URL + company_relative_link
            print(f"    Scraping company: {full_company_url}")
            
            try:
                company_name, email = get_company_info(full_company_url)
                results.append((company_name, email))
            except Exception as e:
                print(f"Failed to scrape {full_company_url}: {e}")
            
            time.sleep(random.uniform(1, 2))  # polite scraping

    # Save to CSV
    with open("construction_companies.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Company Name", "Email"])
        writer.writerows(results)

    print("Done! Saved to construction_companies.csv")

if __name__ == "__main__":
    main()
