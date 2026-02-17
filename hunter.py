import os
import json
import requests
from datetime import datetime, timedelta

# Configuration
SERPER_KEY = os.getenv("SERPER_API_KEY")

def get_jobs():
    """Fetches US-only leads across 4 roles and 2 platforms."""
    # Boolean search for roles
    roles = '("Data Analyst" OR "Data Engineer" OR "Power BI Developer" OR "Business Intelligence Analyst")'
    
    # Comprehensive US location tags
    location = '("United States" OR "US" OR "USA")'
    
    # Platform-specific queries to maximize results
    queries = [
        f"{roles} {location} site:jobs.lever.co",
        f"{roles} {location} site:boards.greenhouse.io"
    ]
    
    url = "https://google.serper.dev/search"
    headers = {
        'X-API-KEY': str(SERPER_KEY),
        'Content-Type': 'application/json'
    }
    
    all_results = []

    for q in queries:
        try:
            # We use last 24h (qdr:d) to ensure a steady stream of 10+ jobs
            payload = {"q": q, "num": 40, "tbs": "qdr:d"}
            res = requests.post(url, headers=headers, json=payload)
            organic = res.json().get('organic', [])
            all_results.extend(organic)
            print(f"📡 Found {len(organic)} potential leads on {q.split('site:')[1]}")
        except Exception as e:
            print(f"❌ Error searching: {e}")
            continue
            
    return all_results

def update_database(new_raw_leads):
    file_path = 'jobs.json'
    database = []
    
    # Load existing data
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            try:
                database = json.load(f)
            except:
                database = []

    # 1. CLEANUP: Delete jobs older than 3 days (72 hours)
    three_days_ago = datetime.now() - timedelta(days=3)
    database = [
        j for j in database 
        if datetime.strptime(j['found_at'], "%Y-%m-%d %H:%M") > three_days_ago
    ]

    # 2. 6PM ARCHIVE LOGIC (Triggering at 23:00 UTC / ~6:00 PM EST)
    # This locks 'New' jobs into 'Best_Archived' status for your morning review.
    current_hour = datetime.now().hour
    if current_hour == 23:
        for job in database:
            if job['status'] == 'New':
                job['status'] = 'Best_Archived'

    # 3. ADD NEW ENTRIES: Deduplicate using the URL
    existing_urls = {j['url'] for j in database}
    new_entries = []
    
    for lead in new_raw_leads:
        url = lead.get('link')
        if url and url not in existing_urls:
            title = lead.get('title', 'Unknown Role')
            
            # Simple company extraction logic
            company = "Hiring Company"
            if " at " in title:
                company = title.split(" at ")[-1].split(" - ")[0].strip()
            elif " | " in title:
                company = title.split(" | ")[0].strip()

            new_entries.append({
                "title": title,
                "url": url,
                "company": company,
                "status": "New",
                "found_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            existing_urls.add(url)

    # 4. ORGANIZE: Newest at top, keep only the top 50 total
    database = (new_entries + database)[:50]

    # 5. SAVE
    with open(file_path, 'w') as f:
        json.dump(database, f, indent=4)
        
    print(f"✅ Success: {len(new_entries)} fresh US leads added. Total database: {len(database)}")

if __name__ == "__main__":
    print(f"🚀 Starting Hunt at {datetime.now().strftime('%Y-%m-%d %H:%M')}...")
    leads = get_jobs()
    update_database(leads)
