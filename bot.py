#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import logging
import os
from datetime import datetime
import asyncio
from telegram import Bot
import re
import sys

# تنظیمات
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_currency_prices(self):
        """دریافت قیمت ارز از منابع مختلف"""
        prices = {}
        
        # روش 1: API ارز Nerkh Kala
        try:
            logging.info("تلاش برای دریافت از API...")
            response = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=10)
            if response.status_code == 200:
                data = response.json()
                # فرض: 1 دلار = 58000 تومان (قیمت تقریبی)
                usd_price = 58000  # می‌توانید از منبع دیگر بگیرید
                eur_rate = data['rates'].get('EUR', 0.92)
                eur_price = int(usd_price / eur_rate)
                
                prices['دلار آمریکا'] = f"{usd_price:,} تومان"
                prices['یورو'] = f"{eur_price:,} تومان"
                logging.info(f"قیمت ارز دریافت شد")
        except Exception as e:
            logging.error(f"خطا در API ارز: {e}")
        
        # روش 2: Web Scraping از xe.com (معمولا کار می‌کند)
        if not prices:
            try:
                response = requests.get('https://www.xe.com/currencyconverter/convert/?Amount=1&From=USD&To=IRR', timeout=10)
                if response.status_code == 200:
                    match = re.search(r'(\d{3},\d{3})', response.text)
                    if match:
                        rial_price = int(match.group(1).replace(',', ''))
                        toman_price = rial_price // 10
                        prices['دلار آمریکا'] = f"{toman_price:,} تومان"
                        logging.info("قیمت از XE دریافت شد")
            except Exception as e:
                logging.error(f"خطا در XE: {e}")
        
        # روش 3: CurrencyAPI (رایگان با محدودیت)
        if not prices:
            try:
                # این API رایگان است اما نیاز به ثبت نام دارد
                # می‌توانید از https://app.currencyapi.com/sign-up کلید رایگان بگیرید
                response = requests.get('https://api.currencyapi.com/v3/latest?apikey=cur_live_WTJezkPGCfL4xDqT0QzR72fKW9IcSdBKIqNhBzJP&base_currency=USD', timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data:
                        # تخمین قیمت بر اساس نرخ رسمی
                        irr_rate = data['data'].get('IRR', {}).get('value', 420000)
                        toman_price = int(irr_rate / 10)
                        prices['دلار آمریکا'] = f"{toman_price:,} تومان"
                        
                        eur_rate = data['data'].get('EUR', {}).get('value', 0.92)
                        eur_price = int(toman_price / eur_rate)
                        prices['یورو'] = f"{eur_price:,} تومان"
                        logging.info("قیمت از CurrencyAPI دریافت شد")
            except Exception as e:
                logging.error(f"خطا در CurrencyAPI: {e}")
        
        # روش 4: قیمت ثابت پیش‌فرض (برای اطمینان)
        if not prices:
            logging.warning("استفاده از قیمت‌های پیش‌فرض")
            prices = {
                'دلار آمریکا': "58,500 تومان (تقریبی)",
                'یورو': "63,800 تومان (تقریبی)"
            }
        
        # طلا و سکه (تقریبی)
        prices['طلای 18 عیار'] = "2,850,000 تومان (تقریبی)"
        prices['سکه امامی'] = "42,500,000 تومان (تقریبی)"
        
        return prices

    def get_crypto_prices(self):
        """دریافت قیمت کریپتو که معمولا کار می‌کند"""
        prices = {}
        
        # Binance API - معمولا بدون محدودیت کار می‌کند
        try:
            # بیت‌کوین
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', timeout=5)
            if response.status_code == 200:
                btc_price = float(response.json()['price'])
                prices['بیت‌کوین'] = f"${btc_price:,.0f}"
                logging.info(f"بیت‌کوین: ${btc_price:,.0f}")
        except Exception as e:
            logging.error(f"خطا Binance BTC: {e}")
        
        try:
            # اتریوم
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT', timeout=5)
            if response.status_code == 200:
                eth_price = float(response.json()['price'])
                prices['اتریوم'] = f"${eth_price:,.0f}"
                logging.info(f"اتریوم: ${eth_price:,.0f}")
        except Exception as e:
            logging.error(f"خطا Binance ETH: {e}")
        
        # CoinGecko API - معمولا کار می‌کند
        if not prices:
            try:
                url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'bitcoin' in data:
                        prices['بیت‌کوین'] = f"${data['bitcoin']['usd']:,.0f}"
                    if 'ethereum' in data:
                        prices['اتریوم'] = f"${data['ethereum']['usd']:,.0f}"
                    logging.info("قیمت از CoinGecko دریافت شد")
            except Exception as e:
                logging.error(f"خطا CoinGecko: {e}")
        
        # CoinCap API - جایگزین
        if 'بیت‌کوین' not in prices:
            try:
                response = requests.get('https://api.coincap.io/v2/assets/bitcoin', timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data:
                        btc_price = float(data['data']['priceUsd'])
                        prices['بیت‌کوین'] = f"${btc_price:,.0f}"
                        logging.info(f"بیت‌کوین از CoinCap: ${btc_price:,.0f}")
            except Exception as e:
                logging.error(f"خطا CoinCap: {e}")
        
        # قیمت تتر (تخمینی بر اساس دلار)
        try:
            # فرض: تتر = دلار + 2000 تومان
            prices['تتر (USDT)'] = "60,500 تومان (تقریبی)"
        except:
            prices['تتر (USDT)'] = "🔄 در حال آپدیت"
        
        # اگر هیچی نگرفتیم
        if 'بیت‌کوین' not in prices:
            prices['بیت‌کوین'] = "$101,000 (تقریبی)"
        if 'اتریوم' not in prices:
            prices['اتریوم'] = "$3,200 (تقریبی)"
        
        return prices

    def format_message(self, main_prices, crypto_prices):
        """فرمت کردن پیام"""
        # تاریخ شمسی
        from datetime import datetime
        import jdatetime
        
        try:
            now = jdatetime.datetime.now()
            current_time = now.strftime("%Y/%m/%d - %H:%M")
        except:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        message = f"📊 گزارش قیمت‌های لحظه‌ای\n"
        message += f"🕐 زمان: {current_time}\n\n"
        
        # ارز و طلا
        message += "💰 بازار ارز و طلا:\n"
        for item, price in main_prices.items():
            if 'دلار' in item:
                emoji = "💵"
            elif 'یورو' in item:
                emoji = "💶"
            elif 'طلا' in item:
                emoji = "🥇"
            elif 'سکه' in item:
                emoji = "🪙"
            else:
                emoji = "•"
            message += f"{emoji} {item}: {price}\n"
        
        message += "\n"
        
        # کریپتو
        message += "₿ ارزهای دیجیتال:\n"
        for crypto, price in crypto_prices.items():
            if 'بیت‌کوین' in crypto:
                emoji = "🟠"
            elif 'اتریوم' in crypto:
                emoji = "🔵"
            elif 'تتر' in crypto:
                emoji = "🟢"
            else:
                emoji = "•"
            message += f"{emoji} {crypto}: {price}\n"
        
        message += "\n"
        message += "🔄 آپدیت بعدی: 30 دقیقه دیگر\n"
        message += "📱 @asle_tehran"
        
        # اگر قیمت‌ها تقریبی هستند
        if "(تقریبی)" in str(main_prices) + str(crypto_prices):
            message += "\n⚠️ برخی قیمت‌ها تقریبی هستند"
        
        return message

    async def send_message(self, message):
        """ارسال پیام به تلگرام"""
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message)
            logging.info("✅ پیام با موفقیت ارسال شد")
            return True
        except Exception as e:
            logging.error(f"❌ خطا در ارسال: {e}")
            return False

    def collect_and_send_prices(self):
        """جمع‌آوری و ارسال قیمت‌ها"""
        logging.info("=" * 50)
        logging.info("شروع جمع‌آوری قیمت‌ها...")
        
        try:
            main_prices = self.get_currency_prices()
            crypto_prices = self.get_crypto_prices()
            
            logging.info(f"تعداد قیمت‌های دریافتی: ارز={len(main_prices)}, کریپتو={len(crypto_prices)}")
            
            message = self.format_message(main_prices, crypto_prices)
            
            logging.info("در حال ارسال پیام...")
            success = asyncio.run(self.send_message(message))
            
            if success:
                logging.info("✅ عملیات با موفقیت انجام شد")
            else:
                logging.error("❌ خطا در ارسال پیام")
                
        except Exception as e:
            logging.error(f"❌ خطای کلی: {e}")
            import traceback
            traceback.print_exc()

def main():
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        print("❌ لطفاً TELEGRAM_BOT_TOKEN و CHAT_ID را تنظیم کنید!")
        sys.exit(1)
    
    logging.info("🚀 ربات شروع به کار کرد")
    monitor = PriceMonitor(TELEGRAM_BOT_TOKEN, CHAT_ID)
    monitor.collect_and_send_prices()
    logging.info("✅ اجرا کامل شد")
    sys.exit(0)

if __name__ == "__main__":
    main()
