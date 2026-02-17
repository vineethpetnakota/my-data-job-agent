import os
import json
import requests
from google import genai

# Config - Matches your GitHub Secrets
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
SERPER_KEY = os.getenv("SERPER_API_KEY")

def get_jobs():
    """Broad search to ensure Google/Serper actually returns leads."""
    # This query captures broad 'Senior' roles across major ATS platforms
    query = 'Senior (Data Analyst OR Data Engineer) (site:lever.co OR site:greenhouse.io OR site:ashbyhq.com)'
    
    url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': str(SERPER_KEY), 'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, json={"q": query, "num": 40})
        data = response.json()
        results = data.get('organic', [])
        print(f"📊 PROGRESS: Serper found {len(results)} raw leads.")
        return results
    except Exception as e:
        print(f"❌ SERPER ERROR: {e}")
        return []

def analyze_jobs(jobs):
    """Filters roles with a focus on 'Seniority' while being flexible on snippets."""
    if not GEMINI_KEY:
        print("❌ GEMINI ERROR: Key missing")
        return []
        
    client = genai.Client(api_key=GEMINI_KEY)
    valid_jobs = []
    
    print(f"🧠 AI is screening {len(jobs)} leads for the 5-8 year sweet spot...")
    
    for j in jobs:
        role_title = j.get('title', '')
        snippet = j.get('snippet', '')
        
        # PROMPT: We use {{ }} for JSON so Python f-strings don't crash.
        prompt = f"""
        Analyze this job lead:
        Title: {role_title}
        Snippet: {snippet}

        CRITERIA:
        - Target: Senior Data roles (approx 5-9 years experience).
        - REJECT if: Title is Junior, Intern, or Director/VP.
        - ACCEPT if: Title is Senior/Staff/Lead/III/IV, even if years aren't in snippet.

        Return ONLY valid JSON: {{"match": true, "co": "Company Name"}} or {{"match": false}}
        """
        
        try:
            # Using 1.5-flash for maximum reliability/speed on the Free tier
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
            # If AI fails on one job, skip to the next
            continue
            
    print(f"✅ SUCCESS: Gemini approved {len(valid_jobs)} jobs.")
    return valid_jobs

if __name__ == "__main__":
    print("🚀 Starting the Hunt...")
    raw_leads = get_jobs()
    
    # Process the leads and save them
    final_list = analyze_jobs(raw_leads) if raw_leads else []
    
    with open('jobs.json', 'w') as f:
        json.dump(final_list, f, indent=4)
        
    print(f"💾 File updated: {len(final_list)} jobs saved. Ready for dashboard.")
