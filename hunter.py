import os
import json
import requests
from datetime import datetime, timedelta

SERPER_KEY = os.getenv("SERPER_API_KEY")

# 1. FINAL DEFENSE: Blacklist non-US locations to prevent false positives
BLACKLIST = ["Africa", "Germany", "UK", "London", "India", "Canada", "Europe", "Berlin", "Munich", "Remote-EMEA"]

def get_jobs():
    """Hunt quality jobs with strict US-only filtering at the API and Query level."""
    # Grouping roles to maximize results per API call
    roles = '("Data Analyst" OR "Data Engineer" OR "Power BI")'
    
    # 2. QUERY LEVEL: Added exclusion operators (-) to filter early
    queries = [
        f'intitle:{roles} "United States" -Africa -Germany -India -UK site:jobs.lever.co',
        f'intitle:{roles} "United States" -London -Berlin site:job-boards.greenhouse.io',
        f'intitle:{roles} "United States" site:ashbyhq.com',
        f'intitle:{roles} "United States" site:smartrecruiters.com',
        f'intitle:{roles} "United States" site:breezy.hr',
        f'intitle:{roles} "United States" site:workable.com'
    ]
    
    url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': str(SERPER_KEY), 'Content-Type': 'application/json'}
    all_results = []

    for q in queries:
        try:
            # 3. API LEVEL: gl="us" forces US-based search results
            payload = {
                "q": q, 
                "num": 5, 
                "tbs": "qdr:d", # Fetch jobs from the last 24 hours only
                "gl": "us", 
                "hl": "en"
            }
            res = requests.post(url, headers=headers, json=payload)
            organic = res.json().get('organic', [])
            all_results.extend(organic)
        except Exception as e:
            print(f"Error: {e}")
            continue
            
    return all_results

def update_database(new_raw_leads):
    file_path = 'jobs.json'
    database = []
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            try: database = json.load(f)
            except: database = []

    # CLEANUP: Delete jobs older than 72 hours
    three_days_ago = datetime.now() - timedelta(days=3)
    database = [j for j in database if datetime.strptime(j['found_at'], "%Y-%m-%d %H:%M") > three_days_ago]

    # 6PM LOCK: Move to review section (23:00 UTC = 6PM EST)
    if datetime.now().hour == 23:
        for job in database:
            if job['status'] == 'New':
                job['status'] = 'Best_Archived'

    existing_urls = {j['url'] for j in database}
    new_entries = []
    
    for lead in new_raw_leads:
        url = lead.get('link')
        title = lead.get('title', 'Unknown Role')
        snippet = lead.get('snippet', '')

        # 4. PYTHON LEVEL: Check if the title or snippet contains blacklisted locations
        is_foreign = any(loc.lower() in title.lower() or loc.lower() in snippet.lower() for loc in BLACKLIST)
        
        if url and url not in existing_urls and not is_foreign:
            # Extract posted age (e.g., "4 hours ago")
            posted_at = lead.get('date', 'Recently')
            if "ago" in snippet and posted_at == "Recently":
                posted_at = snippet.split("—")[0].strip()

            new_entries.append({
                "title": title,
                "url": url,
                "company": title.split(" at ")[-1].split(" - ")[0] if " at " in title else "US Company",
                "status": "New",
                "posted_at": posted_at,
                "found_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            existing_urls.add(url)

    # Store 50 jobs and delete from database after 2-3 days
    database = (new_entries + database)[:50]

    with open(file_path, 'w') as f:
        json.dump(database, f, indent=4)
    print(f"✅ Success: {len(new_entries)} verified US leads added.")

if __name__ == "__main__":
    update_database(get_jobs())
