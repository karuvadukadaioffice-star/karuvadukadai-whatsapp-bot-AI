from flask import Flask, request, jsonify
import os
import hmac
import hashlib
import openai
import requests

app = Flask(__name__)

# Environment variables
INTERAKT_WEBHOOK_SECRET = os.getenv("INTERAKT_WEBHOOK_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

@app.route('/')
def home():
    return jsonify({"status": "Karuvadukadai AI Bot is live"}), 200

@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    if request.method == 'GET':
        return jsonify({"status": "Webhook active"}), 200

    signature = request.headers.get("Interakt-Signature")
    body = request.get_data()

    # Verify signature
    if not signature or not verify_signature(signature, body):
        return jsonify({"error": "Invalid signature"}), 401

    data = request.json
    print("Received webhook:", data)

    if "message" in data:
        user_message = data["message"].get("text", "")
        reply = generate_reply(user_message)
        print("AI Reply:", reply)

    return jsonify({"status": "success"}), 200


def verify_signature(signature, body):
    if not INTERAKT_WEBHOOK_SECRET:
        return True
    expected = hmac.new(
        INTERAKT_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def generate_reply(message):
    prompt = f"User said: {message}\nReply in Tamil-English mix: "
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
