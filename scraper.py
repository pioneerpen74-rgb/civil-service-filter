import csv
import re
from playwright.sync_api import sync_playwright

# --- CRITERIA ---
# Must contain any of these keywords (leave empty to match all within your base search)
MUST_CONTAIN = []

# Exclude jobs containing any of these keywords
MUST_NOT_CONTAIN = [
    "veterinary",
    "clinical",
    "prison",
]

def run():
    print("Launching browser...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = context.new_page()

        print("Navigating to Civil Service search page...")
        page.goto("https://www.civilservicejobs.service.gov.uk/csr/index.cgi?pageaction=searchcontext&pageclass=Search", wait_until="networkidle")

        # Accept cookies if banner appears
        try:
            cookie_btn = page.locator("button:has-text('Accept'), button:has-text('agree'), input[value*='Accept']")
            if cookie_btn.count() > 0:
                cookie_btn.first.click()
                page.wait_for_timeout(1000)
        except Exception:
            pass

        # Fill search parameters
        try:
            # Location
            loc_input = page.locator("input[name*='location'], input[id*='location']").first
            if loc_input.count() > 0:
                loc_input.fill("London")

            # Distance: select 10 miles if dropdown exists
            dist_select = page.locator("select[name*='radius'], select[id*='distance'], select[name*='distance']").first
            if dist_select.count() > 0:
                dist_select.select_option(label=re.compile(r"10\s*miles?", re.I))

            # Salary min (£40,000)
            sal_input = page.locator("input[name*='minsalary'], input[id*='salary'], input[name*='salary']").first
            if sal_input.count() > 0:
                sal_input.fill("40000")

            # Submit form
            submit_btn = page.locator("input[type='submit'][value*='Search'], button[type='submit']:has-text('Search')").first
            if submit_btn.count() > 0:
                submit_btn.click()
            else:
                page.keyboard.press("Enter")

            page.wait_for_timeout(6000)
        except Exception as e:
            print(f"Notice during search setup: {e}")

        # Parse listings
        print(f"Current URL: {page.url}")
        jobs = []

        # Find search result links/blocks
        result_links = page.locator("a[href*='pageaction=viewjob'], .search-results-job-box, .job-search-result, table.table-jobs tr").all()
        print(f"Found {len(result_links)} potential listing elements.")

        for item in result_links:
            text = item.inner_text().strip()
            if not text or len(text) < 15:
                continue

            lower_text = text.lower()

            # Filter out exclusions
            if any(bad.lower() in lower_text for bad in MUST_NOT_CONTAIN):
                continue

            # Inclusion criteria check
            if MUST_CONTAIN and not any(good.lower() in lower_text for good in MUST_CONTAIN):
                continue

            # Extract URL if available
            href = item.get_attribute("href") or ""
            if href and not href.startswith("http"):
                href = f"https://www.civilservicejobs.service.gov.uk{href}"

            first_line = text.split("\n")[0].strip()

            jobs.append({
                "Title": first_line,
                "Link": href,
                "Summary": " ".join([l.strip() for l in text.split("\n")[1:] if l.strip()])[:250]
            })

        browser.close()

    # Save results
    with open("matched_jobs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Title", "Link", "Summary"])
        writer.writeheader()
        writer.writerows(jobs)

    print(f"Done. Saved {len(jobs)} matches to matched_jobs.csv.")

if __name__ == "__main__":
    run()
