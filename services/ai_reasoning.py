import os
from openai import OpenAI
from dotenv import load_dotenv

# Load the API key from the .env file
load_dotenv()

# Initialize the client pointing to xAI's API
client = OpenAI(
    api_key=os.getenv("GROK_API_KEY"),
    base_url="https://api.x.ai/v1",
)

def generate_ai_explanation(data):
    prompt = f"""
    You are an expert fraud analyst for government documents. 
    Analyze the following verification findings and write a concise, 2-3 sentence risk summary.
    
    FINDINGS:
    - Extracted Reference Number: {data.get('extracted_ref')}
    - Database Record Found: {data.get('db_match')}
    - Date Match: {data.get('date_match')}
    - Image Tamper Score: {data.get('tamper_score')}/100
    - Has Blockchain Provenance: {data.get('hash_match')}

    Start with a bold one-line verdict (e.g., "🔴 HIGH RISK:" or "🟢 VERIFIED:"). 
    Keep the tone factual and professional.
    """

    try:
        response = client.chat.completions.create(
            model="grok-beta", # You can also use grok-2-mini if available
            messages=[
                {"role": "system", "content": "You are a senior fraud detection API."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2, # Low temperature for factual, reliable outputs
            max_tokens=150
        )
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"Grok API Error: {e}")
        # Fallback if internet drops during your buildathon demo
        if not data['db_match']: 
            return "🔴 HIGH RISK: Reference number not found in official database."
        if data['tamper_score'] > 45: 
            return f"🔴 HIGH RISK: Visual tampering detected (Score: {data['tamper_score']})."
        return "🟢 VERIFIED: Document matches official records with no visible tampering."