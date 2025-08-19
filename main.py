from telegram import Bot
import os

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME')

bot = Bot(token=BOT_TOKEN)
bot.send_message(chat_id=CHANNEL_USERNAME, text='✅ تست اتصال ربات به کانال')
