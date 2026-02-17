import os
import json
import requests
from google import genai

# Config
SERPER_KEY = os.getenv("SERPER_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

def get_jobs():
    """Fetches 20 raw leads from Google/Serper."""
    query = 'intitle:"Data Analyst" (site:boards.greenhouse.io OR site:jobs.lever.co)'
    url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': str(SERPER_KEY), 'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, json={"q": query, "num": 20})
        return response.json().get('organic', [])
    except:
        return []

def process_with_ai(raw_leads):
    """Uses Gemini to identify the Company and filter out non-data roles."""
    if not GEMINI_KEY:
        print("❌ Gemini Key missing!")
        return []

    client = genai.Client(api_key=GEMINI_KEY)
    final_jobs = []

    for lead in raw_leads:
        title = lead.get('title', 'Unknown Title')
        snippet = lead.get('snippet', '')
        
        # Simple Prompt: Just Company extraction + Verification
        prompt = f"""
        Analyze this job lead:
        Title: {title}
        Snippet: {snippet}

        1. Is this actually a Data Analyst or Data Engineer role?
        2. What is the Company Name?

        Return ONLY JSON: {{"match": true, "company": "Name"}} or {{"match": false}}
        """

        try:
            response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
            # Clean the AI response to get pure JSON
            res_text = response.text.strip().replace('```json', '').replace('```', '').strip()
            data = json.loads(res_text)

            if data.get("match") is True:
                final_jobs.append({
                    "title": title,
                    "url": lead.get('link'),
                    "company": data.get("company", "Unknown"),
                    "experience": "Checking...", # We will add this in Phase 2!
                    "score": 100
                })
        except:
            continue
            
    return final_jobs

if __name__ == "__main__":
    print("🚀 Running AI-Categorized Pipeline...")
    raw = get_jobs()
    if raw:
        processed = process_with_ai(raw)
        with open('jobs.json', 'w') as f:
            json.dump(processed, f, indent=4)
        print(f"✅ Success! {len(processed)} jobs verified by AI.")
