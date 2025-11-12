from flask import Flask, request, jsonify
import requests, os, json, datetime

app = Flask(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INTERAKT_API_KEY = os.getenv("INTERAKT_API_KEY")

print("===========================================")
print("🚀 Karuvadukadai WhatsApp AI Bot (Hybrid) Starting...")
print("✅ OpenAI Key Loaded:", "Yes" if OPENAI_API_KEY else "❌ Missing")
print("✅ Interakt Key Loaded:", "Yes" if INTERAKT_API_KEY else "❌ Missing")
print("===========================================")


# ==========================================================
# 🧠 Generate AI Reply
# ==========================================================
def generate_ai_reply(user_message):
    try:
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a friendly Tamil-English chatbot for Karuvadukadai.com. "
                        "Keep replies short, relevant to seafood, dry fish, or delivery help."
                    )
                },
                {"role": "user", "content": user_message}
            ]
        }
        res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        if res.status_code != 200:
            print("❌ OpenAI Error:", res.text)
            return "Server busy bro 😔 Try again later."

        return res.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print("❌ AI Exception:", e)
        return "Error generating reply bro 😔"


# ==========================================================
# 💬 Send session message (inside 24 h window)
# ==========================================================
def send_session_message(mobile, message):
    try:
        url = "https://app.interakt.io/api/public/v2/message/"
        payload = {
            "countryCode": "+91",
            "phoneNumber": str(mobile),
            "callbackData": "karuvadukadai-ai",
            "type": "Text",
            "message": {"text": message}
        }
        headers = {
            "Authorization": f"Basic {INTERAKT_API_KEY}",
            "Content-Type": "application/json"
        }
        r = requests.post(url, headers=headers, json=payload)
        print("📤 Interakt Session Msg Code:", r.status_code)
        print("📤 Response:", r.text)
        return r.status_code == 200
    except Exception as e:
        print("❌ Session Msg Error:", e)
        return False


# ==========================================================
# 📩 Send fallback template (outside 24 h window)
# ==========================================================
def send_template_message(mobile):
    try:
        url = "https://app.interakt.io/api/public/v2/template/"
        payload = {
            "countryCode": "+91",
            "phoneNumber": str(mobile),
            "callbackData": "karuvadukadai-fallback",
            "templateName": "browse_catalog_on_whatsapp",   # 🔁 Replace with your actual template name in Interakt
            "languageCode": "en",
            "parameters": []
        }
        headers = {
            "Authorization": f"Basic {INTERAKT_API_KEY}",
            "Content-Type": "application/json"
        }
        r = requests.post(url, headers=headers, json=payload)
        print("📤 Template Msg Code:", r.status_code)
        print("📤 Template Response:", r.text)
        return r.status_code == 200
    except Exception as e:
        print("❌ Template Send Error:", e)
        return False


# ==========================================================
# 🌊 Webhook Receiver
# ==========================================================
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        print("📩 Incoming Webhook:")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        msg_data = data.get("data", {}).get("message", {})
        cust_data = data.get("data", {}).get("customer", {})

        mobile = cust_data.get("phoneNumber")
        msg_type = (msg_data.get("type") or "").lower()

        # Extract text content
        msg_text = msg_data.get("content")
        if isinstance(msg_text, dict):
            msg_text = msg_text.get("text") or msg_text.get("body")

        print(f"📞 From: {mobile}")
        print(f"💬 Type: {msg_type}")
        print(f"💬 Text Extracted: {msg_text}")

        if not msg_text:
            print("⚠️ No text found, skipping.")
            return jsonify({"status": "ignored"}), 200

        ai_reply = generate_ai_reply(msg_text)

        # Try sending via session first
        success = send_session_message(mobile, ai_reply)
        if not success:
            print("⚠️ Session expired. Sending fallback template.")
            send_template_message(mobile)
        else:
            print("✅ AI reply sent successfully!")

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print("🔥 Webhook Exception:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "active", "bot": "Karuvadukadai AI Hybrid"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
