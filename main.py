from flask import Flask, request, jsonify
import requests, os

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
                    "content": "You are a helpful Tamil-English assistant for Karuvadukadai.com. Reply naturally, friendly, short, and relevant to dry fish, seafood, or delivery questions."
                },
                {"role": "user", "content": user_message}
            ]
        }

        res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        if res.status_code != 200:
            print("❌ OpenAI Error:", res.text)
            return "Server busy bro 😔 Please try again later."

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
        print("📤 Interakt v2 Response Code:", response.status_code)
        print("📤 Interakt v2 Response:", response.text)

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
        data = request.get_json()
        print("📩 Incoming Webhook:")
        print(data)

        # Extract message details
        event = data.get("event", "")
        message_data = data.get("data", {}).get("message", {})
        customer_data = data.get("data", {}).get("customer", {})

        mobile = customer_data.get("phoneNumber")
        message_type = message_data.get("type", "").lower()
        message_text = message_data.get("content")

        # Detect actual message content
        if not message_text:
            print("⚠️ No text message found, skipping.")
            return jsonify({"status": "ignored"}), 200

        print(f"📞 From: {mobile}")
        print(f"💬 Message Type: {message_type}")
        print(f"💬 Message Text: {message_text}")

        # Skip system/template/campaign messages
        if message_type not in ["text"]:
            print("⏸ Ignored non-text or campaign message.")
            return jsonify({"status": "ignored"}), 200

        # Generate AI reply
        ai_reply = generate_ai_reply(message_text)

        # Send reply via Interakt v2 API
        sent = send_whatsapp_message(mobile, ai_reply)

        if sent:
            print("✅ AI Reply sent to", mobile)
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
        "message": "Karuvadukadai WhatsApp AI Bot (v2 Interakt) ✅"
    })


# ==========================================================
# 🚀 Run App
# ==========================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
