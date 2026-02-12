import os
import json
import requests
import time
from google import genai

# Configuration from GitHub Secrets
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
SERPER_KEY = os.getenv("SERPER_API_KEY")

def get_jobs():
    """Fetches job leads specifically targeting 5-8 years of experience."""
    # The '5..8 years' operator tells Google to find any number between 5 and 8.
    query = '("Data Analyst" OR "Data Engineer") "5..8 years" (site:lever.co OR site:greenhouse.io OR site:jobs.ashbyhq.com)'
    
    url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': SERPER_KEY, 'Content-Type': 'application/json'}
    
    try:
        # Requesting 100 leads to maximize the pool for the specific 5-8yr range
        response = requests.post(url, headers=headers, json={"q": query, "num": 100})
        results = response.json().get('organic', [])
        print(f"DEBUG: Serper found {len(results)} leads targeting the 5-8yr range.")
        return results
    except Exception as e:
        print(f"ERROR: Search failed - {e}")
        return []

def analyze_jobs(jobs):
    """Filters roles and extracts specific years of experience."""
    if not GEMINI_KEY:
        print("ERROR: GEMINI_API_KEY missing.")
        return []
        
    client = genai.Client(api_key=GEMINI_KEY)
    valid_jobs = []
    
    for j in jobs:
        role_title = j.get('title', 'Unknown')
        snippet = j.get('snippet', '')
        
        # We instruct Gemini to categorize the experience specifically
        prompt = f"""
        Role: {role_title}
        Info: {snippet}
        
        Task: 
        1. Does this role require 5-8 years of experience? (5+, 6+, 7+, or 8+ matches).
        2. If it's a match, return JSON: 
           {{"match": true, "exp": "7+ Years", "co": "Company Name", "score": 95}}
        3. If it's entry-level, junior, or requires 10+ years, match is false.
        
        Return ONLY valid JSON.
        """
        
        try:
            response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            clean_json = response.text.strip().replace('```json', '').replace('```', '').strip()
            data = json.loads(clean_json)
            
            if data.get('match') is True:
                valid_jobs.append({
                    "title": role_title,
                    "url": j.get('link'),
                    "company": data.get('co', 'Hiring Company'),
                    "experience": data.get('exp', '5-8 Years'), # New Field
                    "score": data.get('score', 90)
                })
            
            time.sleep(0.5) # Protect API quota
            
        except Exception:
            continue
            
    return valid_jobs

if __name__ == "__main__":
    print("🚀 Hunting for 5-8 Year Data Roles...")
    raw_leads = get_jobs()
    
    if raw_leads:
        final_list = analyze_jobs(raw_leads)
        
        with open('jobs.json', 'w') as f:
            json.dump(final_list, f, indent=4)
        
        print(f"✅ Mission Complete: Saved {len(final_list)} jobs.")
    else:
        print("⚠️ No leads found. Check Serper API credits.")
