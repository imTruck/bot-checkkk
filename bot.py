#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import logging
import os
from datetime import datetime
import asyncio
from telegram import Bot
import sys
import re

# تنظیمات
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# تنظیم لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class PriceCollector:
    def __init__(self, bot_token, chat_id):
        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def get_crypto_prices(self):
        """دریافت قیمت کریپتو از API های معتبر"""
        prices = {}
        
        # روش 1: Binance API (کار می‌کنه)
        try:
            logging.info("دریافت BTC از Binance API...")
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', timeout=5)
            if response.status_code == 200:
                data = response.json()
                btc_price = float(data['price'])
                if 10000 <= btc_price <= 200000:  # محدوده منطقی
                    prices['بیت‌کوین'] = f"${btc_price:,.0f}"
                    logging.info(f"✓ BTC: ${btc_price:,.0f}")
            
            logging.info("دریافت ETH از Binance API...")
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT', timeout=5)
            if response.status_code == 200:
                data = response.json()
                eth_price = float(data['price'])
                if 1000 <= eth_price <= 15000:  # محدوده منطقی
                    prices['اتریوم'] = f"${eth_price:,.0f}"
                    logging.info(f"✓ ETH: ${eth_price:,.0f}")
        except Exception as e:
            logging.error(f"خطا در Binance API: {e}")
        
        # روش 2: CoinCap API (اگر Binance کار نکرد)
        if 'بیت‌کوین' not in prices:
            try:
                response = requests.get('https://api.coincap.io/v2/assets/bitcoin', timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    btc_price = float(data['data']['priceUsd'])
                    if 10000 <= btc_price <= 200000:
                        prices['بیت‌کوین'] = f"${btc_price:,.0f}"
                        logging.info(f"✓ BTC از CoinCap: ${btc_price:,.0f}")
            except:
                pass
        
        if 'اتریوم' not in prices:
            try:
                response = requests.get('https://api.coincap.io/v2/assets/ethereum', timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    eth_price = float(data['data']['priceUsd'])
                    if 1000 <= eth_price <= 15000:
                        prices['اتریوم'] = f"${eth_price:,.0f}"
                        logging.info(f"✓ ETH از CoinCap: ${eth_price:,.0f}")
            except:
                pass
        
        return prices

    def get_dollar_price(self):
        """دریافت قیمت دلار از چند منبع"""
        
        # منبع 1: Bonbast
        try:
            logging.info("دریافت دلار از Bonbast...")
            response = self.session.get('https://bonbast.com/', timeout=10)
            if response.status_code == 200:
                html = response.text
                
                # جستجوی قیمت دلار
                patterns = [
                    r'"usd":\s*{\s*"sell":\s*"?(\d+)"?',
                    r'USD.*?(\d{2},\d{3})',
                    r'>(\d{2},\d{3})<.*?دلار'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, html, re.IGNORECASE)
                    if match:
                        price_str = match.group(1).replace(',', '')
                        if price_str.isdigit():
                            price = int(price_str)
                            if 60000 <= price <= 110000:  # محدوده واقعی دلار
                                logging.info(f"✓ دلار از Bonbast: {price:,}")
                                return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا در Bonbast: {e}")
        
        # منبع 2: TGJU صفحه مستقیم
        try:
            logging.info("دریافت دلار از TGJU...")
            response = self.session.get('https://www.tgju.org/profile/price_dollar_rl', timeout=10)
            if response.status_code == 200:
                html = response.text
                
                # جستجو در محتوای صفحه
                patterns = [
                    r'قیمت فعلی.*?(\d{2},\d{3})',
                    r'نرخ.*?(\d{2},\d{3})',
                    r'>(\d{2},\d{3})<'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, html)
                    for match in matches:
                        price_str = match.replace(',', '')
                        if price_str.isdigit():
                            price = int(price_str)
                            if 60000 <= price <= 110000:
                                logging.info(f"✓ دلار از TGJU: {price:,}")
                                return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا در TGJU دلار: {e}")
        
        return None

    def get_gold_price(self):
        """دریافت قیمت طلای 18 عیار"""
        
        # منبع 1: TGJU
        try:
            logging.info("دریافت طلا از TGJU...")
            response = self.session.get('https://www.tgju.org/profile/geram18', timeout=10)
            if response.status_code == 200:
                html = response.text
                
                patterns = [
                    r'قیمت فعلی.*?(\d{1,2},\d{3},\d{3})',
                    r'نرخ.*?(\d{1,2},\d{3},\d{3})',
                    r'>(\d{1,2},\d{3},\d{3})<'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, html)
                    for match in matches:
                        price_str = match.replace(',', '')
                        if price_str.isdigit():
                            price = int(price_str)
                            if 2500000 <= price <= 5000000:  # محدوده واقعی طلا
                                logging.info(f"✓ طلا از TGJU: {price:,}")
                                return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا در TGJU طلا: {e}")
        
        # منبع 2: TalaOnline
        try:
            logging.info("دریافت طلا از TalaOnline...")
            response = self.session.get('https://www.talaonline.com/', timeout=10)
            if response.status_code == 200:
                html = response.text
                
                patterns = [
                    r'18.*?عیار.*?(\d{1,2},\d{3},\d{3})',
                    r'طلای 18.*?(\d{1,2},\d{3},\d{3})'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, html)
                    for match in matches:
                        price_str = match.replace(',', '')
                        if price_str.isdigit():
                            price = int(price_str)
                            if 2500000 <= price <= 5000000:
                                logging.info(f"✓ طلا از TalaOnline: {price:,}")
                                return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا در TalaOnline: {e}")
        
        return None

    def get_coin_price(self):
        """دریافت قیمت سکه امامی"""
        
        # منبع 1: TGJU
        try:
            logging.info("دریافت سکه از TGJU...")
            response = self.session.get('https://www.tgju.org/profile/sekee', timeout=10)
            if response.status_code == 200:
                html = response.text
                
                patterns = [
                    r'قیمت فعلی.*?(\d{2},\d{3},\d{3})',
                    r'نرخ.*?(\d{2},\d{3},\d{3})',
                    r'>(\d{2},\d{3},\d{3})<'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, html)
                    for match in matches:
                        price_str = match.replace(',', '')
                        if price_str.isdigit():
                            price = int(price_str)
                            if price > 100000000:  # اگر ریال است، تبدیل به تومان
                                price = price // 10
                            if 30000000 <= price <= 70000000:  # محدوده واقعی سکه
                                logging.info(f"✓ سکه از TGJU: {price:,}")
                                return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا در TGJU سکه: {e}")
        
        # منبع 2: TalaOnline  
        try:
            logging.info("دریافت سکه از TalaOnline...")
            response = self.session.get('https://www.talaonline.com/', timeout=10)
            if response.status_code == 200:
                html = response.text
                
                patterns = [
                    r'سکه.*?امامی.*?(\d{2},\d{3},\d{3})',
                    r'امامی.*?(\d{2},\d{3},\d{3})'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, html)
                    for match in matches:
                        price_str = match.replace(',', '')
                        if price_str.isdigit():
                            price = int(price_str)
                            if price > 100000000:
                                price = price // 10
                            if 30000000 <= price <= 70000000:
                                logging.info(f"✓ سکه از TalaOnline: {price:,}")
                                return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا در TalaOnline سکه: {e}")
        
        return None

    def get_tether_price(self):
        """دریافت قیمت تتر از API صرافی‌ها"""
        
        # منبع 1: Nobitex API
        try:
            logging.info("دریافت تتر از Nobitex API...")
            response = requests.get(
                'https://api.nobitex.ir/market/stats?srcCurrency=usdt&dstCurrency=rls',
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if 'stats' in data and 'usdt-rls' in data['stats']:
                    price_rial = float(data['stats']['usdt-rls']['latest'])
                    price_toman = int(price_rial / 10)
                    if 70000 <= price_toman <= 120000:  # محدوده واقعی تتر
                        logging.info(f"✓ تتر از Nobitex: {price_toman:,}")
                        return f"{price_toman:,} تومان"
        except Exception as e:
            logging.error(f"خطا در Nobitex: {e}")
        
        return None

    def collect_and_send_prices(self):
        """جمع‌آوری و ارسال قیمت‌ها"""
        logging.info("=" * 50)
        logging.info("🚀 شروع جمع‌آوری قیمت‌ها...")
        
        try:
            # جمع‌آوری قیمت‌ها
            dollar = self.get_dollar_price()
            tether = self.get_tether_price()
            gold = self.get_gold_price()
            coin = self.get_coin_price()
            crypto = self.get_crypto_prices()
            
            # ساخت پیام
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            message = f"📊 قیمت‌های لحظه‌ای\n"
            message += f"🕐 آپدیت: {current_time}\n\n"
            
            # بازار ارز و طلا
            message += "💰 بازار ارز و طلا:\n"
            message += f"💵 دلار آمریکا: {dollar if dollar else '🔄 در حال آپدیت'}\n"
            message += f"💳 تتر: {tether if tether else '🔄 در حال آپدیت'}\n"
            message += f"🥇 طلای 18 عیار: {gold if gold else '🔄 در حال آپدیت'}\n"
            message += f"🪙 سکه امامی: {coin if coin else '🔄 در حال آپدیت'}\n\n"
            
            # ارزهای دیجیتال
            message += "₿ ارزهای دیجیتال:\n"
            message += f"🟠 بیت‌کوین: {crypto.get('بیت‌کوین', '🔄 در حال آپدیت')}\n"
            message += f"🔵 اتریوم: {crypto.get('اتریوم', '🔄 در حال آپدیت')}\n\n"
            
            message += "🔄 آپدیت بعدی: 30 دقیقه دیگر\n"
            message += "📱 @asle_tehran"
            
            # لاگ نتایج
            results = {
                'دلار آمریکا': dollar,
                'تتر': tether, 
                'طلای 18 عیار': gold,
                'سکه امامی': coin,
                **crypto
            }
            
            success_count = sum(1 for v in results.values() if v is not None)
            logging.info(f"📊 نتایج: {success_count}/6 قیمت موفق")
            
            for name, price in results.items():
                status = "✓" if price else "✗"
                logging.info(f"  {status} {name}: {price if price else 'ناموفق'}")
            
            # ارسال پیام
            success = asyncio.run(self.send_message(message))
            
            if success:
                logging.info("✅ پیام ارسال شد")
            else:
                logging.error("❌ خطا در ارسال")
                
        except Exception as e:
            logging.error(f"❌ خطای کلی: {e}")
            import traceback
            traceback.print_exc()

    async def send_message(self, message):
        """ارسال پیام به تلگرام"""
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message)
            return True
        except Exception as e:
            logging.error(f"خطا در ارسال: {e}")
            return False

def main():
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        print("❌ لطفاً TELEGRAM_BOT_TOKEN و CHAT_ID را تنظیم کنید!")
        sys.exit(1)
    
    logging.info("🤖 ربات قیمت شروع شد")
    collector = PriceCollector(TELEGRAM_BOT_TOKEN, CHAT_ID)
    collector.collect_and_send_prices()
    logging.info("✅ پایان")
    sys.exit(0)

if __name__ == "__main__":
    main()
