#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import logging
import os
from datetime import datetime
import asyncio
from telegram import Bot
import sys
import json
import re
from bs4 import BeautifulSoup

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
            'Accept': 'text/html,application/json,*/*',
            'Accept-Language': 'fa,en;q=0.9'
        })

    def get_tgju_prices(self):
        """دریافت قیمت از TGJU"""
        prices = {}
        
        try:
            logging.info("درخواست به TGJU...")
            
            # روش 1: صفحه اصلی TGJU
            response = self.session.get('https://www.tgju.org/', timeout=10)
            if response.status_code == 200:
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                
                # جستجوی قیمت دلار
                dollar_elem = soup.find('tr', {'data-market-row': 'price_dollar_rl'})
                if dollar_elem:
                    price_elem = dollar_elem.find('td', class_='nf')
                    if price_elem:
                        price_text = price_elem.text.strip().replace(',', '')
                        if price_text.isdigit():
                            dollar_price = int(price_text)
                            prices['دلار آمریکا'] = f"{dollar_price:,} تومان"
                            logging.info(f"TGJU دلار: {dollar_price:,}")
                
                # جستجوی قیمت طلا
                gold_elem = soup.find('tr', {'data-market-row': 'geram18'})
                if gold_elem:
                    price_elem = gold_elem.find('td', class_='nf')
                    if price_elem:
                        price_text = price_elem.text.strip().replace(',', '')
                        if price_text.isdigit():
                            gold_price = int(price_text)
                            prices['طلای 18 عیار'] = f"{gold_price:,} تومان"
                            logging.info(f"TGJU طلا: {gold_price:,}")
                
                # جستجوی قیمت سکه
                coin_elem = soup.find('tr', {'data-market-row': 'sekee'})
                if coin_elem:
                    price_elem = coin_elem.find('td', class_='nf')
                    if price_elem:
                        price_text = price_elem.text.strip().replace(',', '')
                        if price_text.isdigit():
                            coin_price = int(price_text)
                            # اگر عدد بزرگ است، از ریال به تومان تبدیل کن
                            if coin_price > 100000000:
                                coin_price = coin_price // 10
                            prices['سکه امامی'] = f"{coin_price:,} تومان"
                            logging.info(f"TGJU سکه: {coin_price:,}")
        except Exception as e:
            logging.error(f"خطا در TGJU HTML: {e}")
        
        # روش 2: API های TGJU
        if not prices:
            try:
                endpoints = [
                    'https://api.tgju.org/v1/data/sana/json',
                    'https://cdn.tgju.org/api/v1/data/sana/json',
                    'https://api.tgju.org/v1/market/indicator/summary-table-data'
                ]
                
                for endpoint in endpoints:
                    try:
                        response = self.session.get(endpoint, timeout=10)
                        if response.status_code == 200:
                            data = response.json()
                            
                            # پردازش JSON
                            if isinstance(data, dict):
                                # دلار
                                if 'price_dollar_rl' in data and 'دلار آمریکا' not in prices:
                                    dollar = data['price_dollar_rl'].get('p', '').replace(',', '')
                                    if dollar.isdigit():
                                        prices['دلار آمریکا'] = f"{int(dollar):,} تومان"
                                        logging.info(f"TGJU API دلار: {dollar}")
                                
                                # طلا
                                if 'geram18' in data and 'طلای 18 عیار' not in prices:
                                    gold = data['geram18'].get('p', '').replace(',', '')
                                    if gold.isdigit():
                                        prices['طلای 18 عیار'] = f"{int(gold):,} تومان"
                                        logging.info(f"TGJU API طلا: {gold}")
                                
                                # سکه
                                if 'sekee' in data and 'سکه امامی' not in prices:
                                    coin = data['sekee'].get('p', '').replace(',', '')
                                    if coin.isdigit():
                                        coin_price = int(coin)
                                        if coin_price > 100000000:
                                            coin_price = coin_price // 10
                                        prices['سکه امامی'] = f"{coin_price:,} تومان"
                                        logging.info(f"TGJU API سکه: {coin_price}")
                            
                            if prices:
                                break
                    except:
                        continue
            except Exception as e:
                logging.error(f"خطا در TGJU API: {e}")
        
        return prices

    def get_bonbast_prices(self):
        """دریافت قیمت از Bonbast"""
        prices = {}
        
        try:
            logging.info("درخواست به Bonbast...")
            
            # صفحه اصلی
            response = self.session.get('https://bonbast.com/', timeout=10)
            if response.status_code == 200:
                html = response.text
                
                # دلار
                usd_match = re.search(r'USD.*?Sell.*?(\d{2},?\d{3})', html, re.DOTALL)
                if not usd_match:
                    usd_match = re.search(r'"usd".*?"sell".*?(\d+)', html, re.DOTALL)
                if usd_match:
                    usd_price = int(usd_match.group(1).replace(',', ''))
                    prices['دلار آمریکا'] = f"{usd_price:,} تومان"
                    logging.info(f"Bonbast دلار: {usd_price:,}")
                
                # طلای 18 عیار
                gold_match = re.search(r'18 Karat.*?(\d{1,2},?\d{3},?\d{3})', html, re.DOTALL)
                if not gold_match:
                    gold_match = re.search(r'gol18.*?(\d+)', html, re.DOTALL)
                if gold_match:
                    gold_price = int(gold_match.group(1).replace(',', ''))
                    prices['طلای 18 عیار'] = f"{gold_price:,} تومان"
                    logging.info(f"Bonbast طلا: {gold_price:,}")
                
                # سکه امامی
                coin_match = re.search(r'Emami.*?(\d{2,3},?\d{3},?\d{3})', html, re.DOTALL)
                if not coin_match:
                    coin_match = re.search(r'sekee.*?(\d+)', html, re.DOTALL)
                if coin_match:
                    coin_price = int(coin_match.group(1).replace(',', ''))
                    if coin_price > 100000000:
                        coin_price = coin_price // 10
                    prices['سکه امامی'] = f"{coin_price:,} تومان"
                    logging.info(f"Bonbast سکه: {coin_price:,}")
                    
        except Exception as e:
            logging.error(f"خطا در Bonbast: {e}")
        
        # API Bonbast
        if not prices:
            try:
                response = self.session.get('https://bonbast.com/json', timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'usd' in data:
                        usd = data['usd'].get('sell', '').replace(',', '')
                        if usd.isdigit():
                            prices['دلار آمریکا'] = f"{int(usd):,} تومان"
                    
                    if 'gol18' in data:
                        gold = data['gol18'].get('sell', '').replace(',', '')
                        if gold.isdigit():
                            prices['طلای 18 عیار'] = f"{int(gold):,} تومان"
                    
                    if 'sekee' in data:
                        coin = data['sekee'].get('sell', '').replace(',', '')
                        if coin.isdigit():
                            coin_price = int(coin)
                            if coin_price > 100000000:
                                coin_price = coin_price // 10
                            prices['سکه امامی'] = f"{coin_price:,} تومان"
                            
            except Exception as e:
                logging.error(f"خطا در Bonbast JSON: {e}")
        
        return prices

    def get_tether_price(self):
        """دریافت قیمت تتر از نوبیتکس"""
        try:
            response = requests.get(
                'https://api.nobitex.ir/market/stats?srcCurrency=usdt&dstCurrency=rls',
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if 'stats' in data and 'usdt-rls' in data['stats']:
                    usdt = int(float(data['stats']['usdt-rls']['latest']) / 10)
                    logging.info(f"Nobitex تتر: {usdt:,}")
                    return f"{usdt:,} تومان"
        except Exception as e:
            logging.error(f"خطا در Nobitex: {e}")
        return None

    def get_crypto_prices(self):
        """دریافت قیمت بیت‌کوین و اتریوم از Binance"""
        prices = {}
        try:
            # بیت‌کوین
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', timeout=5)
            if response.status_code == 200:
                btc = float(response.json()['price'])
                prices['بیت‌کوین'] = f"${btc:,.0f}"
                logging.info(f"Binance BTC: ${btc:,.0f}")
            
            # اتریوم
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT', timeout=5)
            if response.status_code == 200:
                eth = float(response.json()['price'])
                prices['اتریوم'] = f"${eth:,.0f}"
                logging.info(f"Binance ETH: ${eth:,.0f}")
        except Exception as e:
            logging.error(f"خطا در Binance: {e}")
        
        return prices

    def collect_and_send_prices(self):
        """جمع‌آوری و ارسال قیمت‌ها"""
        logging.info("=" * 60)
        logging.info("🚀 شروع جمع‌آوری قیمت‌ها...")
        
        try:
            main_prices = {}
            
            # اول از TGJU
            tgju_prices = self.get_tgju_prices()
            main_prices.update(tgju_prices)
            
            # اگر کامل نبود از Bonbast
            if len(main_prices) < 3:
                logging.info("قیمت‌های TGJU کامل نیست، تلاش با Bonbast...")
                bonbast_prices = self.get_bonbast_prices()
                for key, value in bonbast_prices.items():
                    if key not in main_prices:
                        main_prices[key] = value
            
            # تتر
            tether = self.get_tether_price()
            if tether:
                main_prices['تتر'] = tether
            
            # کریپتو
            crypto_prices = self.get_crypto_prices()
            
            # فرمت پیام
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            message = f"📊 گزارش قیمت‌های لحظه‌ای\n"
            message += f"🕐 زمان: {current_time}\n\n"
            
            # بازار ارز و طلا
            if main_prices:
                message += "💰 بازار ارز و طلا:\n"
                if 'دلار آمریکا' in main_prices:
                    message += f"💵 دلار آمریکا: {main_prices['دلار آمریکا']}\n"
                if 'تتر' in main_prices:
                    message += f"💳 تتر: {main_prices['تتر']}\n"
                if 'طلای 18 عیار' in main_prices:
                    message += f"🥇 طلای 18 عیار: {main_prices['طلای 18 عیار']}\n"
                if 'سکه امامی' in main_prices:
                    message += f"🪙 سکه امامی: {main_prices['سکه امامی']}\n"
                message += "\n"
            
            # ارزهای دیجیتال
            if crypto_prices:
                message += "₿ ارزهای دیجیتال:\n"
                if 'بیت‌کوین' in crypto_prices:
                    message += f"🟠 بیت‌کوین: {crypto_prices['بیت‌کوین']}\n"
                if 'اتریوم' in crypto_prices:
                    message += f"🔵 اتریوم: {crypto_prices['اتریوم']}\n"
                message += "\n"
            
            message += "🔄 آپدیت بعدی: 30 دقیقه دیگر\n"
            message += "📱 @asle_tehran"
            
            # لاگ
            total = len(main_prices) + len(crypto_prices)
            logging.info(f"📊 مجموع: {total} قیمت")
            for name, price in {**main_prices, **crypto_prices}.items():
                logging.info(f"  ✓ {name}: {price}")
            
            # ارسال
            success = asyncio.run(self.send_message(message))
            
            if success:
                logging.info("✅ پیام ارسال شد")
            else:
                logging.error("❌ خطا در ارسال")
                
        except Exception as e:
            logging.error(f"❌ خطا: {e}")
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
    
    logging.info("🤖 ربات قیمت شروع به کار کرد")
    monitor = PriceMonitor(TELEGRAM_BOT_TOKEN, CHAT_ID)
    monitor.collect_and_send_prices()
    logging.info("✅ پایان اجرا")
    sys.exit(0)

if __name__ == "__main__":
    main()
