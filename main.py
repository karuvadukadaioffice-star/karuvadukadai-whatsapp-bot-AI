from flask import Flask, request, jsonify
import os
import requests
import openai
import json

app = Flask(__name__)

# ===================== CONFIG =====================
INTERAKT_API_KEY = os.getenv("INTERAKT_API_KEY")  # base64 encoded key from Interakt dashboard
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SHOP_URL = os.getenv("SHOP_URL")

openai.api_key = OPENAI_API_KEY

TRACKING_FILE = "tracking_store.json"

# ===================== HELPERS =====================
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

tracking_data = load_tracking_data()

# ===================== ROUTES =====================
@app.route('/')
def home():
    return jsonify({"status": "Karuvadukadai WhatsApp Bot is Live ✅"})

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        return jsonify({"status": "Webhook active ✅"}), 200

    try:
        data = request.get_json()
        print("📩 Incoming:", data)
        event_type = data.get("type")

        # ✅ Tracking update events from Interakt
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

        # ✅ Customer messages
        elif event_type == "message_received":
            customer = data["data"]["customer"]
            mobile = customer["wa_id"]
            message_text = data["data"]["message"]["text"]["body"].lower().strip()
            print(f"💬 {mobile}: {message_text}")

            # Handle tracking query
            if "track" in message_text or "tracking" in message_text:
                if mobile in tracking_data:
                    t = tracking_data[mobile]
                    reply = (
                        f"Unga tracking number {t['tracking_number']} 📦\n"
                        f"Tracking link 👉 {t['tracking_link']}"
                    )
                else:
                    reply = (
                        "Bro unga order tracking details not found 😅.\n"
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

# ===================== SEND WHATSAPP MESSAGE =====================
def send_whatsapp_message(mobile, message):
    try:
        payload = {
            "countryCode": "91",  # ✅ Must NOT have '+'
            "phoneNumber": mobile,
            "type": "Plain Text",  # ✅ Correct format (Interakt expects this)
            "message": {"text": message}
        }

        headers = {
            "Authorization": f"Basic {INTERAKT_API_KEY}",  # ✅ Already Base64 encoded
            "Content-Type": "application/json"
        }

        print("📦 Sending payload to Interakt:", json.dumps(payload, indent=2))
        r = requests.post("https://api.interakt.ai/v1/public/message/", json=payload, headers=headers)
        print("📤 WhatsApp reply:", r.status_code, r.text)

        if r.status_code != 200:
            print("❌ Interakt Error:", r.text)

    except Exception as e:
        print("❌ Send message error:", e)

# ===================== AI REPLY =====================
def generate_ai_reply(message):
    try:
        prompt = f"""
        You are 'Karuvadukadai' — a friendly seafood seller bot.
        Reply in Tanglish (Tamil-English mix), polite and short.
        Give helpful replies with product links.

        Examples:
        - Vanjaram → "Vanjaram iruku bro 🐟! Super quality. Link 👉 {SHOP_URL}/products/kingfish-karuvadu"
        - Nethili → "Fresh nethili karuvadu ready bro! 🔥 Link 👉 {SHOP_URL}/products/nethili-dry-fish"
        - Ready to eat → "Naanga have Ready-to-Eat seafoods 🍛 👉 {SHOP_URL}/collections/ready-to-eat"
        - Combo → "Combo packs iruku bro 😍! Check 👉 {SHOP_URL}/collections/combo"
        - Price/Stock → Friendly response
        - Delivery or tracking → Ask politely for tracking number if not known
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

# ===================== RUN SERVER =====================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
