from flask import Flask, request, jsonify
import os
import requests
import json

app = Flask(__name__)

# ================================
# 🌍 Environment Variables
# ================================
INTERAKT_API_KEY = os.getenv("INTERAKT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SHOP_URL = "https://karuvadukadai.com"

# ================================
# 🧠 Generate AI Reply (Tanglish)
# ================================
def generate_ai_reply(user_text):
    try:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are 'Karuvadukadai' — a friendly Tamil seafood seller bot 🐟.\n"
                        "Reply in Tanglish (Tamil-English mix) warmly and helpfully.\n"
                        f"Product links:\n"
                        f"- Vanjaram Karuvadu → {SHOP_URL}/products/kingfish-karuvadu\n"
                        f"- Nethili Karuvadu → {SHOP_URL}/products/nethili-dry-fish\n"
                        f"- Ready to Eat → {SHOP_URL}/collections/ready-to-eat\n"
                        f"- Combo Offers → {SHOP_URL}/collections/combo\n"
                        "Keep tone friendly, short, and kind — like a local seller."
                    )
                },
                {"role": "user", "content": user_text}
            ],
            "max_tokens": 150,
            "temperature": 0.8
        }

        r = requests.post(url, headers=headers, json=payload)
        data = r.json()

        reply = data["choices"][0]["message"]["content"].strip()
        print("🧠 AI Reply:", reply)
        return reply

    except Exception as e:
        print("❌ OpenAI error:", e)
        return "Server busy irukku bro 😅 Konjam later try pannunga!"

# ================================
# 💬 Send WhatsApp Message (Session Type)
# ================================
def send_whatsapp_message(mobile, message):
    try:
        payload = {
            "countryCode": "+91",
            "phoneNumber": str(mobile),
            "type": "text",   # ✅ Session message type
            "message": {
                "text": message
            }
        }

        headers = {
            "Authorization": f"Basic {INTERAKT_API_KEY}",
            "Content-Type": "application/json"
        }

        r = requests.post(
            "https://app.interakt.shop/api/public/message/",
            json=payload,
            headers=headers
        )

        print("\n📤 WhatsApp Message Sent →")
        print("Payload:", json.dumps(payload, indent=2))
        print("Status:", r.status_code)
        print("Response:", r.text)
        print("📤 --------------------------\n")

    except Exception as e:
        print("❌ Send message error:", e)

# ================================
# 📩 Webhook (Handle Customer Message)
# ================================
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        print("\n📩 Incoming Webhook:", json.dumps(data, indent=2))

        event = data.get("event", "")
        if event != "message_received":
            print("Ignored event:", event)
            return jsonify({"status": "ignored"}), 200

        customer = data.get("data", {}).get("customer", {})
        phone = customer.get("phoneNumber")

        message_obj = data.get("data", {}).get("message", {})
        message_text = (
            message_obj.get("text")
            or message_obj.get("body")
            or message_obj.get("content")
        )

        if not phone or not message_text:
            print("⚠️ Invalid webhook payload")
            return jsonify({"error": "invalid"}), 400

        print(f"📲 From {phone}: {message_text}")

        # ✅ Generate AI reply
        reply = generate_ai_reply(message_text)

        # ✅ Send back to WhatsApp
        send_whatsapp_message(phone, reply)

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print("❌ Webhook error:", e)
        return jsonify({"error": str(e)}), 500

# ================================
# 🌐 Home Route (For Testing)
# ================================
@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Karuvadukadai WhatsApp Bot is LIVE ✅"}), 200

# ================================
# 🚀 Run App (Render)
# ================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
