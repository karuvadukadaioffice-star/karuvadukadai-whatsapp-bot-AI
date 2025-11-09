from flask import Flask, request, jsonify
import os
import requests
import openai

app = Flask(__name__)

# Environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INTERAKT_API_KEY = os.getenv("INTERAKT_API_KEY")

openai.api_key = OPENAI_API_KEY

@app.route("/")
def home():
    return jsonify({"status": "Karuvadukadai WhatsApp Bot connected ✅"}), 200


@app.route("/webhook", methods=["POST", "GET"])
def webhook():
    if request.method == "GET":
        return jsonify({"status": "Webhook active ✅"}), 200

    data = request.json
    print("Incoming message:", data)

    try:
        # Extract WhatsApp number and message text
        customer_number = data.get("waId") or data.get("phone") or None
        message_text = data.get("text") or data.get("message") or None

        if not customer_number or not message_text:
            return jsonify({"error": "Missing message or number"}), 400

        # Send to OpenAI
        ai_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are Karuvadukadai’s friendly Tamil-English assistant. Reply in a warm, Tanglish style."},
                {"role": "user", "content": message_text},
            ]
        )

        reply_text = ai_response.choices[0].message["content"]

        # Send reply to Interakt
        send_url = "https://api.interakt.ai/v1/public/message/"
        headers = {
            "Authorization": f"Basic {INTERAKT_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "countryCode": "+91",
            "phoneNumber": str(customer_number),
            "callbackData": "Karuvadukadai AI Bot",
            "type": "TEXT",
            "message": {"text": reply_text}
        }

        requests.post(send_url, json=payload, headers=headers)
        print("✅ Replied to:", customer_number)

        return jsonify({"success": True}), 200

    except Exception as e:
        print("Webhook Error:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
