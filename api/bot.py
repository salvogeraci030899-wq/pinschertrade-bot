from flask import Flask, request
import requests

app = Flask(__name__)

TOKEN = "8496256972:AAHsOI5HqtIbe_Z6E38xHmLKFD1olTRGd-E"

# Messaggi completi
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

📱 `/APP` - Open the trading platform
💰 `/BUY` - Purchase your access pass
📖 `/GUIDE` - Step-by-step setup instructions
🆘 `/SUPPORT` - Technical assistance

*Transform your trading with institutional-grade tools today!*
______""",

    "app": """📱 **TRADING PLATFORM**

🚀 **Launch the Mini App directly here:**
👉 [t.me/PINSCHERTRADE_BOT/app](https://t.me/PINSCHERTRADE_BOT/app)

**Or:**
1. Open @PINSCHERTRADE_BOT
2. Click the menu in the bottom right
3. Select "Web App" or "Mini App"

*Enter your access password to start receiving real-time trading signals!*""",

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

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    
    if 'message' in update:
        chat_id = update['message']['chat']['id']
        text = update['message'].get('text', '')
        
        # Log per debug
        print(f"Received message: '{text}' from chat {chat_id}")
        
        # Mappatura diretta dei comandi
        command_map = {
            '/start': 'start',
            '/app': 'app', 
            '/buy': 'buy',
            '/guide': 'guide',
            '/support': 'support'
        }
        
        # Cerca il comando esatto
        response_key = 'start'  # default
        for cmd, key in command_map.items():
            if text.lower().startswith(cmd.lower()):
                response_key = key
                break
        
        print(f"Selected response: {response_key}")
        response_text = MESSAGES.get(response_key, MESSAGES['start'])
        
        send_message(chat_id, response_text)
    
    return 'OK'

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown',
        'disable_web_page_preview': False
    }
    try:
        result = requests.post(url, json=payload, timeout=10)
        print(f"Message sent to Telegram, status: {result.status_code}")
        return True
    except Exception as e:
        print(f"Error sending message: {e}")
        return False

@app.route('/')
def home():
    return "🤖 PINSCHERTRADE Bot is running!"

@app.route('/set-webhook')
def set_webhook():
    webhook_url = f"https://{request.host}/webhook"
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}"
    result = requests.get(url).json()
    return f"Webhook setup: {result}"

# Test route per verificare i messaggi
@app.route('/test-messages')
def test_messages():
    return {
        "app_message": MESSAGES['app'],
        "guide_message": MESSAGES['guide'],
        "all_keys": list(MESSAGES.keys())
    }

if __name__ == '__main__':
    app.run()
