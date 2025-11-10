from flask import Flask, request, jsonify
import os
import requests
import openai
import base64
import json

app = Flask(__name__)

# Environment variables
INTERAKT_API_KEY = os.getenv("INTERAKT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SHOP_URL = os.getenv("SHOP_URL")

openai.api_key = OPENAI_API_KEY

TRACKING_FILE = "tracking_store.json"

# ------------------- Helper: Load/Save JSON -------------------
def load_tracking_data():
    try:
        if os.path.exists(TRACKING_FILE):
            with open(TRACKING_FILE, "r") as f:
                return json.load(f)
    except:
        pass
    return {}

def save_tracking_data(data):
    with open(TRACKING_FILE, "w") as f:
        json.dump(data, f)

# Load existing tracking info
tracking_data = load_tracking_data()

# ------------------- Home Route -------------------
@app.route('/')
def home():
    return jsonify({"status": "Karuvadukadai WhatsApp Bot is Live ✅"})

# ------------------- Webhook Route -------------------
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        return jsonify({"status": "Webhook active ✅"}), 200

    try:
        data = request.get_json()
        print("📩 Incoming:", data)
        event_type = data.get("type")

        # ✅ 1. When Interakt sends tracking updates (save it permanently)
        if event_type == "event" and "order" in data.get("data", {}):
            order = data["data"]["order"]
            mobile = order.get("customer", {}).get("wa_id")
            tracking_number = order.get("tracking_number", "").strip()
            tracking_link = order.get("tracking_link", "https://franchexpress.com")
            status = order.get("status", "Processing")

            if mobile:
                tracking_data[mobile] = {
                    "tracking_number": tracking_number,
                    "tracking_link": tracking_link,
                    "status": status
                }
                save_tracking_data(tracking_data)
                print(f"✅ Saved tracking for {mobile}: {tracking_number} ({status})")

            return jsonify({"status": "tracking_saved"}), 200

        # ✅ 2. When customer sends a message
        elif event_type == "message_received":
            customer = data["data"]["customer"]
            mobile = customer["wa_id"]
            message_text = data["data"]["message"]["text"]["body"].lower().strip()

            print(f"💬 {mobile}: {message_text}")

            # If user asks about tracking
            if "tracking" in message_text or "track" in message_text:
                if mobile in tracking_data:
                    t = tracking_data[mobile]
                    reply = (
                        f"Unga tracking number {t['tracking_number']} 📦\n"
                        f"Tracking link 👉 {t['tracking_link']}"
                    )
                else:
                    reply = (
                        "Bro, unga order tracking details not found 😅.\n"
                        "Once dispatch aagum bothu update pannuren 🙏."
                    )
            else:
                reply = generate_ai_reply(message_text)

            send_whatsapp_message(mobile, reply)
            return jsonify({"status": "ok"}), 200

        else:
            print("⚙️ Ignored event type:", event_type)
            return jsonify({"ignored": True}), 200

    except Exception as e:
        print("❌ Webhook error:", e)
        return jsonify({"error": str(e)}), 500

# ------------------- Send WhatsApp Message -------------------
def send_whatsapp_message(mobile, message):
    try:
        payload = {
            "countryCode": "+91",
            "phoneNumber": mobile,
            "type": "PlainText",
            "message": {"text": message}
        }

        headers = {
            "Authorization": f"Basic {base64.b64encode(INTERAKT_API_KEY.encode()).decode()}",
            "Content-Type": "application/json"
        }

        r = requests.post("https://api.interakt.ai/v1/public/message/", json=payload, headers=headers)
        print("📤 WhatsApp reply:", r.status_code, r.text)
    except Exception as e:
        print("❌ Send message error:", e)

# ------------------- AI Reply Generator -------------------
def generate_ai_reply(message):
    try:
        prompt = f"""
        You are 'Karuvadukadai' — a friendly seafood store bot.
        Reply in Tanglish (Tamil-English mix) — short, kind, and polite.
        Mention links if customer asks about products.

        Examples:
        - Vanjaram → "Vanjaram iruku bro 🐟! Super quality. Link: {SHOP_URL}/products/kingfish-karuvadu"
        - Nethili → "Fresh nethili karuvadu ready bro! 🔥 Link: {SHOP_URL}/products/nethili-dry-fish"
        - Ready to eat → "Naanga have Ready-to-Eat seafoods bro 🍛 👉 {SHOP_URL}/collections/ready-to-eat"
        - Combo → "Combo packs iruku bro 😍! Check 👉 {SHOP_URL}/collections/combo"
        - Price or stock → Give friendly tone
        - Delivery or tracking → Ask politely for tracking number if not known.

        Message: {message}
        """

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": message}
            ],
            temperature=0.8,
            max_tokens=200
        )

        reply = response["choices"][0]["message"]["content"].strip()
        print("🤖 AI reply:", reply)
        return reply

    except Exception as e:
        print("❌ OpenAI error:", e)
        return "Server busy irukku bro 😅! Konjam later try pannunga."

# ------------------- Run Server -------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
