# Karuvadukadai WhatsApp AI Bot 🐟

A friendly Tamil-English seafood assistant that chats with customers on WhatsApp via Interakt.shop.

### 🔧 Features
- Tamil + English mixed (Tanglish) replies
- Fetches product details dynamically
- Uses OpenAI GPT for personalized responses
- Works for **session messages (within 24h)** on Interakt.shop
- Hosted easily on **Render**

### 🚀 Setup
1. Fork this repo on GitHub.
2. Add environment variables in Render:
   - `INTERAKT_API_KEY` = Your Interakt.shop API key (base64 encoded)
   - `OPENAI_API_KEY` = Your OpenAI API key
3. Deploy to Render.
4. Add webhook URL in Interakt:
