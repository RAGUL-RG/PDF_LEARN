import requests
import os

def ask_gemini(question, context):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("Missing GEMINI_API_KEY in environment variables.")

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{"text": f"Context: {context}\n\nQuestion: {question}"}]
        }]
    }

    try:
        response = requests.post(f"{url}?key={key}", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data['candidates'][0]['content']['parts'][0]['text']
    except requests.exceptions.RequestException as e:
        return f"Error contacting Gemini API: {e}"
    except (KeyError, IndexError):
        return "Error: Unexpected response format from Gemini API."
