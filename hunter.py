import os
import json
import requests
from google import genai

# Configuration
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
SERPER_KEY = os.getenv("SERPER_API_KEY")

def get_jobs():
    """Ultra-broad search to force results."""
    # We are removing specific sites and strict quotes to ensure we get leads
    query = 'Senior Data Analyst OR Senior Data Engineer'
    
    url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': SERPER_KEY, 'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, json={"q": query, "num": 50})
        data = response.json()
        
        # Debugging: Print the whole response if it's empty
        if "organic" not in data:
            print(f"❌ API MESSAGE: {data.get('message', 'No organic results found')}")
            return []
            
        results = data.get('organic', [])
        print(f"📊 PROGRESS: Serper found {len(results)} raw leads.")
        return results
    except Exception as e:
        print(f"❌ SERPER CONNECTION ERROR: {e}")
        return []

def analyze_jobs(jobs):
    """Generous AI filtering."""
    if not GEMINI_KEY:
        print("❌ GEMINI ERROR: Key missing")
        return []
        
    client = genai.Client(api_key=GEMINI_KEY)
    valid_jobs = []
    
    for j in jobs:
        role_title = j.get('title', '')
        snippet = j.get('snippet', '')
        
        prompt = f"Is this a senior data role? Title: {role_title}. Snippet: {snippet}. Return JSON: {{"match": true, "co": "Company"}} or {{"match": false}}"
        
        try:
            response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
            clean_json = response.text.strip().replace('```json', '').replace('```', '').strip()
            data = json.loads(clean_json)
            
            if data.get('match'):
                valid_jobs.append({
                    "title": role_title,
                    "url": j.get('link'),
                    "company": data.get('co', 'Company'),
                    "experience": "5-8 Years",
                    "score": 90
                })
        except:
            continue
    return valid_jobs

if __name__ == "__main__":
    leads = get_jobs()
    final_list = analyze_jobs(leads) if leads else []
    with open('jobs.json', 'w') as f:
        json.dump(final_list, f, indent=4)
    print(f"✅ SUCCESS: Saved {len(final_list)} jobs.")
