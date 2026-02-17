import os
import json
import requests
from google import genai

# Configuration - Matches your GitHub Secrets
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
SERPER_KEY = os.getenv("SERPER_API_KEY")

def get_jobs():
    """Tries a high-quality search, then falls back to global if 0 results found."""
    # Attempt 1: Targeted search for quality job boards
    query = 'Senior "Data Analyst" (site:greenhouse.io OR site:lever.co)'
    
    url = "https://google.serper.dev/search"
    headers = {
        'X-API-KEY': str(SERPER_KEY), 
        'Content-Type': 'application/json'
    }

    if not SERPER_KEY:
        print("❌ ERROR: SERPER_API_KEY not found in environment.")
        return []

    try:
        response = requests.post(url, headers=headers, json={"q": query, "num": 30})
        data = response.json()
        results = data.get('organic', [])

        # FALLBACK: If specific sites are empty, search the whole web
        if not results:
            print("⚠️ Targeted search found 0. Falling back to global search...")
            fallback_query = 'Senior Data Analyst jobs USA remote'
            response = requests.post(url, headers=headers, json={"q": fallback_query, "num": 20})
            results = response.json().get('organic', [])

        print(f"📊 PROGRESS: Serper found {len(results)} raw leads.")
        return results
    except Exception as e:
        print(f"❌ SERPER CONNECTION ERROR: {e}")
        return []

def analyze_jobs(jobs):
    """Uses Gemini to filter roles, being generous with senior job titles."""
    if not GEMINI_KEY:
        print("❌ GEMINI ERROR: Key missing.")
        return []
        
    client = genai.Client(api_key=GEMINI_KEY)
    valid_jobs = []
    
    print(f"🧠 AI is screening {len(jobs)} leads...")
    
    for j in jobs:
        role_title = j.get('title', '')
        snippet = j.get('snippet', '')
        
        # PROMPT: Instructs AI to be more flexible on senior titles
        prompt = f"""
        Analyze this job lead:
        Title: {role_title}
        Info: {snippet}

        CRITERIA:
        - Target: Senior Data roles (5-9 years experience).
        - ACCEPT if title has 'Senior', 'Lead', 'Staff', or 'III/IV'.
        - REJECT if title is 'Junior', 'Intern', or 'Entry'.
        - Be flexible: if snippet is vague but title is 'Senior', say YES.

        Return ONLY JSON: {{"match": true, "co": "Company Name"}} or {{"match": false}}
        """
        
        try:
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
            
    print(f"✅ SUCCESS: Gemini approved {len(valid_jobs)} jobs.")
    return valid_jobs

if __name__ == "__main__":
    print("🚀 Starting the Hunt...")
    leads = get_jobs()
    
    # Process and save even if empty to keep the dashboard valid
    final_list = analyze_jobs(leads) if leads else []
    
    with open('jobs.json', 'w') as f:
        json.dump(final_list, f, indent=4)
        
    print(f"💾 File updated: {len(final_list)} jobs saved.")
