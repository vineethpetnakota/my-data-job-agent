import os
import json
import requests
from datetime import datetime, timedelta

SERPER_KEY = os.getenv("SERPER_API_KEY")

def get_jobs():
    """Step 1: Hunt 15-20 quality jobs by limiting results per role."""
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
            # Setting num: 4 for 5 queries = 20 potential leads
            res = requests.post(url, headers=headers, json={"q": q, "num": 4, "tbs": "qdr:d"})
            organic = res.json().get('organic', [])
            all_results.extend(organic)
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

    # Step 4: Update History (Cleanup jobs older than 72 hours)
    three_days_ago = datetime.now() - timedelta(days=3)
    database = [j for j in database if datetime.strptime(j['found_at'], "%Y-%m-%d %H:%M") > three_days_ago]

    # Step 5: 6PM LOCK (23:00 UTC) - Move 'New' to 'Best_Archived' for Morning Review
    if datetime.now().hour == 23:
        for job in database:
            if job['status'] == 'New':
                job['status'] = 'Best_Archived'

    # Step 2 & 3: Capture timings and Replace old with new
    existing_urls = {j['url'] for j in database}
    new_entries = []
    
    for lead in new_raw_leads:
        url = lead.get('link')
        if url and url not in existing_urls:
            title = lead.get('title', 'Unknown Role')
            # Extracting posting time metadata from Google
            posted_time = lead.get('date', 'Just now') 
            
            new_entries.append({
                "title": title,
                "url": url,
                "company": title.split(" at ")[-1].split(" - ")[0] if " at " in title else "US Company",
                "status": "New",
                "posted_at": posted_time, # STEP 2
                "found_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            existing_urls.add(url)

    # Step 3: Replace logic - New entries go to the top, capped at 50 total
    database = (new_entries + database)[:50]

    with open(file_path, 'w') as f:
        json.dump(database, f, indent=4)
    print(f"✅ Success: {len(new_entries)} new leads. Total database: {len(database)}")

if __name__ == "__main__":
    update_database(get_jobs())
