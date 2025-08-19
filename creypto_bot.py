import requests
from bs4 import BeautifulSoup
from telegram import Bot
import os

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME')

print(f"BOT_TOKEN: {BOT_TOKEN[:5]}...") # فقط اولش برای تست
print(f"CHANNEL_USERNAME: {CHANNEL_USERNAME}")

def get_selected_data():
    url = 'https://www.bonbast.com'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    targets = {
        'دلار آمریکا': '💵',
        'بیت‌کوین': '🪙',
        'تتر': '💳',
        'سکه امامی': '🏅',
        'نیم سکه': '🥈',
        'ربع سکه': '🥉',
        'طلا ۱۸ عیار': '🔸',
        'یورو': '🌍',
        'پوند': '🇬🇧',
        'درهم امارات': '🇦🇪'
    }

    result = '📊 قیمت‌های منتخب بازار ارز و طلا:\n\n'

    for row in soup.find_all('tr'):
        cells = row.find_all('td')
        if len(cells) >= 2:
            name = cells[0].text.strip()
            price = cells[1].text.strip()
            for target_name, emoji in targets.items():
                if target_name in name:
                    result += f'{emoji} {name}: {price} ریال\n'

    result += '\n#دلار #بیتکوین #تتر #سکه #طلا #یورو #پوند #درهم #ارزدیجیتال #بازار #اقتصاد #قیمت_لحظه‌ای #تحلیل_بازار'
    return result

def send_to_channel():
    bot = Bot(token=BOT_TOKEN)
    message = get_selected_data()
    print("Sending message to Telegram...")
    try:
        bot.send_message(chat_id=CHANNEL_USERNAME, text=message)
        print("Message sent successfully.")
    except Exception as e:
        print(f"Error sending message: {e}")

if __name__ == "__main__":
    send_to_channel()
