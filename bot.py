#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import logging
import os
from datetime import datetime
import asyncio
from telegram import Bot
import sys
import re
import json

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

    def get_crypto_and_tether(self):
        """دریافت کریپتو و تتر - بدون تغییر"""
        prices = {}
        
        # بیت‌کوین از Binance
        try:
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', timeout=8)
            if response.status_code == 200:
                btc_price = float(response.json()['price'])
                prices['بیت‌کوین'] = f"${btc_price:,.0f}"
                logging.info(f"✓ BTC: ${btc_price:,.0f}")
        except Exception as e:
            logging.error(f"خطا BTC: {e}")
        
        # اتریوم از Binance
        try:
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT', timeout=8)
            if response.status_code == 200:
                eth_price = float(response.json()['price'])
                prices['اتریوم'] = f"${eth_price:,.0f}"
                logging.info(f"✓ ETH: ${eth_price:,.0f}")
        except Exception as e:
            logging.error(f"خطا ETH: {e}")
        
        # تتر از Nobitex API
        try:
            response = requests.get('https://api.nobitex.ir/market/stats?srcCurrency=usdt&dstCurrency=rls', timeout=8)
            if response.status_code == 200:
                data = response.json()
                if 'stats' in data and 'usdt-rls' in data['stats']:
                    tether_rial = float(data['stats']['usdt-rls']['latest'])
                    tether_toman = int(tether_rial / 10)
                    prices['تتر'] = f"{tether_toman:,} تومان"
                    logging.info(f"✓ USDT: {tether_toman:,}")
        except Exception as e:
            logging.error(f"خطا USDT: {e}")
        
        return prices

    def get_dollar_latest(self):
        """دریافت قیمت دلار از منابع مختلف"""
        
        # روش 1: Aban Tether API
        try:
            logging.info("دلار: تست Aban Tether...")
            response = requests.get('https://abantether.com/api/v1/otc/fiat-irt/list', timeout=10)
            if response.status_code == 200:
                data = response.json()
                for item in data.get('data', []):
                    if item.get('fiat') == 'USD':
                        dollar_price = int(float(item.get('sellPrice', 0)))
                        if 60000 <= dollar_price <= 120000:
                            logging.info(f"✓ دلار از Aban: {dollar_price:,}")
                            return f"{dollar_price:,} تومان"
        except Exception as e:
            logging.error(f"خطا Aban: {e}")
        
        # روش 2: Navasan API
        try:
            logging.info("دلار: تست Navasan...")
            response = requests.get('http://api.navasan.tech/latest/?api_key=freeQnOFlXXDqloNmYt99DF5evFrNBkz', timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'usd' in data and 'value' in data['usd']:
                    dollar_price = int(data['usd']['value'])
                    if 60000 <= dollar_price <= 120000:
                        logging.info(f"✓ دلار از Navasan: {dollar_price:,}")
                        return f"{dollar_price:,} تومان"
        except Exception as e:
            logging.error(f"خطا Navasan: {e}")
        
        # روش 3: Bonbast JSON
        try:
            logging.info("دلار: تست Bonbast JSON...")
            response = requests.get('https://bonbast.com/json', timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'usd' in data and 'sell' in data['usd']:
                    dollar_str = str(data['usd']['sell']).replace(',', '')
                    if dollar_str.isdigit():
                        dollar_price = int(dollar_str)
                        if 60000 <= dollar_price <= 120000:
                            logging.info(f"✓ دلار از Bonbast JSON: {dollar_price:,}")
                            return f"{dollar_price:,} تومان"
        except Exception as e:
            logging.error(f"خطا Bonbast JSON: {e}")
        
        # روش 4: TGJU HTML Scraping
        try:
            logging.info("دلار: تست TGJU HTML...")
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get('https://www.tgju.org/profile/price_dollar_rl', headers=headers, timeout=15)
            if response.status_code == 200:
                html = response.text
                
                # جستجوی دقیق‌تر
                patterns = [
                    r'data-last-price="(\d+)"',
                    r'"p":"(\d+)"',
                    r'قیمت\s*فعلی[^0-9]*(\d{2},\d{3})',
                    r'آخرین\s*قیمت[^0-9]*(\d{2},\d{3})'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    for match in matches:
                        price_str = match.replace(',', '')
                        if price_str.isdigit():
                            dollar_price = int(price_str)
                            if 60000 <= dollar_price <= 120000:
                                logging.info(f"✓ دلار از TGJU HTML: {dollar_price:,}")
                                return f"{dollar_price:,} تومان"
        except Exception as e:
            logging.error(f"خطا TGJU HTML: {e}")
        
        # روش 5: Bonbast HTML
        try:
            logging.info("دلار: تست Bonbast HTML...")
            response = requests.get('https://bonbast.com/', headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            if response.status_code == 200:
                html = response.text
                
                # الگوهای HTML
                patterns = [
                    r'<td[^>]*>USD</td>\s*<td[^>]*>[^<]*</td>\s*<td[^>]*>(\d{2},\d{3})</td>',
                    r'USD.*?(\d{2},\d{3})',
                    r'"sell":\s*"(\d+)"'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
                    for match in matches:
                        price_str = match.replace(',', '')
                        if price_str.isdigit():
                            dollar_price = int(price_str)
                            if 60000 <= dollar_price <= 120000:
                                logging.info(f"✓ دلار از Bonbast HTML: {dollar_price:,}")
                                return f"{dollar_price:,} تومان"
        except Exception as e:
            logging.error(f"خطا Bonbast HTML: {e}")
        
        return None

    def get_gold_latest(self):
        """دریافت قیمت طلا از منابع مختلف"""
        
        # روش 1: TGJU API
        try:
            logging.info("طلا: تست TGJU API...")
            response = requests.get('https://api.tgju.org/v1/data/sana/json', timeout=15)
            if response.status_code == 200:
                data = response.json()
                if 'geram18' in data and 'p' in data['geram18']:
                    gold_str = str(data['geram18']['p']).replace(',', '')
                    if gold_str.isdigit():
                        gold_price = int(gold_str)
                        if 2000000 <= gold_price <= 6000000:
                            logging.info(f"✓ طلا از TGJU API: {gold_price:,}")
                            return f"{gold_price:,} تومان"
        except Exception as e:
            logging.error(f"خطا TGJU API طلا: {e}")
        
        # روش 2: Navasan API
        try:
            logging.info("طلا: تست Navasan...")
            response = requests.get('http://api.navasan.tech/latest/?api_key=freeQnOFlXXDqloNmYt99DF5evFrNBkz', timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'gol18' in data and 'value' in data['gol18']:
                    gold_price = int(data['gol18']['value'])
                    if 2000000 <= gold_price <= 6000000:
                        logging.info(f"✓ طلا از Navasan: {gold_price:,}")
                        return f"{gold_price:,} تومان"
        except Exception as e:
            logging.error(f"خطا Navasan طلا: {e}")
        
        # روش 3: TGJU HTML
        try:
            logging.info("طلا: تست TGJU HTML...")
            response = requests.get('https://www.tgju.org/profile/geram18', 
                                  headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            if response.status_code == 200:
                html = response.text
                
                patterns = [
                    r'data-last-price="(\d+)"',
                    r'"p":"(\d+)"',
                    r'قیمت\s*فعلی[^0-9]*(\d{1,2},\d{3},\d{3})',
                    r'آخرین\s*قیمت[^0-9]*(\d{1,2},\d{3},\d{3})'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    for match in matches:
                        price_str = match.replace(',', '')
                        if price_str.isdigit():
                            gold_price = int(price_str)
                            if 2000000 <= gold_price <= 6000000:
                                logging.info(f"✓ طلا از TGJU HTML: {gold_price:,}")
                                return f"{gold_price:,} تومان"
        except Exception as e:
            logging.error(f"خطا TGJU HTML طلا: {e}")
        
        # روش 4: TalaOnline
        try:
            logging.info("طلا: تست TalaOnline...")
            response = requests.get('https://www.talaonline.com/', 
                                  headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            if response.status_code == 200:
                html = response.text
                
                patterns = [
                    r'18\s*عیار[^0-9]*(\d{1,2},\d{3},\d{3})',
                    r'طلای\s*18[^0-9]*(\d{1,2},\d{3},\d{3})',
                    r'(\d{1,2},\d{3},\d{3})[^0-9]*تومان[^0-9]*18'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    for match in matches:
                        price_str = match.replace(',', '')
                        if price_str.isdigit():
                            gold_price = int(price_str)
                            if 2000000 <= gold_price <= 6000000:
                                logging.info(f"✓ طلا از TalaOnline: {gold_price:,}")
                                return f"{gold_price:,} تومان"
        except Exception as e:
            logging.error(f"خطا TalaOnline: {e}")
        
        return None

    def get_coin_latest(self):
        """دریافت قیمت سکه از منابع مختلف"""
        
        # روش 1: TGJU API
        try:
            logging.info("سکه: تست TGJU API...")
            response = requests.get('https://api.tgju.org/v1/data/sana/json', timeout=15)
            if response.status_code == 200:
                data = response.json()
                if 'sekee' in data and 'p' in data['sekee']:
                    coin_str = str(data['sekee']['p']).replace(',', '')
                    if coin_str.isdigit():
                        coin_price = int(coin_str)
                        # تبدیل ریال به تومان اگر لازم باشد
                        if coin_price > 100000000:
                            coin_price = coin_price // 10
                        if 25000000 <= coin_price <= 80000000:
                            logging.info(f"✓ سکه از TGJU API: {coin_price:,}")
                            return f"{coin_price:,} تومان"
        except Exception as e:
            logging.error(f"خطا TGJU API سکه: {e}")
        
        # روش 2: Navasan API
        try:
            logging.info("سکه: تست Navasan...")
            response = requests.get('http://api.navasan.tech/latest/?api_key=freeQnOFlXXDqloNmYt99DF5evFrNBkz', timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'sekee' in data and 'value' in data['sekee']:
                    coin_price = int(data['sekee']['value'])
                    if coin_price > 100000000:
                        coin_price = coin_price // 10
                    if 25000000 <= coin_price <= 80000000:
                        logging.info(f"✓ سکه از Navasan: {coin_price:,}")
                        return f"{coin_price:,} تومان"
        except Exception as e:
            logging.error(f"خطا Navasan سکه: {e}")
        
        # روش 3: TGJU HTML
        try:
            logging.info("سکه: تست TGJU HTML...")
            response = requests.get('https://www.tgju.org/profile/sekee', 
                                  headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            if response.status_code == 200:
                html = response.text
                
                patterns = [
                    r'data-last-price="(\d+)"',
                    r'"p":"(\d+)"',
                    r'قیمت\s*فعلی[^0-9]*(\d{2,3},\d{3},\d{3})',
                    r'آخرین\s*قیمت[^0-9]*(\d{2,3},\d{3},\d{3})'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    for match in matches:
                        price_str = match.replace(',', '')
                        if price_str.isdigit():
                            coin_price = int(price_str)
                            if coin_price > 100000000:
                                coin_price = coin_price // 10
                            if 25000000 <= coin_price <= 80000000:
                                logging.info(f"✓ سکه از TGJU HTML: {coin_price:,}")
                                return f"{coin_price:,} تومان"
        except Exception as e:
            logging.error(f"خطا TGJU HTML سکه: {e}")
        
        # روش 4: TalaOnline
        try:
            logging.info("سکه: تست TalaOnline...")
            response = requests.get('https://www.talaonline.com/', 
                                  headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            if response.status_code == 200:
                html = response.text
                
                patterns = [
                    r'سکه\s*امامی[^0-9]*(\d{2,3},\d{3},\d{3})',
                    r'امامی[^0-9]*(\d{2,3},\d{3},\d{3})',
                    r'(\d{2,3},\d{3},\d{3})[^0-9]*تومان[^0-9]*سکه'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    for match in matches:
                        price_str = match.replace(',', '')
                        if price_str.isdigit():
                            coin_price = int(price_str)
                            if coin_price > 100000000:
                                coin_price = coin_price // 10
                            if 25000000 <= coin_price <= 80000000:
                                logging.info(f"✓ سکه از TalaOnline: {coin_price:,}")
                                return f"{coin_price:,} تومان"
        except Exception as e:
            logging.error(f"خطا TalaOnline سکه: {e}")
        
        return None

    def collect_and_send_prices(self):
        """جمع‌آوری و ارسال"""
        logging.info("=" * 50)
        logging.info("🚀 شروع جمع‌آوری قیمت‌ها...")
        
        try:
            # کریپتو و تتر (بدون تغییر)
            crypto_tether = self.get_crypto_and_tether()
            
            # دلار، طلا، سکه (بهبود یافته)
            dollar = self.get_dollar_latest()
            gold = self.get_gold_latest()
            coin = self.get_coin_latest()
            
            # ترکیب همه
            all_prices = crypto_tether.copy()
            if dollar:
                all_prices['دلار آمریکا'] = dollar
            if gold:
                all_prices['طلای 18 عیار'] = gold
            if coin:
                all_prices['سکه امامی'] = coin
            
            # ساخت پیام
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            message = f"📊 قیمت‌های لحظه‌ای\n"
            message += f"🕐 آپدیت: {current_time}\n\n"
            
            # بازار ارز و طلا
            message += "💰 بازار ارز و طلا:\n"
            message += f"💵 دلار آمریکا: {all_prices.get('دلار آمریکا', '🔄 در حال آپدیت')}\n"
            message += f"💳 تتر: {all_prices.get('تتر', '🔄 در حال آپدیت')}\n"
            message += f"🥇 طلای 18 عیار: {all_prices.get('طلای 18 عیار', '🔄 در حال آپدیت')}\n"
            message += f"🪙 سکه امامی: {all_prices.get('سکه امامی', '🔄 در حال آپدیت')}\n\n"
            
            # ارزهای دیجیتال
            message += "₿ ارزهای دیجیتال:\n"
            message += f"🟠 بیت‌کوین: {all_prices.get('بیت‌کوین', '🔄 در حال آپدیت')}\n"
            message += f"🔵 اتریوم: {all_prices.get('اتریوم', '🔄 در حال آپدیت')}\n\n"
            
            message += "🔄 آپدیت بعدی: 30 دقیقه دیگر\n"
            message += "📱 @asle_tehran"
            
            # لاگ نتایج
            target_items = ['دلار آمریکا', 'تتر', 'طلای 18 عیار', 'سکه امامی', 'بیت‌کوین', 'اتریوم']
            success_count = sum(1 for item in target_items if item in all_prices)
            
            logging.info(f"📊 نتیجه: {success_count}/6 قیمت موفق")
            for item in target_items:
                status = "✓" if item in all_prices else "✗"
                price = all_prices.get(item, "ناموفق")
                logging.info(f"  {status} {item}: {price}")
            
            # ارسال
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
        """ارسال پیام"""
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
    
    logging.info("🤖 ربات نهایی شروع شد")
    collector = PriceCollector(TELEGRAM_BOT_TOKEN, CHAT_ID)
    collector.collect_and_send_prices()
    logging.info("✅ پایان")
    sys.exit(0)

if __name__ == "__main__":
    main()
