# ai_analyzer_local.py

import openai
import json

client = openai.OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

def analyze_hazard_local(complaint_type, descriptor):
    """Uses a local LLM via Ollama to score and categorize a 311 complaint."""
    
    # --- UPDATED PROMPT ---
    prompt = f"""
    You are a safety analyst for an app called SafetyGPT. Your job is to assess the potential danger or disruption of a 311 report in NYC.
    
    Analyze the following report and provide ONLY a single, valid JSON object with 'score' (an integer from 1 to 10) and 'category'.
    
    Possible categories are: "Noise", "Road Hazard", "Utility Issue", "Crime/Safety Concern", "Sanitation", "Encampment/Assistance Call", "Other".
    
    Report Details:
    - Complaint Type: "{complaint_type}"
    - Descriptor: "{descriptor}"
    
    JSON Response:
    """
    
    try:
        response = client.chat.completions.create(
            model="llama3:8b", 
            messages=[
                {"role": "system", "content": "You are a helpful safety analyst that only outputs valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"} 
        )
        
        result_text = response.choices[0].message.content
        return json.loads(result_text)
        
    except Exception as e:
        print(f"Error with local Ollama model: {e}")
        return {"score": 1, "category": "Uncategorized"}

# --- Add a test for the new type ---
if __name__ == '__main__':
    print("Testing local LLM analysis. Make sure Ollama is running.")
    
    test_homeless = analyze_hazard_local("Homeless Encampment", "Group of 10-15 individuals with tents and structures on sidewalk.")
    print(f"Test (Encampment): {test_homeless}")