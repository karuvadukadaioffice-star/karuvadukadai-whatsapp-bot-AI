import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

INTERAKT_API_KEY = os.getenv("INTERAKT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SHOP_URL = os.getenv("SHOP_URL")

@app.route('/')
def home():
    return jsonify({"status": "Karuvadukadai WhatsApp Bot is Live ✅"})

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        return jsonify({"status": "Webhook active ✅"}), 200

    data = request.json
    print("Incoming message:", data)

    try:
        message_type = data.get("type")
        if message_type == "message_received":
            customer = data["data"]["customer"]
            mobile = customer["wa_id"]
            message_text = data["data"]["message"]["text"]["body"]

            print(f"Customer message: {message_text}")

            # Generate AI response
            ai_reply = generate_ai_reply(message_text)

            # Send back to Interakt
            payload = {
                "phoneNumber": mobile,
                "message": {
                    "text": ai_reply
                }
            }

            headers = {
                "Authorization": INTERAKT_API_KEY,
                "Content-Type": "application/json"
            }

            response = requests.post(
                "https://api.interakt.ai/v1/public/message/",
                json=payload,
                headers=headers
            )

            print("Reply status:", response.status_code, response.text)
        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print("Webhook error:", e)
        return jsonify({"error": str(e)}), 500


def generate_ai_reply(message):
    import openai
    openai.api_key = OPENAI_API_KEY

    prompt = f"""
    You are 'Karuvadukadai' — a friendly Tamil seafood seller from Tamil Nadu.
    Reply naturally in Tanglish (Tamil-English mix) to help customers about dry fish, prices, or tracking orders.
    Example tone:
    - "Vanakkam bro 😊! Fresh Vanjaram karuvadu available 😋. Link inga 👉 {SHOP_URL}/products/kingfish-karuvadu"
    - "Neenga order panni irukeengala sir? Tracking number kudunga, naan check panren."
    Message: {message}
    """

    completion = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": prompt}]
    )

    reply = completion.choices[0].message.content.strip()
    return reply


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
