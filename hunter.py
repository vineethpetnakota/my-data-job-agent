import os
import json
import requests

# We only need Serper for this stage
SERPER_KEY = os.getenv("SERPER_API_KEY")

def get_jobs():
    """Simple, broad search for Data Analyst roles on specific ATS boards."""
    # This query searches Greenhouse and Lever for any 'Data Analyst' title.
    query = 'intitle:"Data Analyst" (site:boards.greenhouse.io OR site:jobs.lever.co)'
    
    url = "https://google.serper.dev/search"
    headers = {
        'X-API-KEY': str(SERPER_KEY),
        'Content-Type': 'application/json'
    }

    try:
        # Requesting 20 leads just to verify the dashboard
        response = requests.post(url, headers=headers, json={"q": query, "num": 20})
        data = response.json()
        results = data.get('organic', [])
        
        # We manually format the results into your JSON structure 
        # without using AI for now.
        formatted_jobs = []
        for r in results:
            formatted_jobs.append({
                "title": r.get('title'),
                "url": r.get('link'),
                "company": "Found on Google", # Simplified for testing
                "experience": "Unfiltered",
                "score": 100
            })
            
        print(f"📊 PROGRESS: Found {len(formatted_jobs)} raw leads.")
        return formatted_jobs
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return []

if __name__ == "__main__":
    print("🚀 Running Pure Pipeline Test...")
    jobs = get_jobs()
    
    with open('jobs.json', 'w') as f:
        json.dump(jobs, f, indent=4)
        
    print(f"💾 File updated: {len(jobs)} jobs saved to jobs.json.")
