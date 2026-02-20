import os
import json
import requests
from datetime import datetime, timedelta

SERPER_KEY = os.getenv("SERPER_API_KEY")

def get_jobs():
    """Step 1: Hunt 15-20 quality jobs across multi-site platforms including Power BI."""
    # We use OR to find any of the three roles in one query per site
    queries = [
        'intitle:("Data Analyst" OR "Data Engineer" OR "Power BI") "United States" site:ashbyhq.com',
        'intitle:("Data Analyst" OR "Data Engineer" OR "Power BI") "United States" site:smartrecruiters.com',
        'intitle:("Data Analyst" OR "Data Engineer" OR "Power BI") "United States" site:breezy.hr',
        'intitle:("Data Analyst" OR "Data Engineer" OR "Power BI") "United States" site:workable.com'
    ]
    
    url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': str(SERPER_KEY), 'Content-Type': 'application/json'}
    all_results = []

    for q in queries:
        try:
            # We set num: 5 to get ~20 fresh leads total across 4 sites
            # 'tbs': 'qdr:d' ensures only jobs from the last 24 hours are found
            res = requests.post(url, headers=headers, json={"q": q, "num": 5, "tbs": "qdr:d"})
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

    # Step 4: Update History (Cleanup leads older than 72 hours)
    three_days_ago = datetime.now() - timedelta(days=3)
    database = [j for j in database if datetime.strptime(j['found_at'], "%Y-%m-%d %H:%M") > three_days_ago]

    # Step 5: 6PM Morning Review Lock (23:00 UTC)
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
            snippet = lead.get('snippet', '')
            
            # Step 2: Extracting real posting time hint for dashboard display
            posted_at = lead.get('date', 'Recently')
            if "ago" in snippet and posted_at == "Recently":
                posted_at = snippet.split("—")[0].strip()

            new_entries.append({
                "title": title,
                "url": url,
                "company": title.split(" at ")[-1].split(" - ")[0] if " at " in title else "Hiring Co",
                "status": "New",
                "posted_at": posted_at,
                "found_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            existing_urls.add(url)

    # Step 3: Replace old jobs (Keep top 50 freshest)
    database = (new_entries + database)[:50]

    with open(file_path, 'w') as f:
        json.dump(database, f, indent=4)
    print(f"✅ Success: {len(new_entries)} leads added.")

if __name__ == "__main__":
    update_database(get_jobs())
