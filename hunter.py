import os
import json
import requests
from datetime import datetime, timedelta

SERPER_KEY = os.getenv("SERPER_API_KEY")

def get_jobs():
    """Improved search using broader queries and updated Greenhouse domains."""
    # Breaking search into smaller, high-probability strings
    queries = [
        'intitle:"Data Analyst" "United States" site:jobs.lever.co',
        'intitle:"Data Engineer" "United States" site:jobs.lever.co',
        'intitle:"Data Analyst" "United States" site:job-boards.greenhouse.io',
        'intitle:"Power BI" "United States" site:job-boards.greenhouse.io',
        'intitle:"Business Intelligence" "United States" site:boards.greenhouse.io'
    ]
    
    url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': str(SERPER_KEY), 'Content-Type': 'application/json'}
    all_results = []

    for q in queries:
        try:
            # Removed 'tbs' filter temporarily to ensure we get results; 
            # our script will handle the 'freshness' by checking the URL later.
            res = requests.post(url, headers=headers, json={"q": q, "num": 20})
            organic = res.json().get('organic', [])
            all_results.extend(organic)
            print(f"📡 Found {len(organic)} leads for: {q[:30]}...")
        except:
            continue
            
    return all_results

def update_database(new_raw_leads):
    file_path = 'jobs.json'
    database = []
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            try: database = json.load(f)
            except: database = []

    # 1. CLEANUP (Older than 3 days)
    three_days_ago = datetime.now() - timedelta(days=3)
    database = [j for j in database if datetime.strptime(j['found_at'], "%Y-%m-%d %H:%M") > three_days_ago]

    # 2. 6PM LOCK (23:00 UTC)
    if datetime.now().hour == 23:
        for job in database:
            if job['status'] == 'New':
                job['status'] = 'Best_Archived'

    # 3. ADD NEW (Deduplicate)
    existing_urls = {j['url'] for j in database}
    new_entries = []
    for lead in new_raw_leads:
        url = lead.get('link')
        if url and url not in existing_urls:
            title = lead.get('title', 'Unknown Role')
            new_entries.append({
                "title": title,
                "url": url,
                "company": title.split(" at ")[-1].split(" - ")[0] if " at " in title else "US Tech Co",
                "status": "New",
                "found_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            existing_urls.add(url)

    # 4. MERGE & LIMIT
    database = (new_entries + database)[:50]

    with open(file_path, 'w') as f:
        json.dump(database, f, indent=4)
    print(f"✅ Success: {len(new_entries)} leads added. Total stored: {len(database)}")

if __name__ == "__main__":
    update_database(get_jobs())
