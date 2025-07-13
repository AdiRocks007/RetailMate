import requests
import json

def call_ollama_model(prompt, model_name):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.3,
                "max_tokens": 512
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()["response"]
        else:
            return None
    except Exception as e:
        print(f"Error calling {model_name}: {e}")
        return None

def classify_user_query(user_input: str):
    # Your few-shot prompt (trimmed for clarity)
    prompt = f"""
You are RetailMate, an AI-powered shopping assistant. Your job is to classify user queries into structured data for smart shopping recommendations.

Use the format:
{{
  "intent": "...",
  "category": "...",
  "mood": "...",
  "event": "...",
  "urgency": "...",
  "action": "..."
}}

Examples:

---

User: "My best friend's birthday is coming up next week. Need gift suggestions!"
Output:
{{
  "intent": "gift_recommendation",
  "category": null,
  "mood": null,
  "event": "birthday",
  "urgency": "medium",
  "action": "recommend"
}}

---

User: "Feeling kind of low today... I want to treat myself to something nice"
Output:
{{
  "intent": "mood_based_suggestion",
  "category": "self-care",
  "mood": "sad",
  "event": null,
  "urgency": "low",
  "action": "recommend"
}}

---

User: "I have a beach vacation next week — help me pack stylish outfits"
Output:
{{
  "intent": "event_outfit_planning",
  "category": "clothing",
  "mood": "excited",
  "event": "vacation",
  "urgency": "medium",
  "action": "recommend"
}}

---

User: "I want to reorder the shampoo I bought last month"
Output:
{{
  "intent": "product_reorder",
  "category": "personal_care",
  "mood": null,
  "event": null,
  "urgency": "low",
  "action": "reorder"
}}

---

User: "Any discounts on headphones today?"
Output:
{{
  "intent": "deal_lookup",
  "category": "electronics",
  "mood": null,
  "event": null,
  "urgency": "high",
  "action": "search"
}}

---

User: "What can you do?"
Output:
{{
  "intent": "assistant_help",
  "category": null,
  "mood": null,
  "event": null,
  "urgency": "low",
  "action": "explain"
}}

---

User: "{user_input}"
Output:
"""

    # Try with primary model
    primary_model = "qwen2.5:3b"
    fallback_model = "llama3"

    response = call_ollama_model(prompt, primary_model)
    if response:
        print(f"Primary model ({primary_model}) succeeded.")
        return response.strip()

    print(f"Falling back to {fallback_model}...")
    response = call_ollama_model(prompt, fallback_model)
    if response:
        print(f"Fallback model ({fallback_model}) succeeded.")
        return response.strip()

    return "Both models failed to respond."

# Example use
if __name__ == "__main__":
    query = input("Enter user query: ")
    print("\Classified Output:\n", classify_user_query(query))
