import os
import json
import requests
from datetime import datetime

# Config
SERPER_KEY = os.getenv("SERPER_API_KEY")

def get_jobs():
    # Broadened search for your specific roles
    roles = ['"Data Analyst"', '"Business Intelligence Analyst"', '"Financial Analyst"', '"Data Engineer"']
    query = f"({' OR '.join(roles)}) (site:boards.greenhouse.io OR site:jobs.lever.co)"
    
    url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': str(SERPER_KEY), 'Content-Type': 'application/json'}
    
    try:
        # Requesting 40 to ensure we hit your 10-20 lead goal per run
        response = requests.post(url, headers=headers, json={"q": query, "num": 40})
        return response.json().get('organic', [])
    except:
        return []

def update_database(new_raw_leads):
    file_path = 'jobs.json'
    
    # 1. Load existing jobs
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            database = json.load(f)
    else:
        database = []

    # 2. Mark all existing jobs as 'Old'
    for job in database:
        job['status'] = 'Old'

    # 3. Add new leads (Avoiding duplicates)
    existing_urls = {job['url'] for job in database}
    new_count = 0
    
    for lead in new_raw_leads:
        url = lead.get('link')
        if url not in existing_urls:
            database.append({
                "title": lead.get('title'),
                "url": url,
                "company": "New Lead",
                "status": "New", # Freshly found!
                "found_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            existing_urls.add(url)
            new_count += 1

    # 4. Save back to file
    with open(file_path, 'w') as f:
        json.dump(database, f, indent=4)
    
    print(f"📊 Summary: {new_count} New leads added. {len(database) - new_count} Archived.")

if __name__ == "__main__":
    raw = get_jobs()
    update_database(raw)
