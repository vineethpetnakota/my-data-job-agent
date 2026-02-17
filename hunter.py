import os
import json
import requests
import time
from google import genai

# Configuration
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
SERPER_KEY = os.getenv("SERPER_API_KEY")

def get_jobs():
    """Uses a very broad query to force Google to return 100 leads."""
    # Removed all strict 'site:' filters for one run to see if we get hits
    # Searching major boards + general senior data roles
    query = 'Senior "Data Analyst" OR "Data Engineer" (site:lever.co OR site:greenhouse.io OR site:ashbyhq.com)'
    
    url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': SERPER_KEY, 'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, json={"q": query, "num": 100})
        results = response.json().get('organic', [])
        print(f"📊 PROGRESS: Serper found {len(results)} raw leads.")
        return results
    except Exception as e:
        print(f"❌ SERPER ERROR: {e}")
        return []

def analyze_jobs(jobs):
    """Extremely generous AI filtering to ensure results appear."""
    if not GEMINI_KEY:
        print("❌ GEMINI ERROR: Key missing")
        return []
        
    client = genai.Client(api_key=GEMINI_KEY)
    valid_jobs = []
    
    print("🧠 AI is analyzing leads...")
    for j in jobs:
        role_title = j.get('title', '')
        snippet = j.get('snippet', '')
        
        prompt = f"""
        Job: {role_title}
        Snippet: {snippet}
        
        Is this a Senior Data role? (Target 5-8 years, but accept anything 'Senior').
        Return ONLY JSON: {{"match": true, "co": "Company Name", "score": 90}} or {{"match": false}}
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
                    "experience": "5-8+ Years",
                    "score": data.get('score', 95)
                })
        except:
            continue
            
    print(f"✅ SUCCESS: Gemini approved {len(valid_jobs)} jobs.")
    return valid_jobs

if __name__ == "__main__":
    leads = get_jobs()
    if leads:
        final_list = analyze_jobs(leads)
        with open('jobs.json', 'w') as f:
            json.dump(final_list, f, indent=4)
        print("💾 File saved. Check your dashboard in 1 minute.")
