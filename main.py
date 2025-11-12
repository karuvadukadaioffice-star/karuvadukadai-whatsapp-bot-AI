from flask import Flask, request, jsonify
import requests, os

app = Flask(__name__)

# 🔑 Environment Variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INTERAKT_API_KEY = os.getenv("INTERAKT_API_KEY")

print("✅ OpenAI Key Loaded:", "Yes" if OPENAI_API_KEY else "❌ Missing")
print("✅ Interakt Key Loaded:", "Yes" if INTERAKT_API_KEY else "❌ Missing")

# ================================
# 🤖 Generate AI Reply
# ================================
def generate_ai_reply(user_message):
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a friendly Tamil-English assistant for Karuvadukadai.com"},
                {"role": "user", "content": user_message}
            ]
        }

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        print("🧠 OpenAI Response Code:", response.status_code)
        print("🧠 OpenAI Response:", response.text)
        reply = response.json()["choices"][0]["message"]["content"]
        return reply
    except Exception as e:
        print("❌ OpenAI Error:", e)
        return "Server busy bro 😔 Try again later."

# ================================
# 💬 Send WhatsApp Message via Interakt
# ================================
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
        print("📤 Interakt API Response:", r.status_code, r.text)
        return r.status_code == 200
    except Exception as e:
        print("❌ Interakt Send Error:", e)
        return False

# ================================
# 🌊 Webhook Endpoint
# ================================
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        print("📩 Incoming Webhook:", data)

        event = data.get("event")
        if event != "message_received":
            print("🧩 Ignored Event Type:", event)
            return jsonify({"status": "ignored"}), 200

        customer = data.get("data", {}).get("customer", {})
        mobile = customer.get("phoneNumber")
        message = data.get("data", {}).get("message", {}).get("content")

        print(f"📞 From: {mobile}, 💬 Message: {message}")

        if not mobile or not message:
            print("⚠️ Missing mobile or message content.")
            return jsonify({"status": "error"}), 400

        ai_reply = generate_ai_reply(message)
        send_whatsapp_message(mobile, ai_reply)

        return jsonify({"status": "ok"}), 200
    except Exception as e:
        print("❌ Webhook Error:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    return "Karuvadukadai WhatsApp Bot Active ✅"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
