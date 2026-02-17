import os
import json
import requests
from datetime import datetime

# Configuration
SERPER_KEY = os.getenv("SERPER_API_KEY")

def calculate_score(title, snippet):
    """Assigns a value score to each job."""
    score = 50
    t = title.lower()
    s = snippet.lower()
    
    # Priority Keywords (+ points)
    if any(x in t for x in ['engineer', 'bi', 'business intelligence']): score += 30
    if any(x in t for x in ['senior', 'sr', 'lead', 'staff']): score += 20
    if 'remote' in s or 'remote' in t: score += 10
    
    # Negative Keywords (- points)
    if any(x in t for x in ['intern', 'junior', 'entry']): score -= 60
    
    return max(0, min(score, 100))

def get_jobs():
    """Searches for multiple roles across top ATS boards."""
    roles = ['"Data Analyst"', '"Business Intelligence Analyst"', '"Financial Analyst"', '"Data Engineer"']
    query = f"({' OR '.join(roles)}) (site:boards.greenhouse.io OR site:jobs.lever.co)"
    
    url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': str(SERPER_KEY), 'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, json={"q": query, "num": 40})
        return response.json().get('organic', [])
    except:
        return []

def update_database(new_raw_leads):
    file_path = 'jobs.json'
    
    # Load existing database
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                database = json.load(f)
        except: database = []
    else:
        database = []

    # Mark all currently stored jobs as 'Old'
    for job in database:
        job['status'] = 'Old'

    existing_urls = {job['url'] for job in database}
    new_found = 0
    
    for lead in new_raw_leads:
        url = lead.get('link')
        if url and url not in existing_urls:
            title = lead.get('title', 'Unknown Role')
            database.append({
                "title": title,
                "url": url,
                "company": lead.get('snippet', '').split('...')[0][:30] or "Hiring Co",
                "status": "New",
                "score": calculate_score(title, lead.get('snippet', '')),
                "found_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            existing_urls.add(url)
            new_found += 1

    # Sort: Highest score first
    database.sort(key=lambda x: x['score'], reverse=True)

    with open(file_path, 'w') as f:
        json.dump(database, f, indent=4)
    print(f"📊 {new_found} new jobs added. Database size: {len(database)}")

if __name__ == "__main__":
    leads = get_jobs()
    update_database(leads)
