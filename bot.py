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
        self.consecutive_failures = 0

    def get_tgju_prices_api(self):
        """دریافت قیمت از API مستقیم TGJU"""
        prices = {}
        
        api_endpoints = [
            'https://api.tgju.org/v1/market/indicator/summary-table-data/',
            'https://call6.tgju.org/ajax.json',
            'https://api.tgju.org/v1/market/live-price',
        ]
        
        for api_url in api_endpoints:
            try:
                response = self.session.get(api_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    
                    if isinstance(data, list):
                        # فرمت آرایه‌ای
                        for item in data:
                            if isinstance(item, dict):
                                title = item.get('title', '').lower()
                                price = item.get('p', 0) or item.get('price', 0)
                                
                                if price and price > 0:
                                    # همه قیمت‌ها از ریال به تومان تبدیل می‌شود
                                    price_toman = int(price) // 10
                                    
                                    if 'دلار' in title or 'dollar' in title or 'usd' in title:
                                        prices['دلار آمریکا'] = f"{price_toman:,} تومان"
                                    elif 'یورو' in title or 'euro' in title or 'eur' in title:
                                        prices['یورو'] = f"{price_toman:,} تومان"
                                    elif 'طلا' in title or 'gold' in title or 'geram18' in title:
                                        prices['طلای 18 عیار'] = f"{price_toman:,} تومان"
                                    elif 'سکه' in title or 'sekee' in title or 'emami' in title:
                                        prices['سکه امامی'] = f"{price_toman:,} تومان"
                    
                    elif isinstance(data, dict):
                        # فرمت دیکشنری
                        current = data.get('current', {})
                        
                        # همه قیمت‌ها را از ریال به تومان تبدیل می‌کنیم
                        if 'usd' in current:
                            usd_price = int(current['usd'].get('p', 0))
                            if usd_price > 0:
                                prices['دلار آمریکا'] = f"{usd_price // 10:,} تومان"
                        
                        if 'eur' in current:
                            eur_price = int(current['eur'].get('p', 0))
                            if eur_price > 0:
                                prices['یورو'] = f"{eur_price // 10:,} تومان"
                        
                        if 'geram18' in current:
                            gold_price = int(current['geram18'].get('p', 0))
                            if gold_price > 0:
                                prices['طلای 18 عیار'] = f"{gold_price // 10:,} تومان"
                        
                        if 'sekee' in current:
                            coin_price = int(current['sekee'].get('p', 0))
                            if coin_price > 0:
                                prices['سکه امامی'] = f"{coin_price // 10:,} تومان"
                    
                    if prices:
                        logging.info(f"API موفق: {len(prices)} قیمت از {api_url}")
                        return prices
                        
            except Exception as e:
                logging.error(f"خطا در API {api_url}: {e}")
                continue
        
        return prices

    def get_tgju_prices_scraping(self):
        """استخراج قیمت با کراول مستقیم از صفحات اختصاصی"""
        prices = {}
        
        # URL های مستقیم برای هر قیمت
        urls = {
            'dollar': 'https://www.tgju.org/profile/price_dollar_rl',
            'euro': 'https://www.tgju.org/profile/eur',
            'gold': 'https://www.tgju.org/profile/geram18',
            'coin': 'https://www.tgju.org/profile/sekee'
        }
        
        for price_type, url in urls.items():
            try:
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    html = response.text
                    
                    # پترن‌های مختلف برای استخراج قیمت
                    patterns = [
                        r'نرخ فعلی.*?(\d{1,3}(?:,\d{3})*)',
                        r'قیمت لحظه‌ای.*?(\d{1,3}(?:,\d{3})*)',
                        r'<span[^>]*class="[^"]*price[^"]*"[^>]*>(\d{1,3}(?:,\d{3})*)</span>',
                        r'"p":\s*(\d+)',
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
                        if match:
                            price_str = match.group(1).replace(',', '')
                            price_rial = int(price_str)
                            
                            # تبدیل از ریال به تومان
                            price_toman = price_rial // 10
                            
                            if price_type == 'dollar':
                                prices['دلار آمریکا'] = f"{price_toman:,} تومان"
                            elif price_type == 'euro':
                                prices['یورو'] = f"{price_toman:,} تومان"
                            elif price_type == 'gold':
                                prices['طلای 18 عیار'] = f"{price_toman:,} تومان"
                            elif price_type == 'coin':
                                prices['سکه امامی'] = f"{price_toman:,} تومان"
                            break
                
                logging.info(f"استخراج از {price_type}: {'موفق' if price_type in ['dollar', 'euro', 'gold', 'coin'] and any(key in prices for key in ['دلار آمریکا', 'یورو', 'طلای 18 عیار', 'سکه امامی']) else 'ناموفق'}")
                
            except Exception as e:
                logging.error(f"خطا در استخراج {price_type}: {e}")
        
        if prices:
            logging.info(f"کراول موفق: {len(prices)} قیمت معتبر استخراج شد")
        else:
            logging.warning("هیچ قیمتی از کراول بدست نیامد")
        
        return prices

    def get_currency_and_gold_prices(self):
        """دریافت قیمت ارز و طلا"""
        # اول API امتحان کن
        prices = self.get_tgju_prices_api()
        
        # اگر API کار نکرد، کراول کن
        if not prices:
            prices = self.get_tgju_prices_scraping()
        
        # اگر هنوز چیزی نگرفتی، از منابع دیگه استفاده کن
        if not prices:
            prices = self.get_fallback_prices()
        
        # اضافه کردن تتر به قیمت‌های اصلی
        tether_price = self.get_tether_price()
        if tether_price != "🔄 در حال آپدیت":
            prices['💳 تتر'] = tether_price
        
        return prices

    def get_fallback_prices(self):
        """منابع جایگزین برای قیمت‌ها"""
        prices = {}
        
        # bonbast.com - معتبرترین منبع قیمت ارز
        try:
            response = self.session.get('https://bonbast.com/', timeout=10)
            if response.status_code == 200:
                content = response.text
                
                # استخراج قیمت دلار از bonbast - قیمت‌ها به ریال است
                usd_match = re.search(r'"usd":\s*{\s*"sell":\s*(\d+)', content)
                if usd_match:
                    usd_price_rial = int(usd_match.group(1))
                    usd_price_toman = usd_price_rial // 10
                    prices['دلار آمریکا'] = f"{usd_price_toman:,} تومان"
                
                # استخراج قیمت یورو از bonbast
                eur_match = re.search(r'"eur":\s*{\s*"sell":\s*(\d+)', content)
                if eur_match:
                    eur_price_rial = int(eur_match.group(1))
                    eur_price_toman = eur_price_rial // 10
                    prices['یورو'] = f"{eur_price_toman:,} تومان"
                
                logging.info(f"قیمت از bonbast دریافت شد: {len(prices)} آیتم")
                
        except Exception as e:
            logging.error(f"خطا در bonbast: {e}")
        
        # اگر هنوز هیچی نداریم، پیام در حال آپدیت
        if not prices:
            prices = {
                'دلار آمریکا': "🔄 در حال آپدیت",
                'یورو': "🔄 در حال آپدیت",
                'طلای 18 عیار': "🔄 در حال آپدیت",
                'سکه امامی': "🔄 در حال آپدیت"
            }
            logging.warning("قیمت‌ها در دسترس نیستند - نمایش پیام در حال آپدیت")
        
        return prices

    def get_tether_price(self):
        """دریافت قیمت تتر از صرافی‌های ایرانی"""
        tether_price = None
        
        # لیست صرافی‌ها برای دریافت قیمت تتر
        sources = [
            {
                'name': 'Nobitex',
                'url': 'https://api.nobitex.ir/v2/orderbook/USDTIRT',
                'parser': lambda data: int(float(data.get('lastTradePrice', 0)) / 10) if data.get('lastTradePrice') else None
            },
            {
                'name': 'Wallex', 
                'url': 'https://api.wallex.ir/v1/markets',
                'parser': lambda data: self._parse_wallex(data)
            },
            {
                'name': 'Ramzinex',
                'url': 'https://publicapi.ramzinex.com/exchange/api/v1.0/exchange/pairs',
                'parser': lambda data: self._parse_ramzinex(data)
            }
        ]
        
        for source in sources:
            try:
                response = self.session.get(source['url'], timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    price = source['parser'](data)
                    if price and price > 0:
                        tether_price = price
                        logging.info(f"قیمت تتر از {source['name']}: {price:,} تومان")
                        break
            except Exception as e:
                logging.error(f"خطا در دریافت تتر از {source['name']}: {e}")
                continue
        
        return f"{tether_price:,} تومان" if tether_price else "🔄 در حال آپدیت"

    def _parse_wallex(self, data):
        """پارس قیمت تتر از Wallex"""
        try:
            symbols = data.get('result', {}).get('symbols', [])
            for symbol in symbols:
                if symbol.get('symbol') == 'USDTTMN':
                    return int(float(symbol.get('stats', {}).get('lastPrice', 0)))
        except:
            pass
        return None

    def _parse_ramzinex(self, data):
        """پارس قیمت تتر از Ramzinex"""
        try:
            pairs = data.get('data', [])
            for pair in pairs:
                if pair.get('pair_id') == 14:  # USDT/IRR
                    price_rial = float(pair.get('last', 0))
                    return int(price_rial / 10)  # تبدیل به تومان
        except:
            pass
        return None

    def get_crypto_prices(self):
        """دریافت قیمت کریپتو"""
        prices = {}
        
        # دریافت قیمت بیتکوین و اتریوم از CoinGecko
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
                
                logging.info("قیمت بیتکوین و اتریوم دریافت شد")
        except Exception as e:
            logging.error(f"خطا در کریپتو: {e}")
            prices['بیت‌کوین'] = "🔄 در حال آپدیت"
            prices['اتریوم'] = "🔄 در حال آپدیت"
        
        return prices

    def format_message(self, main_prices, crypto_prices):
        """فرمت کردن پیام"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # بررسی آیا همه قیمت‌ها در حال آپدیت هستند
        all_updating = all("در حال آپدیت" in str(price) for price in main_prices.values())
        
        if all_updating:
            message = f"⏳ سیستم در حال دریافت قیمت‌ها\n"
            message += f"🕐 زمان: {current_time}\n\n"
            message += "لطفاً چند لحظه صبر کنید...\n"
            message += f"🔄 آپدیت بعدی: {UPDATE_INTERVAL} دقیقه دیگر\n"
            message += "📱 @asle_tehran"
        else:
            message = f"📊 قیمت‌های لحظه‌ای\n"
            message += f"🕐 آپدیت: {current_time}\n\n"
            
            # ارز و طلا
            if main_prices:
                message += "💰 بازار ارز و طلا:\n"
                for item, price in main_prices.items():
                    if 'دلار' in item:
                        message += f"💵 {item}: {price}\n"
                    elif 'یورو' in item:
                        message += f"💶 {item}: {price}\n"
                    elif 'تتر' in item:
                        message += f"{item}: {price}\n"
                    elif 'طلا' in item:
                        message += f"🥇 {item}: {price}\n"
                    elif 'سکه' in item:
                        message += f"🪙 {item}: {price}\n"
                message += "\n"
            
            # کریپتو
            if crypto_prices:
                message += "₿ ارزهای دیجیتال:\n"
                for crypto, price in crypto_prices.items():
                    if 'بیت‌کوین' in crypto:
                        message += f"🟠 {crypto}: {price}\n"
                    elif 'اتریوم' in crypto:
                        message += f"🔵 {crypto}: {price}\n"
                    else:
                        message += f"• {crypto}: {price}\n"
                message += "\n"
            
            message += f"🔄 آپدیت بعدی: {UPDATE_INTERVAL} دقیقه دیگر\n"
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
            main_prices = self.get_currency_and_gold_prices()
            crypto_prices = self.get_crypto_prices()
            
            logging.info(f"قیمت‌ها: اصلی={len(main_prices)}, کریپتو={len(crypto_prices)}")
            
            message = self.format_message(main_prices, crypto_prices)
            
            success = asyncio.run(self.send_message(message))
            
            if success:
                self.consecutive_failures = 0
                logging.info("آپدیت موفق")
            else:
                self.consecutive_failures += 1
                
        except Exception as e:
            self.consecutive_failures += 1
            logging.error(f"خطای کلی: {e}")

def main():
    if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or CHAT_ID == "YOUR_CHAT_ID_HERE":
        print("❌ لطفاً TOKEN و CHAT_ID را تنظیم کنید!")
        return
    
    monitor = PriceMonitor(TELEGRAM_BOT_TOKEN, CHAT_ID)
    
    # تست اولیه
    logging.info("تست اولیه...")
    monitor.collect_and_send_prices()
    
    # زمان‌بندی
    schedule.every(UPDATE_INTERVAL).minutes.do(monitor.collect_and_send_prices)
    
    logging.info(f"ربات شروع شد. آپدیت هر {UPDATE_INTERVAL} دقیقه.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logging.info("ربات متوقف شد")

if __name__ == "__main__":
    main()
