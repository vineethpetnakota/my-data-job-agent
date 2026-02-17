import os
import json
import requests
from datetime import datetime, timedelta

SERPER_KEY = os.getenv("SERPER_API_KEY")

def get_jobs():
    """Aggressive search to ensure 10+ leads across 4 specific roles."""
    # We break it into a broader string for better Google indexing
    roles = '("Data Analyst" OR "Data Engineer" OR "Power BI Developer" OR "Business Intelligence Analyst")'
    sites = '(site:boards.greenhouse.io OR site:jobs.lever.co)'
    query = f"{roles} {sites}"
    
    url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': str(SERPER_KEY), 'Content-Type': 'application/json'}
    
    try:
        # Try Last Hour first
        res = requests.post(url, headers=headers, json={"q": query, "num": 40, "tbs": "qdr:h"})
        results = res.json().get('organic', [])
        
        # If last hour is thin, grab Last 24 Hours to ensure we hit your 10-job goal
        if len(results) < 15:
            res = requests.post(url, headers=headers, json={"q": query, "num": 40, "tbs": "qdr:d"})
            results = res.json().get('organic', [])
            
        print(f"📡 Found {len(results)} potential leads on Google.")
        return results
    except:
        return []

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

    # 2. 6PM ARCHIVE LOGIC (UTC 18:00)
    # If it's 6 PM, we 'lock' the current New jobs so they move to the middle UI section
    current_hour = datetime.now().hour
    if current_hour == 18:
        for job in database:
            if job['status'] == 'New':
                job['status'] = 'Best_Archived'

    # 3. ADD NEW (Avoiding Duplicates)
    existing_urls = {j['url'] for j in database}
    new_entries = []
    for lead in new_raw_leads:
        url = lead.get('link')
        if url and url not in existing_urls:
            title = lead.get('title', 'Unknown Role')
            new_entries.append({
                "title": title,
                "url": url,
                "company": title.split(" at ")[-1].split(" - ")[0] if " at " in title else "Hiring Co",
                "status": "New",
                "found_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            existing_urls.add(url)

    # 4. MERGE & LIMIT
    # Newest go at the top
    database = new_entries + database
    database = database[:50] # Your 50-job limit

    with open(file_path, 'w') as f:
        json.dump(database, f, indent=4)
    print(f"✅ Success: {len(new_entries)} fresh leads added. Total stored: {len(database)}")

if __name__ == "__main__":
    update_database(get_jobs())
