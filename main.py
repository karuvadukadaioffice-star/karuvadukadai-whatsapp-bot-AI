from flask import Flask, request, jsonify
import os
import requests
import json

app = Flask(__name__)

# =========================
# 🔑 ENVIRONMENT VARIABLES
# =========================
INTERAKT_API_KEY = os.getenv("INTERAKT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SHOP_URL = "https://karuvadukadai.com"

# =========================
# 💬 FUNCTION: SEND WHATSAPP MESSAGE
# =========================
def send_whatsapp_message(mobile, message):
    try:
        payload = {
            "countryCode": "+91",
            "phoneNumber": str(mobile),
            "type": "text",  # ✅ must be lowercase
            "message": {
                "text": message
            }
        }

        headers = {
            "Authorization": f"Basic {INTERAKT_API_KEY}",
            "Content-Type": "application/json"
        }

        r = requests.post(
            "https://api.interakt.ai/v1/public/message/",
            json=payload,
            headers=headers
        )

        print("\n📤 --- WhatsApp Message Sent ---")
        print("➡️ Payload:", json.dumps(payload, indent=2))
        print("➡️ Status Code:", r.status_code)
        print("➡️ Response:", r.text)
        print("📤 ------------------------------\n")

    except Exception as e:
        print("❌ Send message error:", e)


# =========================
# 🧠 FUNCTION: GENERATE AI REPLY
# =========================
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
                        "Reply shortly in Tanglish (Tamil-English mix) — polite and natural.\n"
                        "Always sound like a helpful shop owner (bro/sir tone).\n"
                        f"- Vanjaram → {SHOP_URL}/products/kingfish-karuvadu\n"
                        f"- Nethili → {SHOP_URL}/products/nethili-dry-fish\n"
                        f"- Ready to Eat → {SHOP_URL}/collections/ready-to-eat\n"
                        f"- Combo → {SHOP_URL}/collections/combo"
                    )
                },
                {"role": "user", "content": user_text}
            ],
            "max_tokens": 150,
            "temperature": 0.8
        }

        r = requests.post(url, headers=headers, json=payload)
        data = r.json()
        print("🧠 AI Response Raw:", json.dumps(data, indent=2))

        ai_reply = data["choices"][0]["message"]["content"].strip()
        return ai_reply

    except Exception as e:
        print("❌ AI Error:", e)
        return "Server busy iruku bro 😅 konjam later try pannunga!"


# =========================
# 🌊 WEBHOOK: RECEIVE INCOMING MESSAGES
# =========================
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        print("\n📩 --- Incoming Webhook ---")
        print(json.dumps(data, indent=2))
        print("📩 -------------------------\n")

        event_type = data.get("event", "")
        if event_type != "message_received":
            print("⚙️ Ignored event type:", event_type)
            return jsonify({"status": "ignored"}), 200

        # ✅ Extract customer and message
        message_obj = data.get("data", {}).get("message", {})
        message_text = (
            message_obj.get("text")
            or message_obj.get("body")
            or message_obj.get("content")  # ✅ Fix for Interakt payload
        )
        customer = data.get("data", {}).get("customer", {})
        phone = customer.get("phoneNumber")

        if not message_text or not phone:
            print("⚠️ Missing text or phone number in webhook data")
            return jsonify({"status": "invalid"}), 400

        print(f"💬 From {phone}: {message_text}")

        # ✅ Generate AI reply
        reply = generate_ai_reply(message_text)

        # ✅ Send reply to customer via Interakt
        send_whatsapp_message(phone, reply)

        return jsonify({"status": "success"}), 200

    except Exception as e:
        print("❌ Webhook error:", e)
        return jsonify({"error": str(e)}), 500


# =========================
# 🏠 ROOT TEST ROUTE
# =========================
@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Karuvadukadai WhatsApp Bot is Live 🐟"}), 200


# =========================
# 🚀 RUN APP (LOCAL TEST)
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
