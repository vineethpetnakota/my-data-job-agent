import os
import json
import requests
from datetime import datetime, timedelta

SERPER_KEY = os.getenv("SERPER_API_KEY")

def get_jobs():
    """Aggressive multi-role search to guarantee leads."""
    # Breaking these down ensures Google doesn't get confused by a long string
    roles = [
        '"Data Analyst"', 
        '"Data Engineer"', 
        '"Power BI Developer"', 
        '"Business Intelligence Analyst"'
    ]
    # We target both major boards
    sites = "(site:boards.greenhouse.io OR site:jobs.lever.co)"
    
    url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': str(SERPER_KEY), 'Content-Type': 'application/json'}
    
    all_results = []
    
    # We search each role to maximize volume
    for role in roles:
        query = f"{role} {sites}"
        # Try last 24 hours (qdr:d) to ensure we always have 10+ jobs for you
        payload = {"q": query, "num": 20, "tbs": "qdr:d"} 
        
        try:
            res = requests.post(url, headers=headers, json=payload)
            organic = res.json().get('organic', [])
            all_results.extend(organic)
            print(f"📡 Found {len(organic)} leads for {role}")
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

    # 2. 6PM LOCK (Archive Logic)
    # This moves 'New' to 'Best_Archived' at 6PM UTC
    if datetime.now().hour == 18:
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
                "company": title.split(" at ")[-1].split(" - ")[0] if " at " in title else "Hiring Co",
                "status": "New",
                "found_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            existing_urls.add(url)

    # 4. MERGE & LIMIT
    # Newest at top, capped at 50
    database = new_entries + database
    database = database[:50]

    with open(file_path, 'w') as f:
        json.dump(database, f, indent=4)
    print(f"✅ Success: {len(new_entries)} fresh leads added. Total stored: {len(database)}")

if __name__ == "__main__":
    update_database(get_jobs())
