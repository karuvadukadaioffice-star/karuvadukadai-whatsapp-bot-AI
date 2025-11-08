from flask import Flask, request, jsonify
import hmac
import hashlib
import os
import openai

app = Flask(__name__)

# Environment Variables
INTERAKT_WEBHOOK_SECRET = os.getenv("INTERAKT_WEBHOOK_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

@app.route('/')
def home():
    return jsonify({"status": "Karuvadukadai WhatsApp Bot is Live ✅"}), 200

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # Interakt test webhook
        return jsonify({"status": "Webhook active ✅"}), 200

    try:
        signature = request.headers.get("Interakt-Signature")
        body = request.get_data()

        # Validate signature (security check)
        if INTERAKT_WEBHOOK_SECRET:
            expected = hmac.new(
                INTERAKT_WEBHOOK_SECRET.encode(),
                body,
                hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(expected, signature):
                return jsonify({"error": "Invalid signature"}), 401

        data = request.json
        print("Webhook Received:", data)

        # Simple confirmation back to Interakt
        return jsonify({"success": True}), 200

    except Exception as e:
        print("Webhook Error:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
