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
import json
import re

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
            'Accept-Language': 'fa,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Referer': 'https://www.google.com/'
        })

    def get_tgju_api_method1(self):
        """روش 1: API اصلی TGJU"""
        prices = {}
        try:
            logging.info("تست API اصلی TGJU...")
            response = self.session.get(
                'https://api.tgju.org/v1/data/sana/json',
                timeout=15
            )
            if response.status_code == 200:
                data = response.json()
                logging.info(f"پاسخ API: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                
                if isinstance(data, dict):
                    # دلار آمریکا
                    if 'price_dollar_rl' in data:
                        dollar_data = data['price_dollar_rl']
                        dollar_price = str(dollar_data.get('p', '')).replace(',', '').strip()
                        if dollar_price.isdigit():
                            prices['دلار آمریکا'] = f"{int(dollar_price):,} تومان"
                            logging.info(f"✓ دلار: {dollar_price}")
                    
                    # طلای 18 عیار
                    if 'geram18' in data:
                        gold_data = data['geram18']
                        gold_price = str(gold_data.get('p', '')).replace(',', '').strip()
                        if gold_price.isdigit():
                            prices['طلای 18 عیار'] = f"{int(gold_price):,} تومان"
                            logging.info(f"✓ طلا: {gold_price}")
                    
                    # سکه امامی
                    if 'sekee' in data:
                        coin_data = data['sekee']
                        coin_price = str(coin_data.get('p', '')).replace(',', '').strip()
                        if coin_price.isdigit():
                            coin_val = int(coin_price)
                            # اگر بزرگ است، از ریال به تومان
                            if coin_val > 100000000:
                                coin_val = coin_val // 10
                            prices['سکه امامی'] = f"{coin_val:,} تومان"
                            logging.info(f"✓ سکه: {coin_val}")
                    
                    # تتر
                    if 'crypto-usdt' in data:
                        usdt_data = data['crypto-usdt']
                        usdt_price = str(usdt_data.get('p', '')).replace(',', '').strip()
                        if usdt_price.isdigit():
                            prices['تتر'] = f"{int(usdt_price):,} تومان"
                            logging.info(f"✓ تتر: {usdt_price}")
        except Exception as e:
            logging.error(f"خطا در API روش 1: {e}")
        
        return prices

    def get_tgju_api_method2(self):
        """روش 2: API جایگزین TGJU"""
        prices = {}
        try:
            logging.info("تست API جایگزین TGJU...")
            response = self.session.get(
                'https://call6.tgju.org/ajax.json',
                timeout=15
            )
            if response.status_code == 200:
                data = response.json()
                logging.info(f"پاسخ API 2: کلیدها={list(data.keys()) if isinstance(data, dict) else 'نامعلوم'}")
                
                # پردازش داده‌ها بر اساس فرمت مختلف
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            title = item.get('title', '').lower()
                            price = item.get('p', 0) or item.get('price', 0)
                            
                            if price and price > 0:
                                if 'دلار' in title or 'dollar' in title:
                                    prices['دلار آمریکا'] = f"{int(price):,} تومان"
                                    logging.info(f"✓ دلار از لیست: {price}")
                                elif 'طلا' in title or 'geram18' in title:
                                    prices['طلای 18 عیار'] = f"{int(price):,} تومان"
                                    logging.info(f"✓ طلا از لیست: {price}")
                                elif 'سکه' in title or 'sekee' in title:
                                    coin_val = int(price) // 10 if price > 100000000 else int(price)
                                    prices['سکه امامی'] = f"{coin_val:,} تومان"
                                    logging.info(f"✓ سکه از لیست: {coin_val}")
                                elif 'تتر' in title or 'usdt' in title:
                                    prices['تتر'] = f"{int(price):,} تومان"
                                    logging.info(f"✓ تتر از لیست: {price}")
        except Exception as e:
            logging.error(f"خطا در API روش 2: {e}")
        
        return prices

    def get_tgju_scraping(self):
        """روش 3: HTML Scraping از صفحه اصلی"""
        prices = {}
        try:
            logging.info("تست HTML Scraping TGJU...")
            response = self.session.get(
                'https://www.tgju.org/',
                timeout=15
            )
            if response.status_code == 200:
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                logging.info("✓ صفحه اصلی بارگذاری شد")
                
                # جستجوی جدول قیمت‌ها
                price_table = soup.find('table', class_='table')
                if price_table:
                    rows = price_table.find_all('tr')
                    for row in rows:
                        data_market = row.get('data-market-row', '')
                        
                        if data_market == 'price_dollar_rl':
                            # دلار
                            price_cell = row.find('td', class_='nf')
                            if price_cell:
                                price_text = price_cell.text.strip().replace(',', '')
                                if price_text.isdigit():
                                    prices['دلار آمریکا'] = f"{int(price_text):,} تومان"
                                    logging.info(f"✓ دلار HTML: {price_text}")
                        
                        elif data_market == 'geram18':
                            # طلا
                            price_cell = row.find('td', class_='nf')
                            if price_cell:
                                price_text = price_cell.text.strip().replace(',', '')
                                if price_text.isdigit():
                                    prices['طلای 18 عیار'] = f"{int(price_text):,} تومان"
                                    logging.info(f"✓ طلا HTML: {price_text}")
                        
                        elif data_market == 'sekee':
                            # سکه
                            price_cell = row.find('td', class_='nf')
                            if price_cell:
                                price_text = price_cell.text.strip().replace(',', '')
                                if price_text.isdigit():
                                    coin_val = int(price_text)
                                    if coin_val > 100000000:
                                        coin_val = coin_val // 10
                                    prices['سکه امامی'] = f"{coin_val:,} تومان"
                                    logging.info(f"✓ سکه HTML: {coin_val}")
                        
                        elif data_market == 'crypto-usdt':
                            # تتر
                            price_cell = row.find('td', class_='nf')
                            if price_cell:
                                price_text = price_cell.text.strip().replace(',', '')
                                if price_text.isdigit():
                                    prices['تتر'] = f"{int(price_text):,} تومان"
                                    logging.info(f"✓ تتر HTML: {price_text}")
                
                # اگر جدول پیدا نشد، با regex جستجو کن
                if not prices:
                    logging.info("جستجو با regex...")
                    
                    # دلار
                    dollar_match = re.search(r'price_dollar_rl.*?(\d{2},?\d{3})', html, re.DOTALL)
                    if dollar_match:
                        dollar_price = int(dollar_match.group(1).replace(',', ''))
                        prices['دلار آمریکا'] = f"{dollar_price:,} تومان"
                        logging.info(f"✓ دلار regex: {dollar_price}")
                    
                    # طلا
                    gold_match = re.search(r'geram18.*?(\d{1,2},?\d{3},?\d{3})', html, re.DOTALL)
                    if gold_match:
                        gold_price = int(gold_match.group(1).replace(',', ''))
                        prices['طلای 18 عیار'] = f"{gold_price:,} تومان"
                        logging.info(f"✓ طلا regex: {gold_price}")
                    
                    # سکه
                    coin_match = re.search(r'sekee.*?(\d{2,3},?\d{3},?\d{3})', html, re.DOTALL)
                    if coin_match:
                        coin_price = int(coin_match.group(1).replace(',', ''))
                        if coin_price > 100000000:
                            coin_price = coin_price // 10
                        prices['سکه امامی'] = f"{coin_price:,} تومان"
                        logging.info(f"✓ سکه regex: {coin_price}")
        except Exception as e:
            logging.error(f"خطا در HTML Scraping: {e}")
        
        return prices

    def get_tgju_direct_pages(self):
        """روش 4: صفحات مستقیم هر قیمت"""
        prices = {}
        
        pages = {
            'دلار آمریکا': 'https://www.tgju.org/profile/price_dollar_rl',
            'طلای 18 عیار': 'https://www.tgju.org/profile/geram18',
            'سکه امامی': 'https://www.tgju.org/profile/sekee',
            'تتر': 'https://www.tgju.org/profile/crypto-usdt'
        }
        
        for name, url in pages.items():
            try:
                logging.info(f"دریافت {name} از {url}")
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    html = response.text
                    
                    # جستجوی قیمت در صفحه
                    price_patterns = [
                        r'نرخ فعلی.*?(\d{1,3}(?:,\d{3})*)',
                        r'قیمت.*?(\d{1,3}(?:,\d{3})*)',
                        r'<span[^>]*>(\d{1,3}(?:,\d{3})*)</span>',
                        r'"price".*?(\d+)',
                        r'data-price="(\d+)"'
                    ]
                    
                    for pattern in price_patterns:
                        match = re.search(pattern, html, re.DOTALL)
                        if match:
                            price_str = match.group(1).replace(',', '')
                            if price_str.isdigit():
                                price_val = int(price_str)
                                
                                if name == 'سکه امامی' and price_val > 100000000:
                                    price_val = price_val // 10
                                
                                prices[name] = f"{price_val:,} تومان"
                                logging.info(f"✓ {name}: {price_val:,}")
                                break
            except Exception as e:
                logging.error(f"خطا در دریافت {name}: {e}")
        
        return prices

    def get_all_tgju_prices(self):
        """ترکیب همه روش‌های TGJU"""
        all_prices = {}
        
        # روش 1: API اصلی
        prices1 = self.get_tgju_api_method1()
        all_prices.update(prices1)
        logging.info(f"روش 1 - API اصلی: {len(prices1)} قیمت")
        
        # روش 2: API جایگزین (فقط اگر کامل نبود)
        if len(all_prices) < 4:
            prices2 = self.get_tgju_api_method2()
            for key, value in prices2.items():
                if key not in all_prices:
                    all_prices[key] = value
            logging.info(f"روش 2 - API جایگزین: {len(prices2)} قیمت")
        
        # روش 3: HTML Scraping (فقط اگر کامل نبود)
        if len(all_prices) < 4:
            prices3 = self.get_tgju_scraping()
            for key, value in prices3.items():
                if key not in all_prices:
                    all_prices[key] = value
            logging.info(f"روش 3 - HTML Scraping: {len(prices3)} قیمت")
        
        # روش 4: صفحات مستقیم (فقط اگر کامل نبود)
        if len(all_prices) < 4:
            prices4 = self.get_tgju_direct_pages()
            for key, value in prices4.items():
                if key not in all_prices:
                    all_prices[key] = value
            logging.info(f"روش 4 - صفحات مستقیم: {len(prices4)} قیمت")
        
        return all_prices

    def get_crypto_prices(self):
        """دریافت قیمت کریپتو از Binance (تنها منبع غیر TGJU)"""
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
        logging.info("=" * 70)
        logging.info("🚀 تست TGJU - شروع جمع‌آوری قیمت‌ها...")
        
        try:
            # فقط از TGJU
            main_prices = self.get_all_tgju_prices()
            
            # کریپتو از Binance
            crypto_prices = self.get_crypto_prices()
            
            # گزارش نتایج
            logging.info("=" * 50)
            logging.info("📊 نتایج نهایی:")
            logging.info(f"TGJU: {len(main_prices)} قیمت")
            logging.info(f"Binance: {len(crypto_prices)} قیمت")
            
            # فرمت پیام
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            message = f"📊 تست TGJU - قیمت‌های لحظه‌ای\n"
            message += f"🕐 زمان: {current_time}\n\n"
            
            # قیمت‌های TGJU
            if main_prices:
                message += "💰 قیمت‌ها از TGJU:\n"
                if 'دلار آمریکا' in main_prices:
                    message += f"💵 دلار آمریکا: {main_prices['دلار آمریکا']}\n"
                if 'تتر' in main_prices:
                    message += f"💳 تتر: {main_prices['تتر']}\n"
                if 'طلای 18 عیار' in main_prices:
                    message += f"🥇 طلای 18 عیار: {main_prices['طلای 18 عیار']}\n"
                if 'سکه امامی' in main_prices:
                    message += f"🪙 سکه امامی: {main_prices['سکه امامی']}\n"
                message += "\n"
            else:
                message += "❌ هیچ قیمتی از TGJU دریافت نشد\n\n"
            
            # کریپتو
            if crypto_prices:
                message += "₿ ارزهای دیجیتال (Binance):\n"
                if 'بیت‌کوین' in crypto_prices:
                    message += f"🟠 بیت‌کوین: {crypto_prices['بیت‌کوین']}\n"
                if 'اتریوم' in crypto_prices:
                    message += f"🔵 اتریوم: {crypto_prices['اتریوم']}\n"
                message += "\n"
            
            # خلاصه
            total = len(main_prices) + len(crypto_prices)
            message += f"📈 نتیجه: {len(main_prices)}/4 از TGJU + {len(crypto_prices)}/2 از Binance\n\n"
            
            if len(main_prices) == 0:
                message += "🚨 احتمالاً GitHub Actions به TGJU دسترسی ندارد\n\n"
            elif len(main_prices) < 4:
                message += "⚠️ برخی قیمت‌های TGJU دریافت نشد\n\n"
            else:
                message += "✅ همه قیمت‌ها از TGJU دریافت شد\n\n"
            
            message += "🔄 آپدیت بعدی: 30 دقیقه دیگر\n"
            message += "📱 @asle_tehran"
            
            # لاگ نهایی
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
    
    logging.info("🤖 تست TGJU - ربات شروع شد")
    monitor = PriceMonitor(TELEGRAM_BOT_TOKEN, CHAT_ID)
    monitor.collect_and_send_prices()
    logging.info("✅ تست TGJU - پایان")
    sys.exit(0)

if __name__ == "__main__":
    main()
