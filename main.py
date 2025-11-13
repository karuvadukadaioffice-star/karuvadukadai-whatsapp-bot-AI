from flask import Flask, request, jsonify
import requests
import os
import openai

app = Flask(__name__)

INTERAKT_API_KEY = os.getenv("INTERAKT_API_KEY")
WHATSAPP_SENDER = os.getenv("WHATSAPP_SENDER")        # << MUST BE IN ENV
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY


def send_whatsapp_message(to, text):
    url = "https://api.interakt.ai/v1/public/message/"
    headers = {
        "Authorization": f"Bearer {INTERAKT_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "receiver": to,
        "sender": WHATSAPP_SENDER,
        "message_type": "text",
        "text": {"body": text}
    }
    requests.post(url, json=payload)


@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.json
    print("Incoming Payload:", data)

    # 1️⃣ Workflow Webhook
    if "from" in data and "message" in data:
        user_number = str(data["from"])
        user_message = data["message"]
        print("Detected WORKFLOW message:", user_message)

    # 2️⃣ Normal Interakt webhook
    elif (
        data.get("type") == "message_received"
        and data.get("data")
        and data["data"].get("message")
        and data["data"]["message"].
