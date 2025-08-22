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
import json
import time

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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })

    def get_dollar_euro_prices(self):
        """دریافت قیمت دلار و یورو"""
        prices = {}
        
        # روش 1: از API معتبر Frankfurter (بانک مرکزی اروپا)
        try:
            logging.info("درخواست نرخ ارز از Frankfurter...")
            response = requests.get('https://api.frankfurter.app/latest?from=USD', timeout=10)
            if response.status_code == 200:
                data = response.json()
                eur_rate = data['rates'].get('EUR', 0.92)
                
                # نرخ دلار آزاد (براساس تخمین)
                # چون API ایرانی نداریم، از نرخ تتر استفاده می‌کنیم
                tether_price = self.get_tether_price_only()
                if tether_price:
                    dollar_price = int(tether_price * 0.98)  # دلار معمولا 2% از تتر کمتر
                    euro_price = int(dollar_price / eur_rate)
                    
                    prices['دلار آمریکا'] = f"{dollar_price:,} تومان"
                    prices['یورو'] = f"{euro_price:,} تومان"
                    logging.info(f"دلار: {dollar_price}, یورو: {euro_price}")
        except Exception as e:
            logging.error(f"خطا در Frankfurter: {e}")
        
        # روش 2: Web scraping از صرافی‌های آنلاین
        if not prices:
            try:
                logging.info("تلاش برای دریافت از منابع آنلاین...")
                
                # API رایگان exchangerate
                response = requests.get(
                    'https://open.er-api.com/v6/latest/USD',
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    if data['result'] == 'success':
                        # نرخ رسمی
                        irr_official = data['rates'].get('IRR', 42000)
                        eur_rate = data['rates'].get('EUR', 0.92)
                        
                        # تخمین نرخ آزاد (حدود 1.4 برابر رسمی)
                        dollar_price = int((irr_official / 10) * 1.4)
                        euro_price = int(dollar_price / eur_rate)
                        
                        if dollar_price > 50000:  # باید بیش از 50 هزار تومان باشد
                            prices['دلار آمریکا'] = f"{dollar_price:,} تومان"
                            prices['یورو'] = f"{euro_price:,} تومان"
                            logging.info(f"دلار و یورو از exchangerate")
            except Exception as e:
                logging.error(f"خطا در exchangerate: {e}")
        
        return prices

    def get_tether_price_only(self):
        """فقط برای گرفتن قیمت عددی تتر"""
        try:
            response = requests.get(
                'https://api.nobitex.ir/market/stats?srcCurrency=usdt&dstCurrency=rls',
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if 'stats' in data and 'usdt-rls' in data['stats']:
                    price_rial = float(data['stats']['usdt-rls']['latest'])
                    return int(price_rial / 10)
        except:
            pass
        return None

    def get_gold_coin_prices(self):
        """دریافت قیمت طلا و سکه"""
        prices = {}
        
        try:
            logging.info("درخواست قیمت طلا...")
            
            # قیمت جهانی طلا از metals.live
            response = requests.get(
                'https://api.metals.live/v1/spot/gold',
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    gold_usd_per_oz = float(data[0]['price'])
                    gold_usd_per_gram = gold_usd_per_oz / 31.1035
                    
                    # گرفتن قیمت دلار
                    tether_price = self.get_tether_price_only()
                    if tether_price:
                        dollar_price = int(tether_price * 0.98)
                        
                        # محاسبه قیمت طلای 18 عیار (75% خلوص + 20% سود و مالیات)
                        gold_18_price = int(gold_usd_per_gram * dollar_price * 0.75 * 1.20)
                        prices['طلای 18 عیار'] = f"{gold_18_price:,} تومان"
                        
                        # سکه امامی (8.133 گرم + 40% حباب)
                        coin_price = int(gold_18_price * 8.133 * 1.40)
                        prices['سکه امامی'] = f"{coin_price:,} تومان"
                        
                        logging.info(f"طلا: {gold_18_price}, سکه: {coin_price}")
        except Exception as e:
            logging.error(f"خطا در قیمت طلا: {e}")
        
        # روش جایگزین: از goldprice.org
        if 'طلای 18 عیار' not in prices:
            try:
                response = requests.get(
                    'https://api.goldapi.io/api/XAU/USD',
                    headers={'x-access-token': 'goldapi-demo-token'},  # توکن دمو
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    gold_usd_per_oz = float(data['price'])
                    gold_usd_per_gram = gold_usd_per_oz / 31.1035
                    
                    tether_price = self.get_tether_price_only()
                    if tether_price:
                        dollar_price = int(tether_price * 0.98)
                        gold_18_price = int(gold_usd_per_gram * dollar_price * 0.75 * 1.20)
                        prices['طلای 18 عیار'] = f"{gold_18_price:,} تومان"
                        coin_price = int(gold_18_price * 8.133 * 1.40)
                        prices['سکه امامی'] = f"{coin_price:,} تومان"
                        logging.info("قیمت طلا از goldapi")
            except Exception as e:
                logging.error(f"خطا در goldapi: {e}")
        
        return prices

    def get_crypto_prices(self):
        """دریافت قیمت کریپتو"""
        prices = {}
        
        # بیت‌کوین و اتریوم از Binance
        try:
            logging.info("درخواست به Binance...")
            
            # روش جدید: یک درخواست برای همه
            response = requests.get(
                'https://api.binance.com/api/v3/ticker/24hr',
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                for item in data:
                    if item['symbol'] == 'BTCUSDT':
                        btc_price = float(item['lastPrice'])
                        if btc_price > 0:
                            prices['بیت‌کوین'] = f"${btc_price:,.0f}"
                            logging.info(f"BTC: ${btc_price:,.0f}")
                    elif item['symbol'] == 'ETHUSDT':
                        eth_price = float(item['lastPrice'])
                        if eth_price > 0:
                            prices['اتریوم'] = f"${eth_price:,.0f}"
                            logging.info(f"ETH: ${eth_price:,.0f}")
        except Exception as e:
            logging.error(f"خطا در Binance: {e}")
        
        # اگر Binance کار نکرد
        if 'بیت‌کوین' not in prices:
            try:
                # از CoinCap
                response = requests.get('https://api.coincap.io/v2/rates/bitcoin', timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    btc_price = float(data['data']['rateUsd'])
                    prices['بیت‌کوین'] = f"${btc_price:,.0f}"
                    logging.info(f"BTC از CoinCap: ${btc_price:,.0f}")
            except:
                pass
        
        if 'اتریوم' not in prices:
            try:
                response = requests.get('https://api.coincap.io/v2/rates/ethereum', timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    eth_price = float(data['data']['rateUsd'])
                    prices['اتریوم'] = f"${eth_price:,.0f}"
                    logging.info(f"ETH از CoinCap: ${eth_price:,.0f}")
            except:
                pass
        
        # تتر
        tether_price = self.get_tether_price_only()
        if tether_price:
            prices['تتر (USDT)'] = f"{tether_price:,} تومان"
            logging.info(f"USDT: {tether_price}")
        
        return prices

    def collect_all_prices(self):
        """جمع‌آوری همه قیمت‌ها با retry"""
        all_prices = {}
        
        # تتر اول (برای محاسبه دلار)
        logging.info("مرحله 1: دریافت قیمت تتر...")
        tether = self.get_tether_price_only()
        if tether:
            all_prices['تتر (USDT)'] = f"{tether:,} تومان"
        
        # دلار و یورو
        logging.info("مرحله 2: دریافت دلار و یورو...")
        currency = self.get_dollar_euro_prices()
        all_prices.update(currency)
        
        # طلا و سکه
        logging.info("مرحله 3: دریافت طلا و سکه...")
        gold = self.get_gold_coin_prices()
        all_prices.update(gold)
        
        # کریپتو
        logging.info("مرحله 4: دریافت کریپتو...")
        crypto = self.get_crypto_prices()
        
        # جدا کردن کریپتو از بقیه
        main_prices = {k: v for k, v in all_prices.items() if 'بیت‌کوین' not in k and 'اتریوم' not in k and 'تتر' not in k}
        
        return main_prices, crypto

    def format_message(self, main_prices, crypto_prices):
        """فرمت کردن پیام"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"📊 گزارش قیمت‌های لحظه‌ای\n"
        message += f"🕐 زمان: {current_time}\n\n"
        
        # ارز و طلا
        if main_prices:
            message += "💰 بازار ارز و طلا:\n"
            if 'دلار آمریکا' in main_prices:
                message += f"💵 دلار آمریکا: {main_prices['دلار آمریکا']}\n"
            if 'یورو' in main_prices:
                message += f"💶 یورو: {main_prices['یورو']}\n"
            if 'طلای 18 عیار' in main_prices:
                message += f"🥇 طلای 18 عیار: {main_prices['طلای 18 عیار']}\n"
            if 'سکه امامی' in main_prices:
                message += f"🪙 سکه امامی: {main_prices['سکه امامی']}\n"
            message += "\n"
        
        # کریپتو
        if crypto_prices:
            message += "₿ ارزهای دیجیتال:\n"
            if 'بیت‌کوین' in crypto_prices:
                message += f"🟠 بیت‌کوین: {crypto_prices['بیت‌کوین']}\n"
            if 'اتریوم' in crypto_prices:
                message += f"🔵 اتریوم: {crypto_prices['اتریوم']}\n"
            if 'تتر (USDT)' in crypto_prices:
                message += f"🟢 تتر: {crypto_prices['تتر (USDT)']}\n"
            message += "\n"
        
        # اطلاعات تکمیلی
        total_items = len(main_prices) + len(crypto_prices)
        if total_items < 7:
            message += f"⚠️ توجه: {total_items} از 7 قیمت دریافت شد\n\n"
        
        message += "🔄 آپدیت بعدی: 30 دقیقه دیگر\n"
        message += "📱 @asle_tehran"
        
        return message

    async def send_message(self, message):
        """ارسال پیام به تلگرام"""
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message)
            logging.info("✅ پیام ارسال شد")
            return True
        except Exception as e:
            logging.error(f"❌ خطا در ارسال: {e}")
            return False

    def collect_and_send_prices(self):
        """جمع‌آوری و ارسال قیمت‌ها"""
        logging.info("=" * 60)
        logging.info("🚀 شروع جمع‌آوری قیمت‌ها...")
        
        try:
            # جمع‌آوری با تلاش مجدد
            max_retries = 3
            for attempt in range(max_retries):
                logging.info(f"تلاش {attempt + 1} از {max_retries}...")
                
                main_prices, crypto_prices = self.collect_all_prices()
                
                total = len(main_prices) + len(crypto_prices)
                logging.info(f"📊 مجموع قیمت‌های دریافتی: {total}")
                
                # نمایش در لاگ
                for name, price in {**main_prices, **crypto_prices}.items():
                    logging.info(f"  ✓ {name}: {price}")
                
                # اگر حداقل 4 قیمت گرفتیم، ارسال کن
                if total >= 4:
                    break
                elif attempt < max_retries - 1:
                    logging.warning(f"فقط {total} قیمت دریافت شد، تلاش مجدد...")
                    time.sleep(2)
            
            message = self.format_message(main_prices, crypto_prices)
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
    
    logging.info("🤖 ربات قیمت شروع به کار کرد")
    logging.info(f"📢 کانال: {CHAT_ID}")
    
    monitor = PriceMonitor(TELEGRAM_BOT_TOKEN, CHAT_ID)
    monitor.collect_and_send_prices()
    
    logging.info("✅ اجرا کامل شد")
    sys.exit(0)

if __name__ == "__main__":
    main()
