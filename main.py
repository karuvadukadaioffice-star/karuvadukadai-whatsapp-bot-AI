main.py
from flask import Flask, request, jsonify
import hmac, hashlib, os, requests
from openai import OpenAI

app = Flask(__name__)

WEBHOOK_SECRET = os.getenv("INTERAKT_WEBHOOK_SECRET", "f6fe41ec-93df-41b3-913b-f0f47ea9377")
INTERAKT_API_KEY = os.getenv("INTERAKT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY_HERE")

client = OpenAI(api_key=OPENAI_API_KEY)

@app.route('/')
def home():
    return "✅ Karuvadukadai AI WhatsApp Bot is running", 200

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        return jsonify({"status": "Webhook active"}), 200

    payload = request.get_data()
    signature = request.headers.get("Interakt-Signature", "")
    computed_sig = hmac.new(
        WEBHOOK_SECRET.encode(),
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()

    if signature and not hmac.compare_digest(computed_sig, signature):
        print("❌ Invalid signature")
        return jsonify({"error": "invalid signature"}), 401

    data = request.get_json(silent=True)
    print("📩 Incoming webhook:", data)

    user_msg = data.get("message", {}).get("text", "") or ""
    user_phone = data.get("sender", {}).get("phone", "")

    if not user_msg or not user_phone:
        return jsonify({"status": "ignored"}), 200

    if "order" in user_msg.lower() or "status" in user_msg.lower():
        ai_response = "📦 Please share your order ID, I'll check your status immediately!"
    else:
        ai_response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "You are Karuvadukadai AI Assistant. Reply politely in Tamil + English mixed. Give helpful answers about orders, shipping, and dry fish products."},
                {"role": "assistant", "content": "Vanakkam! 👋 Ungal Karuvadukadai AI assistant here. How can I help you today?"},
                {"role": "user", "content": user_msg}
            ]
        ).choices[0].message.content

    print(f"🤖 Replying to {user_phone}: {ai_response}")

    requests.post(
        "https://api.interakt.ai/v1/public/message/",
        headers={
            "Authorization": f"Basic {INTERAKT_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "phoneNumber": user_phone,
            "messageType": "TEXT",
            "text": {"body": ai_response}
        }
    )

    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
