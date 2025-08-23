#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import schedule
import time
import logging
import os
from datetime import datetime
import asyncio
from telegram import Bot
from telegram.error import TelegramError
import json
import re
import pytz
from persiantools.jdatetime import JalaliDate, JalaliDateTime

# تنظیمات
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8011560580:AAE-lsa521NE3DfGKj247DC04cZOr27SuAY')
CHAT_ID = os.getenv('CHAT_ID', '@asle_tehran')
UPDATE_INTERVAL = int(os.getenv('UPDATE_INTERVAL', '30'))  # دقیقه

# تنظیم لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class PriceMonitor:
    def __init__(self, bot_token, chat_id):
        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/html',
            'Accept-Language': 'fa-IR,fa;q=0.9,en;q=0.8',
            'Referer': 'https://www.tgju.org/'
        })

    def get_tehran_time(self):
        """دریافت زمان تهران به شمسی"""
        # تنظیم منطقه زمانی تهران
        tehran_tz = pytz.timezone('Asia/Tehran')
        tehran_time = datetime.now(tehran_tz)
        
        # تبدیل به تاریخ شمسی
        jalali = JalaliDateTime.now(tehran_tz)
        
        # روزهای هفته به فارسی - اصلاح شده برای تقویم شمسی
        # در تقویم شمسی: شنبه = 0, یکشنبه = 1, ... جمعه = 6
        weekdays = {
            5: 'شنبه',      # Saturday
            6: 'یکشنبه',    # Sunday
            0: 'دوشنبه',    # Monday
            1: 'سه‌شنبه',    # Tuesday
            2: 'چهارشنبه',  # Wednesday
            3: 'پنج‌شنبه',   # Thursday
            4: 'جمعه'       # Friday
        }
        
        # ماه‌های شمسی
        months = {
            1: 'فروردین',
            2: 'اردیبهشت',
            3: 'خرداد',
            4: 'تیر',
            5: 'مرداد',
            6: 'شهریور',
            7: 'مهر',
            8: 'آبان',
            9: 'آذر',
            10: 'دی',
            11: 'بهمن',
            12: 'اسفند'
        }
        
        # دریافت روز هفته میلادی و تبدیل به شمسی
        gregorian_weekday = tehran_time.weekday()
        weekday = weekdays[gregorian_weekday]
        month = months[jalali.month]
        
        # فرمت: شنبه، ۱ شهریور ۱۴۰۳ - ۱۹:۰۴
        date_str = f"{weekday}، {jalali.day} {month} {jalali.year}"
        time_str = f"{jalali.hour:02d}:{jalali.minute:02d}"
        
        return date_str, time_str

    def get_tgju_prices(self):
        """دریافت قیمت از TGJU"""
        prices = {}
        
        try:
            # API اصلی TGJU
            response = self.session.get('https://api.tgju.org/v1/market/indicator/summary-table-data', timeout=10)
            if response.status_code == 200:
                data = response.json()
                logging.info(f"TGJU API Response: {json.dumps(data[:5] if isinstance(data, list) else data, ensure_ascii=False)[:500]}")
                
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            title = item.get('title', '')
                            price = item.get('p') or item.get('price') or item.get('value')
                            
                            if price:
                                # دلار
                                if 'دلار' in title or 'dollar' in title.lower() or 'usd' in title.lower():
                                    prices['دلار آمریکا'] = f"{int(price // 10):,} تومان"
                                # یورو
                                elif 'یورو' in title or 'euro' in title.lower() or 'eur' in title.lower():
                                    prices['یورو'] = f"{int(price // 10):,} تومان"
                                # طلا
                                elif 'طلا' in title and '18' in title:
                                    prices['طلای 18 عیار'] = f"{int(price // 10):,} تومان"
                                # سکه
                                elif 'سکه' in title and ('امامی' in title or 'emami' in title.lower()):
                                    prices['سکه امامی'] = f"{int(price // 10):,} تومان"
                
                logging.info(f"قیمت‌های استخراج شده از API: {prices}")
        except Exception as e:
            logging.error(f"خطا در TGJU API: {e}")
        
        # اگر قیمتی نگرفتیم، از API دیگر تلاش کن
        if not prices:
            try:
                response = self.session.get('https://api.tgju.org/v1/data/sana/json', timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    
                    # دلار
                    if 'sana_buy_usd' in data:
                        prices['دلار آمریکا'] = f"{int(data['sana_buy_usd']['p'] // 10):,} تومان"
                    # یورو  
                    if 'sana_buy_eur' in data:
                        prices['یورو'] = f"{int(data['sana_buy_eur']['p'] // 10):,} تومان"
                    # طلا
                    if 'geram18' in data:
                        prices['طلای 18 عیار'] = f"{int(data['geram18']['p'] // 10):,} تومان"
                    # سکه
                    if 'sekee' in data:
                        prices['سکه امامی'] = f"{int(data['sekee']['p'] // 10):,} تومان"
                        
            except Exception as e:
                logging.error(f"خطا در API دوم: {e}")
        
        # از صفحه اصلی TGJU
        if len(prices) < 4:
            try:
                response = self.session.get('https://www.tgju.org/', timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # جستجوی جدول قیمت‌ها
                    tables = soup.find_all('table', class_='data-table')
                    for table in tables:
                        rows = table.find_all('tr')
                        for row in rows:
                            cells = row.find_all(['td', 'th'])
                            if len(cells) >= 2:
                                name = cells[0].get_text().strip()
                                value = cells[1].get_text().strip()
                                
                                # حذف کاراکترهای اضافی و استخراج عدد
                                value_clean = re.sub(r'[^\d,]', '', value)
                                if value_clean:
                                    value_num = int(value_clean.replace(',', ''))
                                    
                                    if 'دلار' in name and 'دلار آمریکا' not in prices:
                                        prices['دلار آمریکا'] = f"{value_num // 10:,} تومان"
                                    elif 'یورو' in name and 'یورو' not in prices:
                                        prices['یورو'] = f"{value_num // 10:,} تومان"
                                    elif 'طلا' in name and '18' in name and 'طلای 18 عیار' not in prices:
                                        prices['طلای 18 عیار'] = f"{value_num // 10:,} تومان"
                                    elif 'سکه' in name and 'امامی' in name and 'سکه امامی' not in prices:
                                        prices['سکه امامی'] = f"{value_num // 10:,} تومان"
                    
            except Exception as e:
                logging.error(f"خطا در صفحه اصلی: {e}")
        
        # اگر هنوز کامل نیست
        if 'طلای 18 عیار' not in prices:
            prices['طلای 18 عیار'] = "🔄 در حال آپدیت"
        if 'سکه امامی' not in prices:
            prices['سکه امامی'] = "🔄 در حال آپدیت"
        if 'دلار آمریکا' not in prices:
            prices['دلار آمریکا'] = "🔄 در حال آپدیت"
        if 'یورو' not in prices:
            prices['یورو'] = "🔄 در حال آپدیت"
            
        return prices

    def get_tether_price(self):
        """دریافت قیمت تتر"""
        try:
            # از Nobitex
            response = self.session.get('https://api.nobitex.ir/v2/orderbook/USDTIRT', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'lastTradePrice' in data:
                    price = int(float(data['lastTradePrice']) / 10)
                    return f"{price:,} تومان"
        except:
            pass
        
        try:
            # از API دیگر Nobitex
            response = self.session.get('https://api.nobitex.ir/market/stats?srcCurrency=usdt&dstCurrency=rls', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'stats' in data:
                    stats = data['stats']
                    if 'usdt-rls' in stats:
                        price = int(float(stats['usdt-rls']['latest']) / 10)
                        return f"{price:,} تومان"
        except:
            pass
            
        return "🔄 در حال آپدیت"

    def get_crypto_prices(self):
        """دریافت قیمت کریپتو"""
        prices = {}
        
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'bitcoin' in data:
                    btc_price = data['bitcoin']['usd']
                    prices['بیت‌کوین'] = f"${btc_price:,.0f}"
                if 'ethereum' in data:
                    eth_price = data['ethereum']['usd']
                    prices['اتریوم'] = f"${eth_price:,.0f}"
        except:
            prices['بیت‌کوین'] = "🔄 در حال آپدیت"
            prices['اتریوم'] = "🔄 در حال آپدیت"
        
        return prices

    def format_message(self, main_prices, tether_price, crypto_prices):
        """فرمت کردن پیام"""
        date_str, time_str = self.get_tehran_time()
        
        message = f"📊 قیمت‌های لحظه‌ای\n"
        message += f"📅 {date_str}\n"
        message += f"🕐 ساعت {time_str} - تهران\n\n"
        
        # ارز و طلا
        message += "💰 بازار ارز و طلا:\n"
        
        # دلار
        if 'دلار آمریکا' in main_prices:
            message += f"💵 دلار آمریکا: {main_prices['دلار آمریکا']}\n"
        
        # یورو
        if 'یورو' in main_prices:
            message += f"💶 یورو: {main_prices['یورو']}\n"
            
        # تتر
        message += f"💳 تتر (USDT): {tether_price}\n"
        
        # طلا
        if 'طلای 18 عیار' in main_prices:
            message += f"🥇 طلای 18 عیار: {main_prices['طلای 18 عیار']}\n"
        
        # سکه
        if 'سکه امامی' in main_prices:
            message += f"🪙 سکه امامی: {main_prices['سکه امامی']}\n"
        
        message += "\n"
        
        # کریپتو
        message += "₿ ارزهای دیجیتال:\n"
        for crypto, price in crypto_prices.items():
            if 'بیت‌کوین' in crypto:
                message += f"🟠 {crypto}: {price}\n"
            elif 'اتریوم' in crypto:
                message += f"🔵 {crypto}: {price}\n"
        
        message += f"\n🔄 آپدیت بعدی: {UPDATE_INTERVAL} دقیقه دیگر\n"
        message += "📱 @asle_tehran"
        
        return message

    async def send_message(self, message):
        """ارسال پیام به تلگرام"""
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message)
            logging.info("پیام ارسال شد")
            return True
        except TelegramError as e:
            logging.error(f"خطا در تلگرام: {e}")
            return False

    def collect_and_send_prices(self):
        """جمع‌آوری و ارسال قیمت‌ها"""
        logging.info("شروع جمع‌آوری قیمت‌ها...")
        
        try:
            # دریافت قیمت‌ها
            main_prices = self.get_tgju_prices()
            tether_price = self.get_tether_price()
            crypto_prices = self.get_crypto_prices()
            
            logging.info(f"قیمت‌های اصلی: {main_prices}")
            logging.info(f"قیمت تتر: {tether_price}")
            logging.info(f"قیمت کریپتو: {crypto_prices}")
            
            # ساخت پیام
            message = self.format_message(main_prices, tether_price, crypto_prices)
            
            # ارسال پیام
            success = asyncio.run(self.send_message(message))
            
            if success:
                logging.info("✅ پیام با موفقیت ارسال شد")
            else:
                logging.error("❌ خطا در ارسال پیام")
                
        except Exception as e:
            logging.error(f"خطای کلی: {e}")

def main():
    # برای GitHub Actions
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN', TELEGRAM_BOT_TOKEN)
    chat_id = os.getenv('CHAT_ID', CHAT_ID)
    
    if not bot_token or bot_token == "YOUR_BOT_TOKEN_HERE":
        print("❌ لطفاً TOKEN را تنظیم کنید!")
        return
    
    monitor = PriceMonitor(bot_token, chat_id)
    
    # فقط یکبار اجرا برای GitHub Actions
    logging.info("ارسال قیمت‌ها...")
    monitor.collect_and_send_prices()
    logging.info("✅ انجام شد")

if __name__ == "__main__":
    main()
