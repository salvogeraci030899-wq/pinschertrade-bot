from flask import Flask, request
import requests
import json

app = Flask(__name__)

TOKEN = "8496256972:AAHsOI5HqtIbe_Z6E38xHmLKFD1olTRGd-E"

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    
    if 'message' in update:
        chat_id = update['message']['chat']['id']
        text = update['message'].get('text', '')
        
        # Risposta semplice per ogni comando
        if '/app' in text.lower():
            response = "📱 APP Response: Mini App link here"
        elif '/guide' in text.lower():
            response = "📋 GUIDE Response: Guide content here"
        elif '/buy' in text.lower():
            response = "💰 BUY Response: Buy content here"
        elif '/support' in text.lower():
            response = "🆘 SUPPORT Response: Support content here"
        else:
            response = "🤖 START Response: Welcome message here"
            
        send_message(chat_id, response)
    
    return 'OK'

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text}
    requests.post(url, json=payload)

@app.route('/')
def home():
    return "Bot is running!"

if __name__ == '__main__':
    app.run()
