from flask import Flask, request
import requests
import os

app = Flask(__name__)

# === CONFIGURAZIONE ===
TOKEN = "8496256972:AAHsOI5HqtIbe_Z6E38xHmLKFD1olTRGd-E"
BOT_USERNAME = "PINSCHERTRADE_BOT"

# === MESSAGGI PERSONALIZZATI ===
MESSAGES = {
    "start": """🤖 **Welcome to PINSCHERTRADE - Advanced Trading Signals**

**What is PINSCHERTRADE?**
PINSCHERTRADE is a professional trading platform that provides real-time cryptocurrency trading signals and advanced market analysis.

**What We Do:**
• Generate BUY/SELL signals using advanced algorithms
• Monitor markets 24/7 across multiple timeframes
• Send instant notifications via Telegram
• Provide risk management tools and strategies

**Key Features:**
✅ Real-time Trading Signals
✅ Multi-Timeframe Analysis (5m, 15m, 1h, 4h)
✅ Automated Telegram Notifications
✅ Professional Risk Management
✅ Bitget, Binance & TradingView Integration

**Get Started:**
Use the commands below to begin your trading journey:

📱 `/app` - Open the trading platform
💰 `/buy` - Purchase your access pass
📖 `/guide` - Step-by-step setup instructions
🆘 `/support` - Technical assistance

*Transform your trading with institutional-grade tools today!*
______""",

    "app": """📱 **TRADING PLATFORM**

🚀 **Launch the Mini App directly:**
https://t.me/pinschertrade_bot/app

Or open the Mini App from the bot's menu to access the trading signals and configure your preferences.""",

    "buy": """💰 **PURCHASE ACCESS PASSWORD**

To access all advanced trading signals from PINSCHERTRADE, purchase the access password:

🔒 **PASSWORD PURCHASE LINK:**
https://payhip.com/b/P0CWm

**What you get:**
• Complete access password
• 24/7 Trading Signals
• Multi-timeframe analysis
• Real-time Telegram notifications
• Dedicated technical support

**Price: €XXX** (check the link for updated price)

*After purchase, you will receive the password via email*
____""",

    "guide": """📋 **COMPLETE GUIDE - HOW TO GET STARTED**

**STEP 1 - PURCHASE ACCESS PASSWORD**
• Go to: https://payhip.com/b/P0CWm
• Complete the purchase
• Receive the password via email

**STEP 2 - ACCESS THE APP**
• Open the Mini App: /APP
• Enter your access password
• Configure your preferences

**STEP 3 - CREATE YOUR TELEGRAM BOT**
• Search for @BotFather on Telegram
• Send /newbot and follow the instructions
• Save the **Token** of the bot you receive
• Get your **Chat ID** with @userinfobot

**STEP 4 - CONFIGURE NOTIFICATIONS**
• In the PINSCHERTRADE app, go to Settings → Notifications
• Enter your bot Token and your Chat ID
• Save the configuration

**STEP 5 - ACTIVATE SIGNALS**
• Add your favorite coins
• Set up your trading strategies
• Receive automatic notifications for BUY/SELL signals

**Support:** /SUPPORT
_____""",

    "support": """🆘 **TECHNICAL SUPPORT**

**Purchase Issues?**
• Contact: @PinscherTradeSupport on Telegram
• Provide your order number and email

**Access Problems?**
• Verify you entered the correct access password
• Check your email (including spam folder)
• If issue persists, contact support

**Telegram Bot Issues?**
• Verify you created the bot correctly with @BotFather
• Check that the Token is correct
• Make sure you started the bot

**Technical Issues in the App?**
• Restart the Mini App
• Check your internet connection
• Try clearing browser cache

**Support Channel:**
💬 **Telegram Only:** @PinscherTradeSupport

**Response Time: 24-48 hours**

*Note: All support requests must be sent via Telegram to @PinscherTradeSupport*"""
}

# === LOGICA DEL BOT ===
@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    
    if 'message' in update:
        chat_id = update['message']['chat']['id']
        text = update['message'].get('text', '').lower()
        
        # Gestisci i comandi
        if text in ['/start', f'/start@{BOT_USERNAME}']:
            response = MESSAGES['start']
        elif text in ['/app', f'/app@{BOT_USERNAME}']:
            response = MESSAGES['app']
        elif text in ['/buy', f'/buy@{BOT_USERNAME}']:
            response = MESSAGES['buy']
        elif text in ['/guide', f'/guide@{BOT_USERNAME}']:
            response = MESSAGES['guide']
        elif text in ['/support', f'/support@{BOT_USERNAME}']:
            response = MESSAGES['support']
        else:
            response = MESSAGES['start']
            
        send_message(chat_id, response)
    
    return 'OK'

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass  # Ignora errori di timeout

@app.route('/')
def home():
    return "🤖 PINSCHERTRADE Bot is running!"

# === SETUP WEBHOOK ===
@app.route('/set-webhook')
def set_webhook():
    webhook_url = f"https://{request.host}/webhook"
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}"
    result = requests.get(url).json()
    return f"Webhook setup: {result}"

if __name__ == '__main__':
    app.run()
