import os
import json
import requests
from datetime import datetime

# Configuration
SERPER_KEY = os.getenv("SERPER_API_KEY")

def calculate_score(title, snippet):
    """Assigns a value score to each job based on your preferences."""
    score = 50
    t = title.lower()
    s = snippet.lower()
    
    # Role-based Boosts
    if 'engineer' in t: score += 30
    if 'bi' in t or 'business intelligence' in t: score += 25
    if 'senior' in t or 'sr' in t or 'lead' in t: score += 20
    if 'remote' in s or 'remote' in t: score += 10
    
    # Penalties
    if any(x in t for x in ['intern', 'junior', 'entry', 'student']): score -= 60
    
    return max(0, min(score, 100))

def get_jobs():
    """Simplified search query to maximize lead volume."""
    # We use a flatter query structure which is more reliable for the Serper API
    query = 'Data Analyst OR "Data Engineer" OR "Financial Analyst" OR "BI Analyst" site:lever.co OR site:greenhouse.io'
    
    url = "https://google.serper.dev/search"
    headers = {
        'X-API-KEY': str(SERPER_KEY),
        'Content-Type': 'application/json'
    }
    
    try:
        # Request 40 results to hit that 10-20 lead goal
        response = requests.post(url, headers=headers, json={"q": query, "num": 40})
        data = response.json()
        
        results = data.get('organic', [])
        print(f"📡 Serper Response Received. Raw results found: {len(results)}")
        return results
    except Exception as e:
        print(f"❌ SERPER ERROR: {e}")
        return []

def update_database(new_raw_leads):
    file_path = 'jobs.json'
    
    # 1. Load existing database
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                database = json.load(f)
        except:
            database = []
    else:
        database = []

    # 2. Mark existing jobs as 'Old'
    for job in database:
        job['status'] = 'Old'

    # 3. Process new leads
    existing_urls = {job['url'] for job in database}
    new_found = 0
    
    for lead in new_raw_leads:
        url = lead.get('link')
        if url and url not in existing_urls:
            title = lead.get('title', 'Unknown Role')
            snippet = lead.get('snippet', '')
            
            # Extract a cleaner company name from the title (e.g., "Data Analyst at Stripe")
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
                "score": calculate_score(title, snippet),
                "found_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            existing_urls.add(url)
            new_found += 1

    # 4. Sort by score so the "Best" jobs are always at the top
    database.sort(key=lambda x: x['score'], reverse=True)

    # 5. Save the updated database
    with open(file_path, 'w') as f:
        json.dump(database, f, indent=4)
        
    print(f"💾 {new_found} new jobs added. Total database size: {len(database)}")

if __name__ == "__main__":
    print("🚀 Starting the Hunt...")
    leads = get_jobs()
    update_database(leads)
