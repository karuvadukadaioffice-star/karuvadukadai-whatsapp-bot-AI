from flask import Flask, request, jsonify
import requests
import os
import openai

app = Flask(__name__)

INTERAKT_API_KEY = os.getenv("INTERAKT_API_KEY")
WHATSAPP_SENDER = os.getenv("WHATSAPP_SENDER")
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

    # ----------------------------
    # 1️⃣ HANDLE INTERAKT WORKFLOW WEBHOOK
    # ----------------------------
    if "from" in data and "message" in data:
        user_number = str(data["from"])
        user_message = data["message"]
        print("Detected WORKFLOW message:", user_message)

    # ----------------------------
    # 2️⃣ HANDLE NORMAL INTERAKT WEBHOOK
    # ----------------------------
    elif (
        data.get("type") == "message_received"
        and data.get("data")
        and data["data"].get("message")
        and data["data"]["message"].get("text")
    ):
        user_number = data["data"]["customer"]["phone_number"]
        user_message = data["data"]["message"]["text"]["body"]
        print("Detected NORMAL message:", user_message)

    else:
        print("⚠️ No valid text message, skipping...")
        return jsonify({"status": "ignored"})

    # ----------------------------
    # 3️⃣ GENERATE AI RESPONSE
    # ----------------------------
    completion = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful dry fish assistant for Karuvadukadai."},
            {"role": "user", "content": user_message}
        ]
    )

    ai_reply = completion.choices[0].message.content
    print("AI Reply:", ai_reply)

    # ----------------------------
    # 4️⃣ SEND AI REPLY TO WHATSAPP
    # ----------------------------
    send_whatsapp_message(user_number, ai_reply)

    return jsonify({"status": "success"})


@app.route("/", methods=["GET"])
def home():
    return "Bot Running OK"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
