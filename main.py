from flask import Flask, request, jsonify
import requests, os

app = Flask(__name__)

INTERAKT_SECRET = os.getenv("INTERAKT_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


@app.route("/", methods=["GET"])
def home():
    return "Interakt + OpenAI Webhook Running!"


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    # Validate Interakt Signature
    received_secret = request.headers.get("X-API-Secret")
    if received_secret != INTERAKT_SECRET:
        return jsonify({"error": "Invalid secret"}), 401

    try:
        message = data["message"]["text"]
        phone = data["sender"]["phone"]

        reply_text = ai_reply(message)
        send_whatsapp(phone, reply_text)

        return jsonify({"status": "reply_sent"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def ai_reply(user_message):
    url = "https://api.openai.com/v1/chat/completions"

    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}

    body = {
        "model": "gpt-4.1-mini",
        "messages": [
            {"role": "system", "content": "You are customer support for Karuvadukadai.com"},
            {"role": "user", "content": user_message},
        ]
    }

    r = requests.post(url, json=body, headers=headers).json()
    return r["choices"][0]["message"]["content"]


def send_whatsapp(phone, text):
    url = "https://api.interakt.ai/v1/public/message/"

    headers = {
        "Accept": "application/json",
        "Authorization": f"Basic {INTERAKT_SECRET}"
    }

    payload = {
        "phoneNumber": phone,
        "type": "text",
        "text": {"body": text}
    }

    requests.post(url, json=payload, headers=headers)


if __name__ == "__main__":
    app.run(debug=True)
