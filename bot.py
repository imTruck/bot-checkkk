
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import schedule
import time
import logging
import os
import signal
import sys
from datetime import datetime
import asyncio
from telegram import Bot
from telegram.error import TelegramError
import json
from pathlib import Path

# تنظیمات از متغیرهای محیطی
TELEGRAM_BOT_TOKEN = os.getenv('8011560580:AAE-lsa521NE3DfGKj247DC04cZOr27SuAY', '8011560580:AAE-lsa521NE3DfGKj247DC04cZOr27SuAY')
CHAT_ID = os.getenv('CHAT_ID', '@asle_tehran')
UPDATE_INTERVAL = int(os.getenv('UPDATE_INTERVAL', '30'))  # دقیقه
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# ایجاد پوشه logs
Path('logs').mkdir(exist_ok=True)

# تنظیم لاگ
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/price_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class PriceMonitor:
    def __init__(self, bot_token, chat_id):
        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.last_successful_update = None
        self.consecutive_failures = 0
        self.max_failures = 5

    def get_currency_prices(self):
        """دریافت قیمت ارزها از tgju.org"""
        try:
            url = "https://www.tgju.org/"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            prices = {}
            
            # استخراج قیمت دلار
            try:
                usd_element = soup.find('a', {'data-market-namad': 'price_dollar_rl'})
                if usd_element:
                    usd_price = usd_element.find('span', class_='info-price')
                    if usd_price:
                        prices['دلار آمریکا'] = usd_price.text.strip()
            except Exception as e:
                logging.warning(f"خطا در دریافت قیمت دلار: {e}")

            # استخراج قیمت یورو
            try:
                eur_element = soup.find('a', {'data-market-namad': 'price_eur'})
                if eur_element:
                    eur_price = eur_element.find('span', class_='info-price')
                    if eur_price:
                        prices['یورو'] = eur_price.text.strip()
            except Exception as e:
                logging.warning(f"خطا در دریافت قیمت یورو: {e}")

            # استخراج قیمت درهم
            try:
                aed_element = soup.find('a', {'data-market-namad': 'price_aed'})
                if aed_element:
                    aed_price = aed_element.find('span', class_='info-price')
                    if aed_price:
                        prices['درهم امارات'] = aed_price.text.strip()
            except Exception as e:
                logging.warning(f"خطا در دریافت قیمت درهم: {e}")

            return prices
            
        except requests.exceptions.RequestException as e:
            logging.error(f"خطا در دریافت داده‌های ارز: {e}")
            return {}

    def get_gold_prices(self):
        """دریافت قیمت طلا از tgju.org"""
        try:
            url = "https://www.tgju.org/gold-chart"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            prices = {}
            
            # استخراج قیمت طلای 18 عیار
            try:
                gold_18_element = soup.find('a', {'data-market-namad': 'gold18'})
                if gold_18_element:
                    gold_price = gold_18_element.find('span', class_='info-price')
                    if gold_price:
                        prices['طلای 18 عیار'] = gold_price.text.strip()
            except Exception as e:
                logging.warning(f"خطا در دریافت قیمت طلای 18 عیار: {e}")

            # استخراج قیمت سکه طرح جدید
            try:
                coin_element = soup.find('a', {'data-market-namad': 'sekee'})
                if coin_element:
                    coin_price = coin_element.find('span', class_='info-price')
                    if coin_price:
                        prices['سکه طرح جدید'] = coin_price.text.strip()
            except Exception as e:
                logging.warning(f"خطا در دریافت قیمت سکه: {e}")

            # استخراج قیمت نیم سکه
            try:
                half_coin_element = soup.find('a', {'data-market-namad': 'nim'})
                if half_coin_element:
                    half_coin_price = half_coin_element.find('span', class_='info-price')
                    if half_coin_price:
                        prices['نیم سکه'] = half_coin_price.text.strip()
            except Exception as e:
                logging.warning(f"خطا در دریافت قیمت نیم سکه: {e}")

            return prices
            
        except requests.exceptions.RequestException as e:
            logging.error(f"خطا در دریافت داده‌های طلا: {e}")
            return {}

    def get_bitcoin_price(self):
        """دریافت قیمت بیت‌کوین از tgju.org"""
        try:
            url = "https://www.tgju.org/crypto"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            prices = {}
            
            # استخراج قیمت بیت‌کوین
            try:
                btc_element = soup.find('a', {'data-market-namad': 'bitcoin'})
                if btc_element:
                    btc_price = btc_element.find('span', class_='info-price')
                    if btc_price:
                        prices['بیت‌کوین'] = btc_price.text.strip()
            except Exception as e:
                logging.warning(f"خطا در دریافت قیمت بیت‌کوین: {e}")

            # استخراج قیمت اتریوم
            try:
                eth_element = soup.find('a', {'data-market-namad': 'ethereum'})
                if eth_element:
                    eth_price = eth_element.find('span', class_='info-price')
                    if eth_price:
                        prices['اتریوم'] = eth_price.text.strip()
            except Exception as e:
                logging.warning(f"خطا در دریافت قیمت اتریوم: {e}")

            return prices
            
        except requests.exceptions.RequestException as e:
            logging.error(f"خطا در دریافت داده‌های ارز دیجیتال: {e}")
            return {}

    def format_message(self, currency_prices, gold_prices, crypto_prices):
        """فرمت کردن پیام برای ارسال"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"📊 **گزارش قیمت‌ها**\n"
        message += f"🕐 زمان آپدیت: {current_time}\n\n"
        
        # قیمت ارزها
        if currency_prices:
            message += "💰 **ارزهای خارجی:**\n"
            for currency, price in currency_prices.items():
                message += f"• {currency}: {price} ریال\n"
            message += "\n"
        
        # قیمت طلا
        if gold_prices:
            message += "🥇 **بازار طلا:**\n"
            for gold_type, price in gold_prices.items():
                message += f"• {gold_type}: {price} ریال\n"
            message += "\n"
        
        # قیمت ارزهای دیجیتال
        if crypto_prices:
            message += "₿ **ارزهای دیجیتال:**\n"
            for crypto, price in crypto_prices.items():
                message += f"• {crypto}: {price} دلار\n"
            message += "\n"
        
        message += f"🔄 آپدیت بعدی: {UPDATE_INTERVAL} دقیقه دیگر\n"
        message += f"✅ وضعیت: آنلاین | خطاهای متوالی: {self.consecutive_failures}"
        
        return message

    async def send_message(self, message):
        """ارسال پیام به تلگرام"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode='Markdown'
                )
                logging.info("پیام با موفقیت ارسال شد")
                return True
            except TelegramError as e:
                logging.warning(f"تلاش {attempt + 1}: خطا در ارسال پیام تلگرام: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(5)  # صبر 5 ثانیه قبل از تلاش مجدد
            except Exception as e:
                logging.error(f"خطای غیرمنتظره در ارسال پیام: {e}")
                break
        return False

    async def send_status_message(self, status_type):
        """ارسال پیام وضعیت"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if status_type == "start":
            message = f"🟢 **ربات قیمت شروع شد**\n🕐 زمان: {current_time}\n⏰ بازه آپدیت: هر {UPDATE_INTERVAL} دقیقه"
        elif status_type == "error":
            message = f"🔴 **خطای متوالی در دریافت قیمت‌ها**\n🕐 زمان: {current_time}\n⚠️ تعداد خطا: {self.consecutive_failures}"
        elif status_type == "recovery":
            message = f"🟡 **بازگشت به حالت عادی**\n🕐 زمان: {current_time}\n✅ دریافت قیمت‌ها با موفقیت انجام شد"
        
        await self.send_message(message)

    def save_prices_to_file(self, currency_prices, gold_prices, crypto_prices):
        """ذخیره قیمت‌ها در فایل JSON"""
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "currencies": currency_prices,
                "gold": gold_prices,
                "crypto": crypto_prices
            }
            
            with open('logs/latest_prices.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"خطا در ذخیره فایل: {e}")

    def collect_and_send_prices(self):
        """جمع‌آوری قیمت‌ها و ارسال پیام"""
        logging.info("شروع جمع‌آوری قیمت‌ها...")
        
        try:
            # دریافت قیمت‌ها
            currency_prices = self.get_currency_prices()
            gold_prices = self.get_gold_prices()
            crypto_prices = self.get_bitcoin_price()
            
            # بررسی اینکه حداقل یکی از قیمت‌ها دریافت شده باشد
            if not currency_prices and not gold_prices and not crypto_prices:
                self.consecutive_failures += 1
                logging.error(f"هیچ قیمتی دریافت نشد! خطای شماره {self.consecutive_failures}")
                
                # ارسال هشدار بعد از 5 خطای متوالی
                if self.consecutive_failures == self.max_failures:
                    asyncio.run(self.send_status_message("error"))
                
                return
            
            # اگر بعد از خطا، دوباره قیمت دریافت شد
            if self.consecutive_failures > 0:
                logging.info("بازگشت به حالت عادی بعد از خطا")
                asyncio.run(self.send_status_message("recovery"))
            
            self.consecutive_failures = 0
            self.last_successful_update = datetime.now()
            
            # ذخیره قیمت‌ها
            self.save_prices_to_file(currency_prices, gold_prices, crypto_prices)
            
            # فرمت کردن پیام
            message = self.format_message(currency_prices, gold_prices, crypto_prices)
            
            # ارسال پیام
            success = asyncio.run(self.send_message(message))
            
            if success:
                logging.info(f"آپدیت موفق در {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            self.consecutive_failures += 1
            logging.error(f"خطای کلی در جمع‌آوری قیمت‌ها: {e}")

def signal_handler(sig, frame):
    """مدیریت سیگنال‌های سیستم"""
    logging.info("دریافت سیگنال توقف. در حال خروج...")
    sys.exit(0)

def main():
    """تابع اصلی برنامه"""
    # ثبت signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # بررسی تنظیمات
    if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or CHAT_ID == "YOUR_CHAT_ID_HERE":
        logging.error("❌ لطفاً TOKEN و CHAT_ID را تنظیم کنید!")
        sys.exit(1)
    
    # ایجاد نمونه کلاس
    monitor = PriceMonitor(TELEGRAM_BOT_TOKEN, CHAT_ID)
    
    # ارسال پیام شروع
    logging.info("ارسال پیام شروع...")
    asyncio.run(monitor.send_status_message("start"))
    
    # تست اولیه
    logging.info("تست اولیه ربات...")
    monitor.collect_and_send_prices()
    
    # زمان‌بندی
    schedule.every(UPDATE_INTERVAL).minutes.do(monitor.collect_and_send_prices)
    
    logging.info(f"ربات شروع به کار کرد. آپدیت هر {UPDATE_INTERVAL} دقیقه.")
    
    # حلقه اصلی
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)  # بررسی هر 30 ثانیه
    except KeyboardInterrupt:
        logging.info("ربات توسط کاربر متوقف شد.")
    except Exception as e:
        logging.error(f"خطای کلی در برنامه: {e}")
        # تلاش برای ارسال پیام خطا
        try:
            error_message = f"🔴 **خطای کلی در ربات**\n```\n{str(e)}\n```"
            asyncio.run(monitor.send_message(error_message))
        except:
            pass

if __name__ == "__main__":
    main()
