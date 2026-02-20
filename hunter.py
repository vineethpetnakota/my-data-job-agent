import os
import json
import requests
from datetime import datetime, timedelta

SERPER_KEY = os.getenv("SERPER_API_KEY")

def get_jobs():
    """Step 1: Hunt quality jobs across ALL 6 major platforms."""
    # Targeting specific roles with a high-probability search string
    roles = '("Data Analyst" OR "Data Engineer" OR "Power BI")'
    
    # Covering the most candidate-friendly tech platforms
    queries = [
        f'intitle:{roles} "United States" site:jobs.lever.co',
        f'intitle:{roles} "United States" site:job-boards.greenhouse.io',
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
            # Fetching 4 results per platform to stay around the 20-25 lead target
            # 'tbs':'qdr:d' restricts results to those posted in the last 24 hours
            res = requests.post(url, headers=headers, json={"q": q, "num": 4, "tbs": "qdr:d"})
            organic = res.json().get('organic', [])
            all_results.extend(organic)
        except Exception as e:
            print(f"Error fetching {q}: {e}")
            continue
            
    return all_results

def update_database(new_raw_leads):
    file_path = 'jobs.json'
    database = []
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            try: database = json.load(f)
            except: database = []

    # A. 72-HOUR CLEANUP: Delete jobs found more than 3 days ago
    three_days_ago = datetime.now() - timedelta(days=3)
    database = [j for j in database if datetime.strptime(j['found_at'], "%Y-%m-%d %H:%M") > three_days_ago]

    # B. 6PM LOCK: Archive "New" jobs for morning review at 23:00 UTC (6PM EST)
    if datetime.now().hour == 23:
        for job in database:
            if job['status'] == 'New':
                job['status'] = 'Best_Archived'

    # C. DEDUPLICATION & METADATA: Capture real "Posted" time
    existing_urls = {j['url'] for j in database}
    new_entries = []
    
    for lead in new_raw_leads:
        url = lead.get('link')
        if url and url not in existing_urls:
            title = lead.get('title', 'Unknown Role')
            snippet = lead.get('snippet', '')
            
            # Extract "4 hours ago" etc. from Google search snippet
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

    # D. SAVE: Prepend new jobs and keep only the 50 freshest total
    database = (new_entries + database)[:50]

    with open(file_path, 'w') as f:
        json.dump(database, f, indent=4)
    print(f"✅ Hunt complete: {len(new_entries)} fresh leads added. Database size: {len(database)}")

if __name__ == "__main__":
    update_database(get_jobs())
