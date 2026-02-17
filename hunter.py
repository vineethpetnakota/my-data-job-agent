import os
import json
import requests
from datetime import datetime, timedelta

# Config
SERPER_KEY = os.getenv("SERPER_API_KEY")

def get_jobs():
    """Fetches at least 10-20 leads. Tries last hour first, then last 24h."""
    query = '("Data Analyst" OR "Data Engineer" OR "Power BI Developer" OR "Business Intelligence Analyst") (site:boards.greenhouse.io OR site:jobs.lever.co)'
    url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': str(SERPER_KEY), 'Content-Type': 'application/json'}
    
    try:
        # Step 1: Try Fresh (Last Hour)
        res = requests.post(url, headers=headers, json={"q": query, "num": 40, "tbs": "qdr:h"})
        results = res.json().get('organic', [])
        
        # Step 2: Fallback (Last Day) to ensure you get 10+ leads
        if len(results) < 10:
            res = requests.post(url, headers=headers, json={"q": query, "num": 40, "tbs": "qdr:d"})
            results = res.json().get('organic', [])
        return results
    except:
        return []

def update_database(new_raw_leads):
    file_path = 'jobs.json'
    database = []
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            database = json.load(f)

    # 1. CLEANUP: Delete jobs older than 3 days
    three_days_ago = datetime.now() - timedelta(days=3)
    database = [j for j in database if datetime.strptime(j['found_at'], "%Y-%m-%d %H:%M") > three_days_ago]

    # 2. SEGREGATION: At 6 PM (18:00), move all current 'New' to 'Best_Archived'
    # This locks them in for your morning review.
    current_hour = datetime.now().hour
    if current_hour == 18:
        for job in database:
            if job['status'] == 'New':
                job['status'] = 'Best_Archived'

    # 3. ADD NEW LEADS: Avoiding duplicates
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

    # 4. ORGANIZE: Newest always at top
    database = new_entries + database

    # 5. CONCISE LIMIT: Store exactly 50 total
    database = database[:50]

    with open(file_path, 'w') as f:
        json.dump(database, f, indent=4)
    print(f"Update complete. {len(new_entries)} fresh leads added.")

if __name__ == "__main__":
    leads = get_jobs()
    update_database(leads)
