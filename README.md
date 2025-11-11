# Karuvadukadai WhatsApp Bot 🤖🐟

A smart AI chatbot integrated with **Interakt WhatsApp API** and **OpenAI GPT-3.5-turbo**,  
deployed on **Render** to assist seafood buyers in Tanglish (Tamil-English).

---

## 🚀 Features
- Replies automatically to WhatsApp messages
- Understands product queries (Vanjaram, Nethili, Ready-to-Eat, etc.)
- Fetches tracking numbers dynamically from Interakt events
- Supports Tamil-English conversation style
- Fully serverless on Render

---

## ⚙️ Environment Variables (set in Render)
| Key | Example Value |
|-----|----------------|
| `INTERAKT_API_KEY` | Base64 Interakt Public API Key |
| `OPENAI_API_KEY` | `sk-xxxxxx...` |
| `SHOP_URL` | `https://karuvadukadai.com` |

---

## 🛠️ Deploy
1. Fork this repo to GitHub  
2. Connect repo to Render  
3. Set environment variables above  
4. Deploy → Manual Deploy → **Deploy latest commit**

---

## 🔍 Test Commands
| Message | Bot Reply |
|----------|------------|
| Vanjaram iruka bro | Product link reply |
| Tracking number sollunga | Fetches tracking info |
| Ready to eat | Sends Ready-to-Eat collection link |
