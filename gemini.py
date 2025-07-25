import requests, os

def ask_gemini(question, context):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    key = os.getenv("GEMINI_API_KEY")
    data = {
        "contents": [{
            "parts": [{"text": f"Context: {context}\n\nQuestion: {question}"}]
        }]
    }
    res = requests.post(f"{url}?key={key}", json=data, headers={"Content-Type": "application/json"})
    return res.json()['candidates'][0]['content']['parts'][0]['text']