README.md
# Karuvadukadai WhatsApp AI Bot 🤖

This bot connects **Interakt WhatsApp API** with **ChatGPT-5** to provide Tamil + English customer support.

## 🧠 Features
- Auto-reply with GPT-5 intelligence
- Handles Tamil-English mixed conversations
- Responds to order-tracking queries
- Works on free Render.com hosting

## ⚙️ Environment Variables
Add these in your Render Environment tab:
- `OPENAI_API_KEY` = your OpenAI key
- `INTERAKT_API_KEY` = your Interakt API key
- `INTERAKT_WEBHOOK_SECRET` = f6fe41ec-93df-41b3-913b-f0f47ea9377

## 🚀 Deploy on Render
1. Create a [Render](https://render.com) account  
2. Connect this GitHub repo  
3. Build command → `pip install -r requirements.txt`  
4. Start command → `python main.py`  
5. Use your permanent URL in Interakt Webhook Settings
