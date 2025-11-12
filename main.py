from flask import Flask, request, jsonify
import requests, os

app = Flask(__name__)

# ==========================================================
# 🔑 Environment Keys
# ==========================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INTERAKT_API_KEY = os.getenv("INTERAKT_API_KEY")

print("===========================================")
print("🚀 Starting Karuvadukadai WhatsApp AI Bot...")
print("✅ OpenAI Key Loaded:", "Yes" if OPENAI_API_KEY else "❌ Missing")
print("✅ Interakt Key Loaded:", "Yes" if INTERAKT_API_KEY else "❌ Missing")
print("===========================================")


# ==========================================================
# 🧠 AI Reply using OpenAI
# ==========================================================
def generate_ai_reply(user_message):
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }

        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a friendly Tamil-English chatbot for Karuvadukadai.com. Keep replies short, casual, and relevant to dry fish, seafood, and delivery topics."
                },
                {"role": "user", "content": user_message}
            ]
        }

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        print("🧠 OpenAI Response Code:", response.status_code)

        if response.status_code != 200:
            print("❌ OpenAI Error:", response.text)
            return "Server busy bro 😔 Try again later."

        reply = response.json()["choices"][0]["message"]["content"]
        print("🧠 AI Reply:", reply)
        return reply

    except Exception as e:
        print("❌ AI Error:", e)
        return "Error generating reply bro 😔"


# ==========================================================
# 💬 Send Message via Interakt API
# ==========================================================
def send_whatsapp_message(mobile, message):
    try:
        payload = {
            "countryCode": "+91",
            "phoneNumber": str(mobile),
            "type": "text",
            "message": {"text": message}
        }

        headers = {
            "Authorization": f"Basic {INTERAKT_API_KEY}",
            "Content-Type": "application/json"
        }

        url = "https://app.interakt.io/api/public/message/"
        r = requests.post(url, json=payload, headers=headers)
        print("📤 Interakt API Status:", r.status_code)
        print("📤 Interakt Response:", r.text)
        return r.status_code == 200

    except Exception as e:
        print("❌ Interakt Send Error:", e)
        return False


# ==========================================================
# 🌊 Webhook Receiver
# ==========================================================
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        print("📩 Incoming Webhook:")
        print(data)

        # Step 1: Identify event or fallback
        event = data.get("event")
        if not event:
            print("⚠️ No 'event' key found — treating as potential session message.")

        # Step 2: Extract customer info and message
        customer = data.get("data", {}).get("customer", {})
        message_obj = data.get("data", {}).get("message", {})

        mobile = customer.get("phoneNumber")
        message_type = message_obj.get("type", "").lower()
        message_text = message_obj.get("content")

        print(f"📞 From: {mobile}")
        print(f"💬 Type: {message_type}")
        print(f"💬 Text: {message_text}")

        # Step 3: Ignore templates, media, and marketing pushes
        if message_type not in ["text"]:
            print("⏸ Ignored non-text message or template.")
            return jsonify({"status": "ignored"}), 200

        if not mobile or not message_text:
            print("⚠️ Missing phone number or message.")
            return jsonify({"status": "missing_fields"}), 400

        # Step 4: Generate AI reply
        ai_reply = generate_ai_reply(message_text)
        success = send_whatsapp_message(mobile, ai_reply)

        if success:
            print("✅ AI reply sent to", mobile)
        else:
            print("❌ Failed to send AI reply to", mobile)

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print("🔥 Webhook Exception:", e)
        return jsonify({"error": str(e)}), 500


# ==========================================================
# 🏠 Home Endpoint
# ==========================================================
@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "active", "message": "Karuvadukadai WhatsApp AI Bot ✅"})


# ==========================================================
# 🚀 Start App
# ==========================================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
