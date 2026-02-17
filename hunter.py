import os
import json
import requests
from datetime import datetime

# Configuration
SERPER_KEY = os.getenv("SERPER_API_KEY")

def get_jobs():
    """
    Broad search query targeting your four specific roles.
    Includes Greenhouse and Lever boards.
    """
    # Flatter query structure to prevent Google/Serper from returning 0 results
    # We use quotes for exact multi-word phrases.
    query = '("Data Analyst" OR "Data Engineer" OR "Power BI Developer" OR "Business Intelligence Analyst") (site:boards.greenhouse.io OR site:jobs.lever.co)'
    
    url = "https://google.serper.dev/search"
    headers = {
        'X-API-KEY': str(SERPER_KEY),
        'Content-Type': 'application/json'
    }
    
    try:
        # Increase 'num' to 40 to ensure we capture a wide net
        # Use 'tbs': 'qdr:d' to find only jobs posted in the last 24 hours (Freshly posted)
        payload = {
            "q": query,
            "num": 40,
            "tbs": "qdr:d" 
        }
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        results = data.get('organic', [])
        
        print(f"📡 Serper Response Received. {len(results)} fresh leads found.")
        return results
    except Exception as e:
        print(f"❌ SERPER ERROR: {e}")
        return []

def update_database(new_raw_leads):
    file_path = 'jobs.json'
    
    # Load existing database
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                database = json.load(f)
        except:
            database = []
    else:
        database = []

    # Mark existing as 'Old' for the UI
    for job in database:
        job['status'] = 'Old'

    existing_urls = {job['url'] for job in database}
    new_found = 0
    
    for lead in new_raw_leads:
        url = lead.get('link')
        if url and url not in existing_urls:
            title = lead.get('title', 'Unknown Role')
            
            # Simple company extraction from title
            company = "Hiring Company"
            if " at " in title:
                company = title.split(" at ")[-1].split(" - ")[0].strip()
            elif " | " in title:
                company = title.split(" | ")[0].strip()

            database.append({
                "title": title,
                "url": url,
                "company": company,
                "status": "New",
                "score": 100, # Set to 100 since we aren't filtering
                "found_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            existing_urls.add(url)
            new_found += 1

    # Save sorted by most recent first
    with open(file_path, 'w') as f:
        json.dump(database, f, indent=4)
        
    print(f"💾 {new_found} new jobs added. Total database size: {len(database)}")

if __name__ == "__main__":
    print("🚀 Running Fresh Job Hunt...")
    leads = get_jobs()
    update_database(leads)
