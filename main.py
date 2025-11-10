# main.py
from flask import Flask, request, jsonify
import os
import requests
import openai
import json
import base64
import traceback

app = Flask(__name__)

# ---------- Environment variables (set these on Render / GitHub secrets) ----------
INTERAKT_API_KEY = os.getenv("INTERAKT_API_KEY", "").strip()   # Either "Basic xxxx" or raw token (we auto-encode if raw)
INTERAKT_WEBHOOK_SECRET = os.getenv("INTERAKT_WEBHOOK_SECRET", "").strip()  # optional
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
SHOP_URL = os.getenv("SHOP_URL", "https://karuvadukadai.com").rstrip("/")
TRACKING_FILE = "tracking_store.json"

# OpenAI setup
openai.api_key = OPENAI_API_KEY

# ---------- Helper: persist tracking data ----------
def load_tracking_data():
    try:
        if os.path.exists(TRACKING_FILE):
            with open(TRACKING_FILE, "r") as f:
                return json.load(f)
    except Exception:
        print("Failed to load tracking file:", traceback.format_exc())
    return {}

def save_tracking_data(data):
    try:
        with open(TRACKING_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        print("Failed to save tracking file:", traceback.format_exc())

tracking_data = load_tracking_data()

# ---------- Utility: prepare Interakt Authorization header ----------
def prepare_interakt_auth_header():
    """
    Accepts either:
     - INTERAKT_API_KEY already as "Basic <base64>"
     - or raw token (we will base64-encode it and add Basic prefix)
    """
    key = INTERAKT_API_KEY
    if not key:
        return ""
    if key.lower().startswith("basic "):
        return key
    # If user provided something that already looks base64 (rare), still encode safely
    try:
        encoded = base64.b64encode(key.encode()).decode()
        return f"Basic {encoded}"
    except Exception:
        return key

INTERAKT_AUTH_HEADER = prepare_interakt_auth_header()

# ---------- Routes ----------
@app.route("/")
def home():
    return jsonify({"status": "Karuvadukadai WhatsApp Bot is Live ✅"})

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    # health check for GET
    if request.method == "GET":
        return jsonify({"status": "Webhook active ✅"}), 200

    # POST: handle incoming Interakt events
    try:
        data = request.get_json(force=True)
        print("📩 Incoming webhook payload:", json.dumps(data)[:4000])  # truncated log to avoid huge prints
        event_type = data.get("type", "").lower()

        # 1) Interakt order/event update (save tracking info)
        # Note: different Interakt schemas exist. We try common patterns.
        if event_type == "event" and isinstance(data.get("data"), dict) and data["data"].get("order"):
            order = data["data"]["order"]
            customer = order.get("customer", {}) or {}
            mobile = customer.get("wa_id") or customer.get("phone_number")
            tracking_number = order.get("tracking_number") or order.get("last_order_tracking_no") or ""
            tracking_link = order.get("tracking_link") or order.get("tracking_url") or "https://franchexpress.com"
            status = order.get("status") or order.get("last_order_status") or "Processing"

            if mobile:
                tracking_data[mobile] = {
                    "tracking_number": tracking_number,
                    "tracking_link": tracking_link,
                    "status": status
                }
                save_tracking_data(tracking_data)
                print(f"✅ Saved tracking for {mobile}: {tracking_number} ({status})")

            return jsonify({"status": "tracking_saved"}), 200

        # 2) Standard message_received event from Interakt
        if event_type == "message_received" or event_type == "message":
            payload = data.get("data", {}) or {}
            customer = payload.get("customer", {}) or {}
            mobile = customer.get("wa_id") or customer.get("phone_number")
            # message may be nested different ways; attempt to extract text
            message_text = None
            msg = payload.get("message") or {}
            # common location for text
            if isinstance(msg, dict):
                # Interakt may provide message['text']['body'] or message['text'] string
                txt = msg.get("text")
                if isinstance(txt, dict):
                    message_text = txt.get("body")
                elif isinstance(txt, str):
                    message_text = txt
            # fallback: payload may have top-level 'message' string
            if not message_text:
                message_text = payload.get("message_text") or payload.get("text") or ""

            message_text = (message_text or "").strip()
            print(f"💬 From {mobile}: {message_text}")

            reply = None
            # handle tracking queries
            lower = message_text.lower()
            if "track" in lower or "tracking" in lower or "tracking number" in lower or "track id" in lower:
                if mobile and mobile in tracking_data and tracking_data[mobile].get("tracking_number"):
                    t = tracking_data[mobile]
                    reply = (
                        f"Unga tracking number {t.get('tracking_number','-')} 📦\n"
                        f"Tracking link: {t.get('tracking_link','https://franchexpress.com')}\n"
                        f"Status: {t.get('status','-')}"
                    )
                else:
                    reply = "Bro, unga order tracking details enga illa 😅. Please share order/tracking number or wait for dispatch update."
            else:
                # pass to OpenAI to generate reply
                reply = generate_ai_reply(message_text)

            # send reply back to Interakt
            if mobile:
                send_whatsapp_message(mobile, reply)
                return jsonify({"status": "ok"}), 200
            else:
                print("⚠️ No mobile number found in message payload.")
                return jsonify({"error": "no_mobile"}), 400

        # else: ignored event types
        print("⚙️ Ignored event type:", event_type)
        return jsonify({"ignored": True}), 200

    except Exception as e:
        print("❌ Webhook handler error:", traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# ---------- Send WhatsApp Message (Interakt API) ----------
def send_whatsapp_message(mobile, message):
    """
    Sends a text message back to Interakt API.
    Interakt expects a payload with fields: phoneNumber, type, message{text}.
    We support INTERAKT_API_KEY provided either as 'Basic xxxx' or raw token (we auto-encode).
    """
    try:
        # ensure mobile is digits (Interakt may expect full international number or wa_id)
        phone = str(mobile).strip()
        if phone.startswith("+"):
            phone = phone[1:]

        payload = {
            "phoneNumber": phone,
            "type": "text",
            "message": {"text": message}
        }

        headers = {
            "Authorization": INTERAKT_AUTH_HEADER,
            "Content-Type": "application/json"
        }

        resp = requests.post(
            "https://api.interakt.ai/v1/public/message/",
            json=payload,
            headers=headers,
            timeout=15
        )

        print("📤 WhatsApp reply:", resp.status_code, resp.text)
        if resp.status_code >= 400:
            # log more context for debugging
            print("⚠️ Interakt returned error. Payload:", json.dumps(payload))
        return resp.status_code, resp.text

    except Exception:
        print("❌ Send message exception:", traceback.format_exc())
        return None, None

# ---------- OpenAI reply generator ----------
def generate_ai_reply(message):
    try:
        # Prompt instructs Tanglish friendly replies and product links
        prompt = f"""
You are 'Karuvadukadai' — a friendly Tamil seafood seller bot.
Reply in Tanglish (Tamil-English mix), be short, kind, and polite.
Use these rules:
- If user asks about Vanjaram mention price/link: {SHOP_URL}/products/kingfish-karuvadu
- If user asks about Nethili mention link: {SHOP_URL}/products/nethili-dry-fish
- If user asks for Ready to Eat or Combo show links to collections.
- If user asks for tracking and we don't have it, ask for tracking number.
- Use a friendly Tamil-English tone (e.g. 'Vanjaram iruku bro! Link 👉 ...')
Message: {message}
"""
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": message}
            ],
            temperature=0.7,
            max_tokens=200
        )

        reply = response["choices"][0]["message"]["content"].strip()
        print("🤖 AI reply:", reply)
        return reply

    except Exception:
        print("❌ OpenAI error:", traceback.format_exc())
        # fallback friendly message
        return "Server busy irukku bro 😅! Konjam later try pannunga."

# ---------- Run server ----------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    print("Starting app on port", port)
    app.run(host="0.0.0.0", port=port)
