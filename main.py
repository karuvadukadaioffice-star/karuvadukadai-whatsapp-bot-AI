from flask import Flask, request, jsonify
import requests, os, json

app = Flask(__name__)

# ==========================================================
# 🔑 Environment Keys
# ==========================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INTERAKT_API_KEY = os.getenv("INTERAKT_API_KEY")

print("===========================================")
print("🚀 Karuvadukadai WhatsApp AI Bot Starting...")
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
                        "Keep replies short, relevant to seafood, dry fish, or delivery."
                    )
                },
                {"role": "user", "content": user_message}
            ]
        }
        res = requests.post("https://api.openai.com/v1/chat/completions",
                            headers=headers, json=data)
        print("🧠 OpenAI Response Code:", res.status_code)
        if res.status_code != 200:
            print("❌ OpenAI Error:", res.text)
            return "Server busy bro 😔 Try again later."

        reply = res.json()["choices"][0]["message"]["content"]
        print("🧠 AI Reply Generated:", reply)
        return reply

    except Exception as e:
        print("❌ AI Exception:", e)
        return "Error generating reply bro 😔"


# ==========================================================
# 💬 Send WhatsApp Message via Interakt v2 API
# ==========================================================
def send_whatsapp_message(mobile, message):
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
        response = requests.post(url, headers=headers, json=payload)
        print("📤 Interakt Response Code:", response.status_code)
        print("📤 Interakt Response:", response.text)
        return response.status_code == 200
    except Exception as e:
        print("❌ Interakt Send Error:", e)
        return False


# ==========================================================
# 🌊 Webhook Receiver
# ==========================================================
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        print("📩 Incoming Webhook Raw:")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        customer = data.get("data", {}).get("customer", {})
        msg_obj = data.get("data", {}).get("message", {})

        mobile = customer.get("phoneNumber")
        msg_type = (msg_obj.get("type") or "").lower()

        # Try multiple possible paths for content
        msg_text = msg_obj.get("content")
        if isinstance(msg_text, dict):
            msg_text = msg_text.get("text") or msg_text.get("body")

        print(f"📞 From: {mobile}")
        print(f"💬 Type: {msg_type}")
        print(f"💬 Text Extracted: {msg_text}")

        if not msg_text:
            print("⚠️ No text content found, skipping.")
            return jsonify({"status": "ignored"}), 200

        if msg_type not in ["text"]:
            print("⏸ Non-text message ignored.")
            return jsonify({"status": "ignored"}), 200

        ai_reply = generate_ai_reply(msg_text)
        sent = send_whatsapp_message(mobile, ai_reply)

        if sent:
            print("✅ AI reply sent to", mobile)
        else:
            print("❌ Failed to send AI reply")

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print("🔥 Webhook Exception:", e)
        return jsonify({"error": str(e)}), 500


# ==========================================================
# 🏠 Home
# ==========================================================
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "active",
        "message": "Karuvadukadai WhatsApp AI Bot (universal Interakt) ✅"
    })


# ==========================================================
# 🚀 Run App
# ==========================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
