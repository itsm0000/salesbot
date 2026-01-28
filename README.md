# Muntazir (منتظر) - Iraqi Arabic Sales AI Agent

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Python](https://img.shields.io/badge/python-3.9+-green)
![License](https://img.shields.io/badge/license-MIT-purple)

**وكيل المبيعات العراقي الذكي**

A culturally-aware AI sales agent platform for Iraqi businesses, fluent in Iraqi Arabic dialect with authentic sales acumen.

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.9+
- Google Gemini API key

### 2. Installation

```bash
# Clone/navigate to project
cd muntazir

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment template
copy .env.example .env

# Edit .env and add your Gemini API key
# GEMINI_API_KEY=your_key_here
```

### 4. Run

```bash
python main.py
```

Open http://localhost:8000 in your browser.

## 📁 Project Structure

```
muntazir/
├── src/
│   ├── core/
│   │   ├── brain.py        # Main AI reasoning engine
│   │   ├── knowledge.py    # Product catalog management
│   │   └── personality.py  # Iraqi Arabic persona
│   ├── storage/
│   │   └── firestore.py    # Database (Phase 1)
│   └── web/
│       ├── app.py          # FastAPI application
│       └── static/         # Web interface
├── data/
│   ├── products.csv        # Product catalog
│   └── prompts/            # Iraqi Arabic templates
├── config/
│   └── business_config.json
├── main.py                 # Entry point
└── requirements.txt
```

## 🎯 Features (Phase 0)

- ✅ Iraqi Arabic conversation with Gemini AI
- ✅ Product catalog management (CSV)
- ✅ Configurable business persona
- ✅ Manual testing web interface
- ✅ Confidence scoring
- ✅ Conversation history

## 🏢 Multi-Tenant Dashboard (Phase 4)

- ✅ Operator login/registration with password auth
- ✅ Multi-bot grid view with status monitoring
- ✅ Real-time message streaming (SSE)
- ✅ Start/Stop bot controls
- ✅ Custom persona & memory configuration per bot
- ✅ Create new bot wizard (3-step flow)

**Access**: Navigate to `/operator` for the operator dashboard.

## 📞 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface |
| `/dashboard` | GET | Business owner dashboard |
| `/operator` | GET | **NEW** Multi-bot operator dashboard |
| `/api/chat` | POST | Process customer message |
| `/api/products` | GET | List all products |
| `/api/config` | GET/PUT | Business configuration |
| `/api/health` | GET | Health check |
| `/api/operator/*` | Various | **NEW** Operator API endpoints |
| `/api/webhook/telegram` | POST | Telegram bot webhook |
| `/api/webhook/whatsapp` | POST | WhatsApp (Twilio) webhook |
| `/api/webhook/facebook` | POST | Facebook Messenger webhook |

## 🔌 Platform Integration

### Telegram Bot Setup
1. Create a bot via [@BotFather](https://t.me/BotFather)
2. Add `TELEGRAM_BOT_TOKEN` to `.env`
3. Set webhook:
   ```bash
   curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://YOUR_SERVER/api/webhook/telegram"
   ```

### WhatsApp (Twilio Sandbox)
1. Get credentials from [Twilio Console](https://console.twilio.com)
2. Add `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` to `.env`
3. Configure Sandbox webhook URL: `https://YOUR_SERVER/api/webhook/whatsapp`

### Facebook Messenger
1. Create app at [Meta Developer](https://developers.facebook.com)
2. Add `FACEBOOK_PAGE_TOKEN` to `.env`
3. Configure webhook URL: `https://YOUR_SERVER/api/webhook/facebook`

## 🌐 Iraqi Arabic Examples

```
Customer: شلونكم، شنو سعر المصباح الذكي؟
Muntazir: هلا والله حجي! المصباح الذكي RGB سعره 45,000 دينار...

Customer: غالي شوية، شنو آخر سعر؟
Muntazir: صدقني حجي هذا أحسن سعر بالسوق...
```

## 📋 Roadmap

- [x] **Phase 0**: Foundation & Manual Interface
- [x] **Phase 1**: Core Intelligence & Training
- [ ] **Phase 2**: Platform Integration (Facebook, WhatsApp)
- [ ] **Phase 3**: Stealth & Reliability
- [x] **Phase 4**: Multi-Tenancy & Operator Dashboard

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| `403 API key was reported as leaked` | Generate a new key at [Google AI Studio](https://aistudio.google.com/app/apikey) and update `.env` |
| `400 API_KEY_INVALID` / `API key expired` | Replace API key in `.env` and restart server |
| `FutureWarning: google.generativeai deprecated` | Cosmetic warning only; migration to `google.genai` planned |

## 📜 License

MIT License - See LICENSE file for details.

---

Built with ❤️ for Iraqi businesses | بُني بحب للأعمال العراقية
