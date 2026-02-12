import os
import json
import requests
import time
from google import genai

# Setup API Keys from GitHub Secrets
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
SERPER_KEY = os.getenv("SERPER_API_KEY")

def get_jobs():
    """Search for Senior Analyst and Engineer roles (5+ years exp)"""
    # Added "Senior" and "Lead" to the query to target experienced roles
    query = '("Senior Data Analyst" OR "Senior Data Engineer" OR "Lead Data Engineer" OR "Data Architect") (site:myworkdayjobs.com OR site:icims.com OR site:boards.greenhouse.io OR site:jobs.lever.co OR site:jobs.ashbyhq.com OR site:smartrecruiters.com OR site:workable.com)'
    
    url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': SERPER_KEY, 'Content-Type': 'application/json'}
    
    try:
        # Pull 50 results to ensure we find enough senior-specific roles
        response = requests.post(url, headers=headers, json={"q": query, "num": 50})
        return response.json().get('organic', [])
    except Exception as e:
        print(f"Search failed: {e}")
        return []

def analyze_jobs(jobs):
    """Uses Gemini to filter for 5+ years experience and relevant titles"""
    if not GEMINI_KEY:
        print("Error: GEMINI_API_KEY missing.")
        return []
        
    client = genai.Client(api_key=GEMINI_KEY)
    valid_jobs = []
    
    for j in jobs:
        role_title = j.get('title', 'Unknown')
        snippet = j.get('snippet', '')
        link = j.get('link')

        # Strict prompt for 5+ years experience
        prompt = f"""
        Role: {role_title}
        Snippet: {snippet}
        
        Task: Is this a Senior/Lead Data Analyst or Data Engineering role requiring 5+ years of experience?
        - If the snippet implies a junior/entry-level role, match is false.
        - If it's a senior role or requires significant experience (5+ years), match is true.
        
        Return ONLY JSON: {{"match": true, "score": 95, "co": "Company Name"}}. 
        If no match, return: {{"match": false}}.
        """
        
        try:
            response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            clean_json = response.text.strip().replace('```json', '').replace('```', '').strip()
            data = json.loads(clean_json)
            
            if data.get('match') is True:
                valid_jobs.append({
                    "title": role_title,
                    "url": link,
                    "score": data.get('score', 90),
                    "company": data.get('co', 'Hiring Company')
                })
            
            time.sleep(0.5) # Avoid rate limits
            
        except Exception:
            continue
            
    return valid_jobs

if __name__ == "__main__":
    print("🚀 Starting Senior Job Hunter...")
    raw_results = get_jobs()
    print(f"🔍 Found {len(raw_results)} potential senior leads.")
    
    final_matches = analyze_jobs(raw_results)
    
    with open('jobs.json', 'w') as f:
        json.dump(final_matches, f, indent=4)
        
    print(f"✅ Done! Saved {len(final_matches)} senior matches to jobs.json.")
