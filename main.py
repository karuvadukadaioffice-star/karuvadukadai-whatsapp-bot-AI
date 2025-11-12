from flask import Flask, request, jsonify
import requests, os

app = Flask(__name__)

# 🔑 Environment Variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INTERAKT_API_KEY = os.getenv("INTERAKT_API_KEY")

# ================================
# 🤖 AI Reply Generator (OpenAI)
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
                {"role": "system", "content": "You are a friendly Tamil-English assistant for karuvadukadai.com"},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.7
        }

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"].strip()
        print("🧠 AI Reply:", reply)
        return reply
    except Exception as e:
        print("❌ OpenAI Error:", e)
        return "Server busy bro 😔. Try again after 1 min."

# ================================
# 💬 Send WhatsApp Message (Interakt)
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

        response = requests.post(url, json=payload, headers=headers)
        print("📤 Interakt Reply:", response.status_code, response.text)
        return response.status_code == 200

    except Exception as e:
        print("❌ Send Error:", e)
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

        if not mobile or not message:
            print("⚠️ Missing phoneNumber or message content")
            return jsonify({"status": "error"}), 400

        # Generate AI reply and send it
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
