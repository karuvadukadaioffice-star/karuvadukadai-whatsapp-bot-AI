from flask import Flask, request, jsonify
import requests
import os
import openai

app = Flask(__name__)

# --------------------------
# ENV VARIABLES
# --------------------------
INTERAKT_API_KEY = os.getenv("INTERAKT_API_KEY")  # NO BEARER
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY


# --------------------------
# SEND MESSAGE TO WHATSAPP (INTERAKT)
# --------------------------
def send_whatsapp_message(to, text):
    url = "https://api.interakt.ai/v1/public/message/"

    headers = {
        "Authorization": INTERAKT_API_KEY,      # IMPORTANT: no Bearer
        "Content-Type": "application/json"
    }

    payload = {
        "receiver": to,
        "message_type": "text",
        "text": {
            "body": text
        }
    }

    print("📤 Sending to Interakt:", payload)
    response = requests.post(url, json=payload, headers=headers)
    print("📨 Interakt Response:", response.text)
    return response.text


# --------------------------
# MAIN WEBHOOK
# --------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("🔥 Incoming Payload:", data)

    user_number = None
    user_message = None

    # ----------------------------------------------------
    # 1️⃣ INTERAKT WORKFLOW CUSTOM WEBHOOK (FROM WORKFLOW)
    # ----------------------------------------------------
    if isinstance(data, dict) and "from" in data and "message" in data:
        user_number = str(data["from"])
        user_message = data["message"]
        print("🟢 Workflow Trigger Detected")

    # ----------------------------------------------------
    # 2️⃣ NORMAL INTERAKT WEBHOOK (REAL CUSTOMER TEXT)
    # ----------------------------------------------------
    elif (
        data.get("type") == "message_received"
        and data.get("data")
        and data["data"].get("message")
        and data["data"]["message"].get("text")
    ):
        user_number = str(data["data"]["customer"]["phone_number"])
        user_message = data["data"]["message"]["text"]["body"]
        print("🟡 Normal Incoming Message Detected")

    else:
        print("⚠️ No text message found → Ignored")
        return jsonify({"status": "ignored"}), 200

    print(f"☎ User: {user_number}")
    print(f"💬 Message: {user_message}")

    # ----------------------------------------------------
    # 3️⃣ GENERATE AI RESPONSE
    # ----------------------------------------------------
    try:
        completion = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a friendly Tamil dry fish expert from Karuvadukadai."},
                {"role": "user", "content": user_message}
            ]
        )

        ai_reply = completion.choices[0].message.content
        print("🤖 AI Reply:", ai_reply)

    except Exception as e:
        print("❌ OpenAI Error:", e)
        return jsonify({"error": str(e)}), 500

    # ----------------------------------------------------
    # 4️⃣ SEND BACK THROUGH INTERAKT
    # ----------------------------------------------------
    send_whatsapp_message(user_number, ai_reply)

    return jsonify({"status": "success"}), 200


@app.route("/", methods=["GET"])
def home():
    return "Bot Running OK ✔"


# For local testing
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
