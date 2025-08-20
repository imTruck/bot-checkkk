import requests
import schedule
import time
from bs4 import BeautifulSoup
from telegram import Bot

# اطلاعات ربات و کانال
TOKEN = '8011560580:AAE-lsa521NE3DfGKj247DC04cZOr27SuAY'         # از BotFather بگیر
CHAT_ID = '@asle_tehran'       # با @ شروع بشه

bot = Bot(token=TOKEN)

def get_local_prices():
    url = 'https://www.navasan.net/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    try:
        dollar = soup.find('td', text='دلار آمریکا').find_next_sibling('td').text.strip()
        euro = soup.find('td', text='یورو').find_next_sibling('td').text.strip()
        gold = soup.find('td', text='یک گرم طلا 18 عیار').find_next_sibling('td').text.strip()
        coin = soup.find('td', text='سکه طرح امامی').find_next_sibling('td').text.strip()
    except:
        dollar = euro = gold = coin = 'نامشخص'

    return dollar, euro, gold, coin

def get_crypto_prices():
    url = 'https://api.coingecko.com/api/v3/simple/price'
    params = {
        'ids': 'bitcoin,ethereum,tether,cardano,solana,ripple',
        'vs_currencies': 'usd',
        'include_24hr_change': 'true'
    }
    response = requests.get(url, params=params)
    data = response.json()

    def format(name, symbol):
        price = data[name]['usd']
        change = data[name]['usd_24h_change']
        return f"{symbol}: ${price:.2f} ({change:+.2f}%)"

    return [
        format('bitcoin', 'BTC'),
        format('ethereum', 'ETH'),
        format('tether', 'USDT'),
        format('cardano', 'ADA'),
        format('solana', 'SOL'),
        format('ripple', 'XRP')
    ]

def send_report():
    dollar, euro, gold, coin = get_local_prices()
    cryptos = get_crypto_prices()

    message = f"""
📊 قیمت لحظه‌ای بازار ایران

💵 دلار: {dollar} تومان  
🌍 یورو: {euro} تومان  
🏅 سکه امامی: {coin} تومان  
🔸 طلا ۱۸ عیار: {gold} تومان  

🪙 رمزارزها:
{chr(10).join(cryptos)}

📌 به‌روزرسانی خودکار هر ۱۵ دقیقه
"""
    bot.send_message(chat_id=CHAT_ID, text=message)

# زمان‌بندی
schedule.every(15).minutes.do(send_report)

print("✅ ربات فعال شد و هر ۱۵ دقیقه قیمت لحظه‌ای بازار رو ارسال می‌کنه...")

while True:
    schedule.run_pending()
    time.sleep(1)
