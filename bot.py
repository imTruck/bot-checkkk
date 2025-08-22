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

class RealPriceBot:
    def __init__(self, bot_token, chat_id):
        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id

    def get_crypto_from_api(self):
        """کریپتو - بدون تغییر"""
        prices = {}
        
        try:
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', timeout=10)
            if response.status_code == 200:
                btc_price = float(response.json()['price'])
                prices['بیت‌کوین'] = f"${btc_price:,.0f}"
                logging.info(f"✓ BTC: ${btc_price:,.0f}")
        except Exception as e:
            logging.error(f"خطا Binance BTC: {e}")
        
        try:
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT', timeout=10)
            if response.status_code == 200:
                eth_price = float(response.json()['price'])
                prices['اتریوم'] = f"${eth_price:,.0f}"
                logging.info(f"✓ ETH: ${eth_price:,.0f}")
        except Exception as e:
            logging.error(f"خطا Binance ETH: {e}")
        
        if not prices:
            try:
                response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd', timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    if 'bitcoin' in data:
                        prices['بیت‌کوین'] = f"${data['bitcoin']['usd']:,.0f}"
                    if 'ethereum' in data:
                        prices['اتریوم'] = f"${data['ethereum']['usd']:,.0f}"
                    logging.info("✓ کریپتو از CoinGecko")
            except Exception as e:
                logging.error(f"خطا CoinGecko: {e}")
        
        return prices

    def get_tether_from_api(self):
        """تتر - بدون تغییر"""
        try:
            response = requests.get('https://api.nobitex.ir/market/stats?srcCurrency=usdt&dstCurrency=rls', timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'stats' in data and 'usdt-rls' in data['stats']:
                    price_rial = float(data['stats']['usdt-rls']['latest'])
                    price_toman = int(price_rial / 10)
                    logging.info(f"✓ USDT: {price_toman:,}")
                    return f"{price_toman:,} تومان"
        except Exception as e:
            logging.error(f"خطا Nobitex: {e}")
        return None

    def get_dollar_iranian_sources(self):
        """دلار فقط از منابع ایرانی"""
        
        # روش 1: API ارز امروز
        try:
            logging.info("دلار: API ارز امروز...")
            response = requests.get('https://call1.tgju.org/ajax.json', timeout=10)
            if response.status_code == 200:
                data = response.json()
                logging.info(f"ارز امروز response type: {type(data)}")
                
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and 'title' in item:
                            title = item.get('title', '').lower()
                            if 'دلار' in title or 'dollar' in title:
                                price = item.get('p', 0) or item.get('price', 0)
                                if price and price > 50000:
                                    logging.info(f"✓ دلار از ارز امروز: {price:,}")
                                    return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا API ارز امروز: {e}")
        
        # روش 2: Bonbast API مستقیم
        try:
            logging.info("دلار: Bonbast API...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://bonbast.com/',
                'Accept': 'application/json'
            }
            response = requests.get('https://bonbast.com/json', headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                logging.info(f"Bonbast JSON structure: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                
                if 'usd' in data:
                    usd_data = data['usd']
                    for key in ['sell', 'buy']:
                        if key in usd_data:
                            price_str = str(usd_data[key]).replace(',', '').strip()
                            if price_str.isdigit():
                                price = int(price_str)
                                logging.info(f"✓ دلار از Bonbast {key}: {price:,}")
                                return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا Bonbast API: {e}")
        
        # روش 3: TGJU API مستقیم
        try:
            logging.info("دلار: TGJU API...")
            endpoints = [
                'https://api.tgju.org/v1/data/sana/json',
                'https://api.tgju.org/v1/market/indicator/summary-table-data',
                'https://call6.tgju.org/ajax.json'
            ]
            
            for endpoint in endpoints:
                try:
                    response = requests.get(endpoint, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        
                        # فرمت مختلف API ها
                        if isinstance(data, dict):
                            if 'price_dollar_rl' in data:
                                price_data = data['price_dollar_rl']
                                price_str = str(price_data.get('p', '')).replace(',', '')
                                if price_str.isdigit():
                                    price = int(price_str)
                                    logging.info(f"✓ دلار از TGJU: {price:,}")
                                    return f"{price:,} تومان"
                        
                        elif isinstance(data, list):
                            for item in data:
                                if 'title' in item and 'دلار' in item.get('title', ''):
                                    price = item.get('p', 0)
                                    if price and price > 50000:
                                        logging.info(f"✓ دلار از TGJU list: {price:,}")
                                        return f"{price:,} تومان"
                except:
                    continue
        except Exception as e:
            logging.error(f"خطا TGJU API: {e}")
        
        # روش 4: HTML scraping دقیق Bonbast
        try:
            logging.info("دلار: Bonbast HTML...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            response = requests.get('https://bonbast.com/', headers=headers, timeout=15)
            if response.status_code == 200:
                html = response.text
                
                # جستجوی دقیق در HTML
                patterns = [
                    # جدول قیمت‌ها
                    r'<td[^>]*>USD</td>.*?<td[^>]*>(\d{2},\d{3})</td>',
                    # نمایش با class
                    r'class="[^"]*usd[^"]*"[^>]*>.*?(\d{2},\d{3})',
                    # متن ساده
                    r'USD[^0-9]*(\d{2},\d{3})',
                    r'دلار[^0-9]*(\d{2},\d{3})'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
                    for match in matches:
                        price_str = match.replace(',', '')
                        if price_str.isdigit():
                            price = int(price_str)
                            logging.info(f"✓ دلار از Bonbast HTML: {price:,}")
                            return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا Bonbast HTML: {e}")
        
        # روش 5: TGJU HTML
        try:
            logging.info("دلار: TGJU HTML...")
            response = requests.get('https://www.tgju.org/profile/price_dollar_rl', 
                                  headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            if response.status_code == 200:
                html = response.text
                
                patterns = [
                    r'data-last-price="(\d+)"',
                    r'class="[^"]*price[^"]*"[^>]*>(\d{2},\d{3})',
                    r'قیمت[^0-9]*(\d{2},\d{3})',
                    r'آخرین[^0-9]*(\d{2},\d{3})'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    for match in matches:
                        price_str = match.replace(',', '')
                        if price_str.isdigit():
                            price = int(price_str)
                            logging.info(f"✓ دلار از TGJU HTML: {price:,}")
                            return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا TGJU HTML: {e}")
        
        # روش 6: سایت‌های دیگر ایرانی
        try:
            logging.info("دلار: سایت‌های دیگر...")
            iranian_sites = [
                'https://arzdigital.com/coins/us-dollar-price/',
                'https://www.sarrafionline.com/',
                'https://www.wallex.ir/exchange/USD_TMN'
            ]
            
            for site in iranian_sites:
                try:
                    response = requests.get(site, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                    if response.status_code == 200:
                        html = response.text
                        
                        # جستجوی عمومی برای قیمت دلار
                        numbers = re.findall(r'(\d{2},\d{3})', html)
                        for num in numbers:
                            price = int(num.replace(',', ''))
                            if 90000 <= price <= 100000:  # محدوده امروز
                                logging.info(f"✓ دلار از {site}: {price:,}")
                                return f"{price:,} تومان"
                except:
                    continue
        except Exception as e:
            logging.error(f"خطا سایت‌های دیگر: {e}")
        
        return None

    def get_gold_from_sources(self):
        """طلا - بدون تغییر"""
        try:
            response = requests.get('https://api.tgju.org/v1/data/sana/json', timeout=15)
            if response.status_code == 200:
                data = response.json()
                if 'geram18' in data and 'p' in data['geram18']:
                    price_str = str(data['geram18']['p']).replace(',', '')
                    if price_str.isdigit():
                        price = int(price_str)
                        logging.info(f"✓ طلا از TGJU API: {price:,}")
                        return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا TGJU API طلا: {e}")
        
        try:
            response = requests.get('https://www.tgju.org/profile/geram18', 
                                  headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            if response.status_code == 200:
                html = response.text
                numbers = re.findall(r'(\d{1,2},\d{3},\d{3})', html)
                for num in numbers:
                    price = int(num.replace(',', ''))
                    if price > 1000000:
                        logging.info(f"✓ طلا از TGJU HTML: {price:,}")
                        return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا TGJU HTML طلا: {e}")
        
        return None

    def get_coin_from_sources(self):
        """سکه - بدون تغییر"""
        try:
            response = requests.get('https://api.tgju.org/v1/data/sana/json', timeout=15)
            if response.status_code == 200:
                data = response.json()
                if 'sekee' in data and 'p' in data['sekee']:
                    price_str = str(data['sekee']['p']).replace(',', '')
                    if price_str.isdigit():
                        price = int(price_str)
                        if price > 100000000:
                            price = price // 10
                        logging.info(f"✓ سکه از TGJU API: {price:,}")
                        return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا TGJU API سکه: {e}")
        
        try:
            response = requests.get('https://www.tgju.org/profile/sekee', 
                                  headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            if response.status_code == 200:
                html = response.text
                numbers = re.findall(r'(\d{2,3},\d{3},\d{3})', html)
                for num in numbers:
                    price = int(num.replace(',', ''))
                    if price > 100000000:
                        price = price // 10
                    if price > 10000000:
                        logging.info(f"✓ سکه از TGJU HTML: {price:,}")
                        return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا TGJU HTML سکه: {e}")
        
        return None

    def collect_and_send_prices(self):
        """جمع‌آوری و ارسال"""
        logging.info("=" * 50)
        logging.info("🚀 دریافت دلار از منابع ایرانی...")
        
        try:
            crypto_prices = self.get_crypto_from_api()
            tether = self.get_tether_from_api()
            dollar = self.get_dollar_iranian_sources()  # ← منابع ایرانی جدید
            gold = self.get_gold_from_sources()
            coin = self.get_coin_from_sources()
            
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            message = f"📊 قیمت‌های لحظه‌ای\n"
            message += f"🕐 آپدیت: {current_time}\n\n"
            
            message += "💰 بازار ارز و طلا:\n"
            message += f"💵 دلار آمریکا: {dollar if dollar else '🔄 در حال آپدیت'}\n"
            message += f"💳 تتر: {tether if tether else '🔄 در حال آپدیت'}\n"
            message += f"🥇 طلای 18 عیار: {gold if gold else '🔄 در حال آپدیت'}\n"
            message += f"🪙 سکه امامی: {coin if coin else '🔄 در حال آپدیت'}\n\n"
            
            message += "₿ ارزهای دیجیتال:\n"
            message += f"🟠 بیت‌کوین: {crypto_prices.get('بیت‌کوین', '🔄 در حال آپدیت')}\n"
            message += f"🔵 اتریوم: {crypto_prices.get('اتریوم', '🔄 در حال آپدیت')}\n\n"
            
            message += "🔄 آپدیت بعدی: 30 دقیقه دیگر\n"
            message += "📱 @asle_tehran"
            
            all_prices = {
                'دلار آمریکا': dollar,
                'تتر': tether,
                'طلای 18 عیار': gold,
                'سکه امامی': coin,
                **crypto_prices
            }
            
            success_count = sum(1 for v in all_prices.values() if v is not None)
            logging.info(f"📊 نتیجه: {success_count}/6 قیمت موفق")
            
            for name, price in all_prices.items():
                status = "✓" if price else "✗"
                logging.info(f"  {status} {name}: {price if price else 'ناموفق'}")
            
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
    
    logging.info("🤖 ربات با منابع ایرانی شروع شد")
    bot = RealPriceBot(TELEGRAM_BOT_TOKEN, CHAT_ID)
    bot.collect_and_send_prices()
    logging.info("✅ پایان")
    sys.exit(0)

if __name__ == "__main__":
    main()
