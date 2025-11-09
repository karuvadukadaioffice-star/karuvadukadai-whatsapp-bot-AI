from flask import Flask, request, jsonify
import os
import requests
import openai

app = Flask(__name__)

# Environment variables
INTERAKT_API_KEY = os.getenv("INTERAKT_API_KEY")
INTERAKT_WEBHOOK_SECRET = os.getenv("INTERAKT_WEBHOOK_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SHOP_URL = os.getenv("SHOP_URL")

openai.api_key = OPENAI_API_KEY


@app.route('/')
def home():
    return jsonify({"status": "Karuvadukadai WhatsApp Bot is Live ✅"})


@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        return jsonify({"status": "Webhook active ✅"}), 200

    try:
        data = request.get_json()
        print("Incoming message:", data)

        if data.get("type") == "message_received":
            customer = data["data"]["customer"]
            mobile = customer["wa_id"]
            message_text = data["data"]["message"]["text"]["body"]

            print(f"Customer message: {message_text}")

            # Generate AI reply
            ai_reply = generate_ai_reply(message_text)

            # Send reply to Interakt
            payload = {
                "phoneNumber": mobile,
                "message": {"text": ai_reply}
            }

            headers = {
                "Authorization": f"Basic {INTERAKT_API_KEY.split(' ')[-1]}",
                "Content-Type": "application/json"
            }

            send_response = requests.post(
                "https://api.interakt.ai/v1/public/message/",
                json=payload,
                headers=headers
            )

            print("Reply status:", send_response.status_code, send_response.text)
            return jsonify({"status": "ok"}), 200

        return jsonify({"ignored": True}), 200

    except Exception as e:
        print("Webhook error:", e)
        return jsonify({"error": str(e)}), 500


def generate_ai_reply(message):
    try:
        prompt = f"""
        You are 'Karuvadukadai' — a friendly Tamil seafood seller.
        Reply in Tanglish (Tamil-English mix). Always respond kindly.
        If customer asks about:
        - Vanjaram → Give price and link: {SHOP_URL}/products/kingfish-karuvadu
        - Nethili → Mention it's fresh and give link: {SHOP_URL}/products/nethili-dry-fish
        - Tracking → Ask for tracking number and offer to help
        - Combo or Ready to Eat → Suggest items from Ready to Eat section
        Message: {message}
        """

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": message}
            ],
            temperature=0.8,
            max_tokens=250
        )

        reply = response["choices"][0]["message"]["content"].strip()
        print("AI reply:", reply)
        return reply

    except Exception as e:
        print("OpenAI error:", e)
        return "Server busy irukku bro 😅! Konjam later try pannunga."


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
