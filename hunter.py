import os
import json
import requests
import time
from google import genai

# Configuration from GitHub Secrets
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
SERPER_KEY = os.getenv("SERPER_API_KEY")

def get_jobs():
    """Broadens the search to ensure Serper finds leads for the AI to filter."""
    # Removed strict quotes and numeric ranges to increase search volume
    query = 'Senior (Data Analyst OR Data Engineer OR Analytics Engineer) (site:lever.co OR site:greenhouse.io OR site:jobs.ashbyhq.com)'
    
    url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': SERPER_KEY, 'Content-Type': 'application/json'}
    
    try:
        # Requesting 100 leads to give the AI a large pool to scan
        response = requests.post(url, headers=headers, json={"q": query, "num": 100})
        results = response.json().get('organic', [])
        print(f"DEBUG: Serper found {len(results)} potential senior leads.")
        return results
    except Exception as e:
        print(f"ERROR: Search failed - {e}")
        return []

def analyze_jobs(jobs):
    """Uses Gemini to filter roles based on experience in the snippet."""
    if not GEMINI_KEY:
        print("ERROR: GEMINI_API_KEY missing.")
        return []
        
    client = genai.Client(api_key=GEMINI_KEY)
    valid_jobs = []
    
    for j in jobs:
        role_title = j.get('title', '')
        snippet = j.get('snippet', '')
        
        # This prompt is the 'Brain'. It handles the 5-8 year logic.
        prompt = f"""
        Analyze this job lead: {role_title} - {snippet}
        
        CRITERIA:
        1. Target experience: 5 to 9 years. 
        2. If the snippet doesn't mention years, but the title is "Senior" or "Staff", consider it a match.
        3. REJECT if it explicitly says "Junior", "Entry", "Intern", or "10+ years" / "Principal" / "Director".
        
        If it's a match, return ONLY this JSON format: 
        {{"match": true, "exp": "5-8 Years", "co": "Company Name", "score": 95}}
        Otherwise, return {{"match": false}}
        """
        
        try:
            response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            # Cleaning the AI output to ensure it's pure JSON
            clean_json = response.text.strip().replace('```json', '').replace('```', '').strip()
            data = json.loads(clean_json)
            
            if data.get('match') is True:
                valid_jobs.append({
                    "title": role_title,
                    "url": j.get('link'),
                    "company": data.get('co', 'Hiring Company'),
                    "experience": data.get('exp', '5-8+ Years'),
                    "score": data.get('score', 90)
                })
            
            # Tiny sleep to avoid hitting API rate limits
            time.sleep(0.5) 
            
        except Exception as e:
            # Skip if there's an AI error or invalid JSON
            continue
            
    return valid_jobs

if __name__ == "__main__":
    print("🚀 Starting the Senior Data Job Hunt...")
    raw_leads = get_jobs()
    
    if raw_leads:
        final_list = analyze_jobs(raw_leads)
        
        with open('jobs.json', 'w') as f:
            json.dump(final_list, f, indent=4)
        
        print(f"✅ Mission Complete: Saved {len(final_list)} matching jobs to jobs.json.")
    else:
        print("⚠️ No leads found by Serper. Check API key or search query.")
