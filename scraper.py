import csv
import re
import urllib.parse
from playwright.sync_api import sync_playwright

# --- YOUR FILTER CRITERIA ---
# Words that MUST appear in the job title or description (leave empty [] to accept all)
MUST_CONTAIN = []

# Words to EXCLUDE (dealsbreakers)
MUST_NOT_CONTAIN = [
    "veterinary",
    "clinical",
    "prison",
]

def run():
    print("Launching browser...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Load Civil Service Search directly
        print("Navigating to Civil Service Jobs...")
        page.goto("https://www.civilservicejobs.service.gov.uk/csr/index.cgi", wait_until="networkidle")

        # Fill search filters
        try:
            # Location
            if page.locator("input#search_location").count() > 0:
                page.fill("input#search_location", "London")
            elif page.locator("input[name='search_location']").count() > 0:
                page.fill("input[name='search_location']", "London")
            
            # Submit search
            page.keyboard.press("Enter")
            page.wait_for_timeout(5000)
        except Exception as e:
            print(f"Filter interaction notice: {e}")

        # Extract listings
        jobs = []
        cards = page.locator(".search-results-job-box, .job-search-result, tr.search-result").all()
        print(f"Found {len(cards)} raw listings on page.")

        for card in cards:
            text = card.inner_text()
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            title = lines[0] if lines else "Unknown"

            # Check exclusion keywords
            lower_text = text.lower()
            if any(term.lower() in lower_text for term in MUST_NOT_CONTAIN):
                continue

            # Check inclusion keywords
            if MUST_CONTAIN and not any(term.lower() in lower_text for term in MUST_CONTAIN):
                continue

            jobs.append({
                "Title": title,
                "Details": " | ".join(lines[1:4]),
                "Raw": text[:200].replace("\n", " ")
            })

        browser.close()

    # Save filtered output
    with open("matched_jobs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Title", "Details", "Raw"])
        writer.writeheader()
        writer.writerows(jobs)

    print(f"\nCompleted! {len(jobs)} jobs matched your criteria. Saved to matched_jobs.csv")

if __name__ == "__main__":
    run()
