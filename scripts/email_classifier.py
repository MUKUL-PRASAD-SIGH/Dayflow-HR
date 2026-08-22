import google.generativeai as genai
import json

# Setup API key
import os
genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))

def classify_emails_with_gemini(emails):
    model = genai.GenerativeModel('gemini-1.5-flash')  # ✅ Correct model name

    prompt = (
        "Classify the following emails into Important, General, or Spam accoring to this rules:- Important: Emails related to job, urgent tasks, password reset, deadlines.General: Newsletters, updates, regular known conversations.Spam: Promotions, advertisements, unknown senders, unwanted content.\n\n"
    )
    for i, email in enumerate(emails, 1):
        prompt += f"Email {i}: {email}\n"

    prompt += "\n\nReturn only a valid JSON like this:\n{\"Important\": [1], \"General\": [2], \"Spam\": [3]}"

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        print("Gemini response:\n", response.text)

        if text.startswith("```json"):
            text = text.replace("```json", "").replace("```", "").strip()

        classification = json.loads(text)
        important_emails = [emails[i - 1] for i in classification.get("Important", []) if 1 <= i <= len(emails)]
        general_emails  = [emails[i - 1] for i in classification.get("General", []) if 1 <= i <= len(emails)]
        spam_emails      = [emails[i - 1] for i in classification.get("Spam", []) if 1 <= i <= len(emails)]
        
        return {
            "Important": important_emails,
            "General": general_emails,
            "Spam": spam_emails
        }

        

    except Exception as e:
        print("Error during Gemini classification:", e)
        return {"Important": [], "General": [], "Spam": []}
