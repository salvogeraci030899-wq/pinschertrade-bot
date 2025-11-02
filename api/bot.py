from flask import Flask, request, jsonify
import requests
import os
import time
from datetime import datetime
import threading

app = Flask(__name__)

# === CONFIGURAZIONE ESPANSA ===
TOKEN = "8496256972:AAHsOI5HqtIbe_Z6E38xHmLKFD1olTRGd-E"
BOT_USERNAME = "PINSCHERTRADE_BOT"

# Database semplice per gli utenti (in memoria - per produzione usa un DB vero)
user_configs = {}

# === SISTEMA NOTIFICHE 24/7 ===
class NotificationManager:
    def __init__(self):
        self.active_signals = {}
        self.coin_data = {}
        
    def fetch_market_data(self):
        """Recupera dati di mercato in tempo reale"""
        try:
            coins = ['bitcoin', 'ethereum', 'solana', 'bonk', 'dogwifcoin']
            for coin in coins:
                response = requests.get(
                    f'https://api.coingecko.com/api/v3/coins/{coin}',
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    self.coin_data[coin] = {
                        'price': data['market_data']['current_price']['usd'],
                        'change_24h': data['market_data']['price_change_percentage_24h'],
                        'name': data['name'],
                        'symbol': data['symbol'].upper()
                    }
                    print(f"✅ Fetched {coin}: ${self.coin_data[coin]['price']}")
        except Exception as e:
            print(f"❌ Error fetching market data: {e}")
    
    def analyze_signals(self):
        """Analizza e genera segnali di trading"""
        signals = []
        for coin_id, data in self.coin_data.items():
            signal = self.generate_signal(coin_id, data)
            if signal and self.is_new_signal(coin_id, signal):
                signals.append(signal)
                self.active_signals[coin_id] = signal
        return signals
    
    def generate_signal(self, coin_id, data):
        """Genera segnale basato su analisi tecnica semplificata"""
        if not data or 'change_24h' not in data:
            return None
            
        price = data['price']
        change_24h = data['change_24h']
        
        # Logica di trading semplificata
        if change_24h < -8:  # Forte calo
            return {
                'type': 'BUY',
                'coin': data,
                'confidence': min(85, abs(change_24h)),
                'reason': f'Oversold - dropped {abs(change_24h):.1f}% in 24h',
                'timestamp': datetime.now().isoformat()
            }
        elif change_24h > 12:  # Forte rialzo
            return {
                'type': 'SELL', 
                'coin': data,
                'confidence': min(80, change_24h),
                'reason': f'Overbought - surged {change_24h:.1f}% in 24h',
                'timestamp': datetime.now().isoformat()
            }
        return None
    
    def is_new_signal(self, coin_id, signal):
        """Controlla se il segnale è nuovo"""
        last_signal = self.active_signals.get(coin_id)
        if not last_signal:
            return True
        return last_signal['type'] != signal['type']
    
    def format_signal_message(self, signal):
        """Formatta il messaggio per Telegram"""
        coin = signal['coin']
        return f"""
🚨 **TRADING SIGNAL - {signal['type']}**

💎 **{coin['name']} ({coin['symbol']})**
💰 Price: ${coin['price']:,.4f}
📈 24h Change: {coin['change_24h']:+.2f}%

🎯 **Confidence:** {signal['confidence']:.0f}%
📊 **Reason:** {signal['reason']}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

#{coin['symbol']} #{signal['type']}
        """.strip()

# Inizializza il manager delle notifiche
notification_manager = NotificationManager()

# === ENDPOINT PER NOTIFICHE AUTOMATICHE ===
@app.route('/check-markets', methods=['GET', 'POST'])
def check_markets():
    """Endpoint chiamato dai cron jobs per controllare i mercati"""
    try:
        print("🔄 Checking markets for signals...")
        
        # Aggiorna dati di mercato
        notification_manager.fetch_market_data()
        
        # Analizza segnali
        signals = notification_manager.analyze_signals()
        
        # Invia notifiche
        sent_count = 0
        for signal in signals:
            for chat_id, config in user_configs.items():
                if config.get('notifications_enabled', False):
                    message = notification_manager.format_signal_message(signal)
                    if send_message(chat_id, message):
                        sent_count += 1
                    time.sleep(0.5)  # Rate limiting
        
        response = {
            'status': 'success',
            'signals_found': len(signals),
            'notifications_sent': sent_count,
            'active_users': sum(1 for config in user_configs.values() if config.get('notifications_enabled', False)),
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"✅ Market check completed: {response}")
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Error in check-markets: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

# === ENDPOINT HEALTH CHECK PER UPTIMEROBOT ===
@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint semplice per UptimeRobot"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_users': len(user_configs),
        'notifications_enabled': sum(1 for config in user_configs.values() if config.get('notifications_enabled', False)),
        'service': 'PINSCHERTRADE Bot'
    }), 200

# === ENDPOINT API SEMPLICE ===
@app.route('/api/check-markets', methods=['GET'])
def check_markets_api():
    """Endpoint API semplificato"""
    try:
        notification_manager.fetch_market_data()
        signals = notification_manager.analyze_signals()
        
        return jsonify({
            'status': 'success',
            'signals_found': len(signals),
            'timestamp': datetime.now().isoformat(),
            'market_data': {coin: data for coin, data in notification_manager.coin_data.items()}
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

# === GESTIONE ISCRIZIONI UTENTI ===
@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    
    if 'message' in update:
        chat_id = update['message']['chat']['id']
        text = update['message'].get('text', '').lower()
        
        # Inizializza configurazione utente
        if str(chat_id) not in user_configs:
            user_configs[str(chat_id)] = {
                'notifications_enabled': False,
                'created_at': datetime.now().isoformat(),
                'username': update['message']['chat'].get('username', ''),
                'first_name': update['message']['chat'].get('first_name', '')
            }
        
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
        elif text in ['/notifications on', f'/notifications on@{BOT_USERNAME}']:
            user_configs[str(chat_id)]['notifications_enabled'] = True
            response = "✅ **24/7 Notifications ACTIVATED**\n\nYou will now receive automatic trading signals even when the app is closed!\n\nUse /status to check your settings."
        elif text in ['/notifications off', f'/notifications off@{BOT_USERNAME}']:
            user_configs[str(chat_id)]['notifications_enabled'] = False
            response = "🔕 **24/7 Notifications DEACTIVATED**\n\nYou will no longer receive automatic signals.\n\nUse /notifications on to reactivate."
        elif text in ['/status', f'/status@{BOT_USERNAME}']:
            status = "ACTIVE ✅" if user_configs[str(chat_id)]['notifications_enabled'] else "INACTIVE 🔕"
            response = f"🔔 **Notification Status: {status}**\n\nUse /notifications on|off to control 24/7 signals"
        elif text in ['/test', f'/test@{BOT_USERNAME}']:
            # Test delle notifiche
            test_signal = {
                'type': 'BUY',
                'coin': {
                    'name': 'Bitcoin',
                    'symbol': 'BTC',
                    'price': 45000.00,
                    'change_24h': -8.5
                },
                'confidence': 85,
                'reason': 'Test signal - oversold condition'
            }
            message = notification_manager.format_signal_message(test_signal)
            send_message(chat_id, message)
            response = "🧪 Test signal sent! Check if you received it."
        else:
            response = MESSAGES['start']
            
        send_message(chat_id, response)
    
    return jsonify({'status': 'ok'})

# === FUNZIONE INVIO MESSAGGI ===
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown'
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error sending message to {chat_id}: {e}")
        return False

# === MESSAGGI AGGIORNATI ===
MESSAGES = {
    "start": """🤖 **Welcome to PINSCHERTRADE - Advanced Trading Signals**

**NEW: 24/7 Automatic Notifications!** 🔔

Now receive trading signals even when the app is closed!

**Commands:**
📱 `/APP` - Open trading platform
💰 `/BUY` - Purchase access pass  
🔔 `/NOTIFICATIONS ON` - Enable 24/7 signals
🔕 `/NOTIFICATIONS OFF` - Disable 24/7 signals
📊 `/STATUS` - Check notification status
🧪 `/TEST` - Test notification
📖 `/GUIDE` - Setup instructions
🆘 `/SUPPORT` - Technical help

*Never miss a trading opportunity again!*""",

    "app": """📱 **TRADING PLATFORM**

🚀 **Launch the Mini App directly:**
👉 [Open PINSCHERTRADE App](https://t.me/PINSCHERTRADE_BOT/app)

Or open the Mini App from the bot's menu to access the trading signals and configure your preferences.""",

    "buy": """💰 **PURCHASE ACCESS PASSWORD**

To access all advanced trading signals from PINSCHERTRADE, purchase the access password:

🔒 **PASSWORD PURCHASE LINK:**
👉 [Buy Access Password](https://payhip.com/b/P0CWm)

**What you get:**
• Complete access password
• 24/7 Trading Signals
• Multi-timeframe analysis
• Real-time Telegram notifications
• Dedicated technical support

**Price: €XXX** (check the link for updated price)

*After purchase, you will receive the password via email*""",

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

**STEP 5 - ACTIVATE 24/7 SIGNALS**
• Send `/notifications on` to this bot
• Receive automatic signals even when app is closed

**Support:** /SUPPORT""",

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

# === PAGINA PRINCIPALE ===
@app.route('/')
def home():
    active_users = sum(1 for config in user_configs.values() if config.get('notifications_enabled', False))
    return f"""
<h1>🤖 PINSCHERTRADE Bot is running with 24/7 Notifications!</h1>
<br>
<p><strong>📊 Statistics:</strong></p>
<ul>
<li>Total Users: {len(user_configs)}</li>
<li>Active Notifications: {active_users}</li>
<li>Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
</ul>
<br>
<p><strong>🔗 Endpoints:</strong></p>
<ul>
<li><a href="/check-markets">/check-markets</a> - Manual market check</li>
<li><a href="/health">/health</a> - Health check (for UptimeRobot)</li>
<li><a href="/api/check-markets">/api/check-markets</a> - API endpoint</li>
<li><a href="/stats">/stats</a> - Statistics</li>
<li><a href="/set-webhook">/set-webhook</a> - Setup webhook</li>
</ul>
"""

@app.route('/set-webhook')
def set_webhook():
    webhook_url = f"https://{request.host}/webhook"
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}"
    result = requests.get(url).json()
    return jsonify(result)

# === STATISTICHE ===
@app.route('/stats')
def stats():
    active_users = sum(1 for config in user_configs.values() if config.get('notifications_enabled', False))
    return jsonify({
        'status': 'success',
        'total_users': len(user_configs),
        'active_notifications': active_users,
        'users_count': len(user_configs),
        'last_check': datetime.now().isoformat(),
        'service': 'PINSCHERTRADE Bot API'
    })

# === AVVIA CONTROLLO AUTOMATICO ALL'AVVIO ===
def start_background_checks():
    """Avvia controlli periodici in background"""
    def background_check():
        while True:
            try:
                # Controlla i mercati ogni 10 minuti
                notification_manager.fetch_market_data()
                signals = notification_manager.analyze_signals()
                
                for signal in signals:
                    for chat_id, config in user_configs.items():
                        if config.get('notifications_enabled', False):
                            message = notification_manager.format_signal_message(signal)
                            send_message(chat_id, message)
                            time.sleep(0.5)
                
                time.sleep(600)  # 10 minuti
            except Exception as e:
                print(f"Background check error: {e}")
                time.sleep(60)
    
    # Avvia il thread in background
    thread = threading.Thread(target=background_check, daemon=True)
    thread.start()
    print("✅ Background market checks started!")

# Avvia i controlli in background quando l'app si avvia
start_background_checks()

# === CONFIGURAZIONE VERCEL ===
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
