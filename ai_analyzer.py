import openai

# Replace with your actual API key
# openai.api_key = 'YOUR_OPENAI_API_KEY'

def analyze_hazard(complaint_type, descriptor):
    """Uses GPT to score and categorize a 311 complaint."""
    
    prompt = f"""
    You are a safety analyst for an app called SafetyGPT. Your job is to assess the potential danger of a 311 report in NYC.
    
    Analyze the following report and provide a JSON object with 'score' (an integer from 1 to 10, where 1 is a minor inconvenience and 10 is a severe, immediate danger) and 'category' (e.g., "Noise", "Road Hazard", "Utility Issue", "Crime/Safety Concern", "Sanitation").
    
    Report Details:
    - Complaint Type: "{complaint_type}"
    - Descriptor: "{descriptor}"
    
    JSON Response:
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful safety analyst outputting JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1 # Low temperature for consistent output
        )
        # The response will be a JSON string, we need to parse it.
        result = response.choices[0].message['content']
        import json
        return json.loads(result)
    except Exception as e:
        print(f"Error with OpenAI API: {e}")
        # Return a default low-risk score on error
        return {"score": 1, "category": "Uncategorized"}


# --- Test it ---
if __name__ == '__main__':
    # Example 1: Low risk
    test1 = analyze_hazard("Noise - Residential", "Loud Music/Party")
    print(f"Test 1 (Loud Party): {test1}")
    
    # Example 2: High risk
    test2 = analyze_hazard("UNSANITARY CONDITION", "Harboring Pests")
    print(f"Test 2 (Pests): {test2}")
    
    # Example 3: Very high risk
    test3 = analyze_hazard("Safety", "Report of a Gas Leak")
    print(f"Test 3 (Gas Leak): {test3}")