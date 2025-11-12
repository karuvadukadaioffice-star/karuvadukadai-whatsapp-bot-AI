from flask import Flask, request, jsonify
import requests, os

app = Flask(__name__)

# ==========================================================
# 🔑 Load Environment Variables (from Render Environment tab)
# ==========================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INTERAKT_API_KEY = os.getenv("INTERAKT_API_KEY")

print("===========================================")
print("🚀 Starting Karuvadukadai WhatsApp AI Bot...")
print("✅ OpenAI Key Loaded:", "Yes" if OPENAI_API_KEY else "❌ Missing")
print("✅ Interakt Key Loaded:", "Yes" if INTERAKT_API_KEY else "❌ Missing")
print("===========================================")


# ==========================================================
# 🧠 Generate AI Reply using OpenAI ChatGPT API
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
                    "content": "You are a friendly Tamil-English assistant for Karuvadukadai.com. Keep replies short, natural and helpful."
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
        print("🧠 AI Reply Generated:", reply)
        return reply

    except Exception as e:
        print("❌ Exception in OpenAI:", e)
        return "Something went wrong, bro 😔"


# ==========================================================
# 💬 Send Message Back to Customer using Interakt API
# ==========================================================
def send_whatsapp_message(mobile, message):
    try:
        payload = {
            "countryCode": "+91",
            "phoneNumber": str(mobile),
            "type": "text",
            "message": {
                "text": message
            }
        }

        headers = {
            "Authorization": f"Basic {INTERAKT_API_KEY}",
            "Content-Type": "application/json"
        }

        url = "https://app.interakt.io/api/public/message/"
        r = requests.post(url, json=payload, headers=headers)
        print("📤 Interakt API Response Code:", r.status_code)
        print("📤 Interakt Response Text:", r.text)
        return r.status_code == 200

    except Exception as e:
        print("❌ Interakt Send Error:", e)
        return False


# ==========================================================
# 🌊 Webhook Endpoint — Receives Messages from Interakt
# ==========================================================
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        print("📩 Incoming Webhook Payload:")
        print(data)

        event = data.get("event")
        if event != "message_received":
            print("⚙️ Ignored Event Type:", event)
            return jsonify({"status": "ignored"}), 200

        customer = data.get("data", {}).get("customer", {})
        mobile = customer.get("phoneNumber")
        message = data.get("data", {}).get("message", {}).get("content")

        print(f"📞 From: {mobile}")
        print(f"💬 Message: {message}")

        if not mobile or not message:
            print("⚠️ Missing mobile or message field in webhook")
            return jsonify({"status": "error"}), 400

        ai_reply = generate_ai_reply(message)
        success = send_whatsapp_message(mobile, ai_reply)

        if success:
            print("✅ Reply sent successfully to", mobile)
        else:
            print("❌ Failed to send reply")

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print("🔥 Webhook Exception:", e)
        return jsonify({"error": str(e)}), 500


# ==========================================================
# 🏠 Home Route — for testing the Render instance
# ==========================================================
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "active",
        "message": "Karuvadukadai WhatsApp AI Bot is running ✅"
    })


# ==========================================================
# 🚀 Start Flask App
# ==========================================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
