from flask import Flask, request, jsonify
import requests
import os
import stripe
import json
from datetime import datetime

app = Flask(__name__)

# === CONFIGURAZIONE ===
TOKEN = "8496256972:AAHsOI5HqtIbe_Z6E38xHmLKFD1olTRGd-E"
BOT_USERNAME = "PINSCHERTRADE_BOT"

# === STRIPE CONFIGURATION ===
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_your_secret_key_here')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', 'whsec_your_webhook_secret_here')

# === DATABASE SEMPLIFICATO (in production usa un database vero) ===
LICENSES_FILE = 'licenses.json'

def load_licenses():
    try:
        with open(LICENSES_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_licenses(licenses):
    with open(LICENSES_FILE, 'w') as f:
        json.dump(licenses, f, indent=2)

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
✅ Multi-Timeframe Analysis
✅ Automated Telegram Notifications
✅ Professional Risk Management
✅ Bitget, Binance & TradingView Integration

**Get Started:**
Use the commands below to begin your trading journey:

📱 `/app` - Open the trading platform
💰 `/buy` - Purchase Lifetime Access ($14.99)
📖 `/guide` - Setup instructions
🆘 `/support` - Technical assistance

*Transform your trading with institutional-grade tools today!*
""",

    "app": """📱 **TRADING PLATFORM**

🚀 **Access the Web App:**
https://pinschertrade.vercel.app

Or use the web app to access real-time trading signals and configure your preferences.""",

    "buy": """💰 **PURCHASE LIFETIME ACCESS**

🚀 **PINSCHERTRADE - LIFETIME ACCESS**

Get complete lifetime access to:
• Real-time trading signals
• Automated Telegram notifications  
• Advanced technical analysis
• Professional risk management
• 24/7 market monitoring

🎯 **Price: $14.99 (one-time payment)**

Click the button below to purchase:""",

    "guide": """📋 **COMPLETE GUIDE - HOW TO GET STARTED**

**STEP 1 - PURCHASE LIFETIME ACCESS**
• Use `/buy` command to purchase access
• Complete the secure Stripe payment
• Receive your license key instantly via Telegram

**STEP 2 - ACCESS THE WEB APP**
• Open: https://pinschertrade.vercel.app
• Enter your license key
• Configure your trading preferences

**STEP 3 - CREATE YOUR TELEGRAM BOT**
• Search for @BotFather on Telegram
• Send `/newbot` and follow instructions
• Save the **Bot Token** you receive
• Get your **Chat ID** with @userinfobot

**STEP 4 - CONFIGURE NOTIFICATIONS**
• In PINSCHERTRADE app, go to Settings → Notifications
• Enter your Bot Token and Chat ID
• Save the configuration

**STEP 5 - ACTIVATE SIGNALS**
• Add your favorite coins to watchlist
• Set up your trading strategies
• Receive automatic BUY/SELL notifications

**Support:** /SUPPORT
_____""",

    "support": """🆘 **TECHNICAL SUPPORT**

**Payment Issues?**
• Contact: @PinscherTradeSupport on Telegram
• Provide your transaction ID

**License Key Issues?**
• Verify you entered the correct license key
• Check your Telegram chat history for the key
• If issue persists, contact support

**Telegram Bot Issues?**
• Verify you created the bot correctly with @BotFather
• Check that the Token is correct
• Make sure you started the bot

**Technical Issues in the App?**
• Restart the web app
• Check your internet connection
• Try clearing browser cache

**Support Channel:**
💬 **Telegram Only:** @PinscherTradeSupport

**Response Time: 24-48 hours**

*Note: All support requests must be sent via Telegram to @PinscherTradeSupport*"""
}

# === FUNZIONI DI SUPPORTO ===
def generate_license_key():
    """Genera una license key unica"""
    import random
    import string
    
    prefix = "PINSCHER"
    timestamp = datetime.now().strftime("%y%m%d")
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    return f"{prefix}-{timestamp}-{random_part}"

def send_license_key(chat_id, license_key):
    """Invia la license key all'utente"""
    message = f"""✅ **PAYMENT CONFIRMED!**

🎉 Welcome to PINSCHERTRADE Premium!

Your lifetime access license key is:

`{license_key}`

**To activate your access:**

1. Go to: https://pinschertrade.vercel.app
2. Enter your license key
3. Click "Activate License"

**What you get:**
• Lifetime access to all features
• Real-time trading signals
• Automated Telegram notifications
• Advanced trading tools
• Priority support

**Need help?** Contact @PinscherTradeSupport

Happy trading! 🚀"""

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown',
        'reply_markup': {
            'inline_keyboard': [[
                {
                    'text': '🚀 Open PINSCHERTRADE',
                    'url': 'https://pinschertrade.vercel.app'
                }
            ]]
        }
    }
    
    try:
        requests.post(url, json=payload, timeout=10)
        return True
    except Exception as e:
        print(f"Error sending license key: {e}")
        return False

def create_stripe_checkout(chat_id):
    """Crea una sessione di checkout Stripe"""
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'PINSCHERTRADE - Lifetime Access',
                        'description': 'Lifetime access to advanced trading signals and notifications'
                    },
                    'unit_amount': 1499,  # $14.99
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f'https://t.me/{BOT_USERNAME}?start=success',
            cancel_url=f'https://t.me/{BOT_USERNAME}?start=cancelled',
            metadata={
                'telegram_chat_id': str(chat_id),
                'product': 'pinschertrade_lifetime'
            }
        )
        return checkout_session.url
    except Exception as e:
        print(f"Stripe error: {e}")
        return None

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
            send_message(chat_id, response)
            
        elif text in ['/app', f'/app@{BOT_USERNAME}']:
            response = MESSAGES['app']
            send_message(chat_id, response)
            
        elif text in ['/buy', f'/buy@{BOT_USERNAME}']:
            # Crea checkout Stripe
            checkout_url = create_stripe_checkout(chat_id)
            
            if checkout_url:
                keyboard = {
                    'inline_keyboard': [[
                        {
                            'text': '💳 Purchase Lifetime Access - $14.99',
                            'url': checkout_url
                        }
                    ]]
                }
                
                send_message(chat_id, MESSAGES['buy'], keyboard)
            else:
                send_message(chat_id, "❌ Error creating payment session. Please try again later.")
            
        elif text in ['/guide', f'/guide@{BOT_USERNAME}']:
            response = MESSAGES['guide']
            send_message(chat_id, response)
            
        elif text in ['/support', f'/support@{BOT_USERNAME}']:
            response = MESSAGES['support']
            send_message(chat_id, response)
            
        else:
            # Se il messaggio inizia con 'start' e ha parametri (per success/cancel)
            if text.startswith('/start'):
                if 'success' in text:
                    send_message(chat_id, "✅ Thank you for your purchase! Your license key has been sent to you. Check your messages above.")
                elif 'cancelled' in text:
                    send_message(chat_id, "❌ Payment was cancelled. You can try again with /buy when you're ready.")
                else:
                    response = MESSAGES['start']
                    send_message(chat_id, response)
            else:
                response = MESSAGES['start']
                send_message(chat_id, response)
    
    return 'OK'

# === WEBHOOK STRIPE ===
@app.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        print(f"Invalid payload: {e}")
        return jsonify(success=False), 400
    except stripe.error.SignatureVerificationError as e:
        print(f"Invalid signature: {e}")
        return jsonify(success=False), 400

    # Gestisci l'evento di pagamento completato
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Estrai i metadata
        chat_id = session['metadata'].get('telegram_chat_id')
        
        if chat_id:
            # Genera license key
            license_key = generate_license_key()
            
            # Salva nel "database"
            licenses = load_licenses()
            licenses[license_key] = {
                'chat_id': chat_id,
                'created_at': datetime.now().isoformat(),
                'stripe_session_id': session['id'],
                'amount_paid': session['amount_total'] / 100,  # Converti da centesimi
                'status': 'active'
            }
            save_licenses(licenses)
            
            # Invia la license key all'utente
            if send_license_key(chat_id, license_key):
                print(f"License key sent to {chat_id}: {license_key}")
            else:
                print(f"Failed to send license key to {chat_id}")
                
    return jsonify(success=True), 200

def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown'
    }
    
    if reply_markup:
        payload['reply_markup'] = reply_markup
        
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending message: {e}")

@app.route('/')
def home():
    return "🤖 PINSCHERTRADE Bot is running!"

@app.route('/validate-license', methods=['POST'])
def validate_license():
    """API per validare le license keys dal frontend"""
    data = request.get_json()
    license_key = data.get('licenseKey', '').strip().upper()
    
    licenses = load_licenses()
    
    if license_key in licenses:
        license_data = licenses[license_key]
        return jsonify({
            'valid': True,
            'userData': {
                'license': license_key,
                'type': 'lifetime',
                'activated': license_data['created_at'],
                'source': 'stripe'
            }
        })
    else:
        return jsonify({
            'valid': False,
            'message': 'License key not found or invalid'
        }), 404

# === SETUP WEBHOOK ===
@app.route('/set-webhook')
def set_webhook():
    webhook_url = f"https://{request.host}/webhook"
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}"
    result = requests.get(url).json()
    return f"Webhook setup: {result}"

if __name__ == '__main__':
    # Crea il file licenses se non esiste
    if not os.path.exists(LICENSES_FILE):
        save_licenses({})
    
    app.run(host='0.0.0.0', port=5000)
