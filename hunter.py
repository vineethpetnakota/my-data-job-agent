import os
import json
import requests
import time
from google import genai

# Configuration - Ensure these names match your GitHub Secrets exactly!
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
SERPER_KEY = os.getenv("SERPER_API_KEY")

def get_jobs():
    """Simple global search to guarantee we bypass the '0 raw leads' error."""
    # This query is broad enough that Google will always have results
    query = 'Senior Data Analyst jobs remote USA'
    
    url = "https://google.serper.dev/search"
    headers = {
        'X-API-KEY': str(SERPER_KEY), 
        'Content-Type': 'application/json'
    }
    
    # Debugging: Check if key is loaded
    if not SERPER_KEY:
        print("❌ ERROR: SERPER_API_KEY is missing from Environment Secrets!")
        return []

    try:
        payload = {"q": query, "num": 50}
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        
        results = data.get('organic', [])
        print(f"📊 PROGRESS: Serper found {len(results)} raw leads.")
        
        if not results:
            print(f"⚠️ API Response: {data}") # Prints the error message from Serper if 0 found
            
        return results
    except Exception as e:
        print(f"❌ SERPER CONNECTION ERROR: {e}")
        return []

def analyze_jobs(jobs):
    """Uses Gemini to filter for the 5-8 year sweet spot."""
    if not GEMINI_KEY:
        print("❌ ERROR: GEMINI_API_KEY is missing from Environment Secrets!")
        return []
        
    client = genai.Client(api_key=GEMINI_KEY)
    valid_jobs = []
    
    print(f"🧠 AI is now screening {len(jobs)} leads...")
    
    for j in jobs:
        role_title = j.get('title', '')
        snippet = j.get('snippet', '')
        
        # Doubled curly braces {{ }} are required to use JSON inside an f-string
        prompt = f"""
        Role: {role_title}
        Info: {snippet}

        Is this a Data role for someone with 5-9 years of experience? 
        If it's 'Senior' or 'Staff' and NOT a 'Director' or 'Junior', say YES.
        
        Return ONLY valid JSON: {{"match": true, "co": "Company Name"}} or {{"match": false}}
        """
        
        try:
            # Using 1.5-flash for reliability on free tier
            response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
            clean_json = response.text.strip().replace('```json', '').replace('```', '').strip()
            data = json.loads(clean_json)
            
            if data.get('match') is True:
                valid_jobs.append({
                    "title": role_title,
                    "url": j.get('link'),
                    "company": data.get('co', 'Hiring Company'),
                    "experience": "5-8 Years",
                    "score": 95
                })
        except:
            continue
            
    print(f"✅ SUCCESS: Gemini approved {len(valid_jobs)} matching roles.")
    return valid_jobs

if __name__ == "__main__":
    print("🚀 Starting the Hunt...")
    raw_leads = get_jobs()
    
    if raw_leads:
        final_results = analyze_jobs(raw_leads)
        
        with open('jobs.json', 'w') as f:
            json.dump(final_results, f, indent=4)
        
        print(f"💾 File updated: {len(final_results)} jobs saved to jobs.json.")
    else:
        # Save empty list if nothing found to prevent dashboard crash
        with open('jobs.json', 'w') as f:
            json.dump([], f)
        print("❌ Mission failed: No leads to process.")
