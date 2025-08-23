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
                                    # تشخیص نوع قیمت و تبدیل مناسب
                                    if 'دلار' in title or 'dollar' in title or 'usd' in title:
                                        price_toman = int(price) // 10
                                        if price_toman > 1000:  # حداقل 1000 تومان
                                            prices['دلار آمریکا'] = f"{price_toman:,} تومان"
                                    
                                    elif 'یورو' in title or 'euro' in title or 'eur' in title:
                                        price_toman = int(price) // 10
                                        if price_toman > 1000:
                                            prices['یورو'] = f"{price_toman:,} تومان"
                                    
                                    elif 'طلا' in title or 'gold' in title or 'geram18' in title:
                                        # طلا ممکن است به ریال باشد
                                        if price > 10000000:  # اگر بیش از 10 میلیون بود، ریال است
                                            price_toman = int(price) // 10
                                        else:
                                            price_toman = int(price)
                                        if price_toman > 100000:  # حداقل 100 هزار تومان
                                            prices['طلای 18 عیار'] = f"{price_toman:,} تومان"
                                    
                                    elif 'سکه' in title or 'sekee' in title or 'emami' in title:
                                        # سکه ممکن است به ریال یا تومان باشد
                                        if price > 100000000:  # اگر بیش از 100 میلیون بود، ریال است
                                            price_toman = int(price) // 10
                                        else:
                                            price_toman = int(price)
                                        if price_toman > 1000000:  # حداقل 1 میلیون تومان
                                            prices['سکه امامی'] = f"{price_toman:,} تومان"
                    
                    elif isinstance(data, dict):
                        # فرمت دیکشنری
                        current = data.get('current', {})
                        
                        # دلار
                        if 'usd' in current or 'price_dollar_rl' in current:
                            key = 'usd' if 'usd' in current else 'price_dollar_rl'
                            usd_price = int(current[key].get('p', 0))
                            if usd_price > 10000:  # اگر بیش از 10000 بود، ریال است
                                usd_price = usd_price // 10
                            if usd_price > 1000:
                                prices['دلار آمریکا'] = f"{usd_price:,} تومان"
                        
                        # یورو
                        if 'eur' in current:
                            eur_price = int(current['eur'].get('p', 0))
                            if eur_price > 10000:
                                eur_price = eur_price // 10
                            if eur_price > 1000:
                                prices['یورو'] = f"{eur_price:,} تومان"
                        
                        # طلا 18 عیار
                        if 'geram18' in current:
                            gold_price = int(current['geram18'].get('p', 0))
                            if gold_price > 10000000:  # ریال
                                gold_price = gold_price // 10
                            if gold_price > 100000:
                                prices['طلای 18 عیار'] = f"{gold_price:,} تومان"
                        
                        # سکه
                        if 'sekee' in current:
                            coin_price = int(current['sekee'].get('p', 0))
                            if coin_price > 100000000:  # ریال
                                coin_price = coin_price // 10
                            if coin_price > 1000000:
                                prices['سکه امامی'] = f"{coin_price:,} تومان"
                    
                    if prices:
                        logging.info(f"API موفق: {len(prices)} قیمت از {api_url}")
                        logging.info(f"قیمت‌های دریافتی: {prices}")
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
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # جستجوی قیمت در المان‌های مختلف
                    price_elements = soup.find_all(['span', 'div'], class_=re.compile(r'price|value|number'))
                    
                    for elem in price_elements:
                        text = elem.get_text().strip()
                        # جستجوی الگوی عددی
                        match = re.search(r'(\d{1,3}(?:,\d{3})+)', text)
                        if match:
                            price_str = match.group(1).replace(',', '')
                            price = int(price_str)
                            
                            if price_type == 'dollar' and price > 100000:  # دلار حداقل 100,000 ریال
                                price_toman = price // 10
                                prices['دلار آمریکا'] = f"{price_toman:,} تومان"
                                break
                            
                            elif price_type == 'euro' and price > 100000:
                                price_toman = price // 10
                                prices['یورو'] = f"{price_toman:,} تومان"
                                break
                            
                            elif price_type == 'gold' and price > 1000000:  # طلا حداقل 1 میلیون ریال
                                price_toman = price // 10
                                prices['طلای 18 عیار'] = f"{price_toman:,} تومان"
                                break
                            
                            elif price_type == 'coin' and price > 10000000:  # سکه حداقل 10 میلیون ریال
                                price_toman = price // 10
                                prices['سکه امامی'] = f"{price_toman:,} تومان"
                                break
                
                logging.info(f"استخراج از {price_type}: {'موفق' if price_type in str(prices) else 'ناموفق'}")
                
            except Exception as e:
                logging.error(f"خطا در استخراج {price_type}: {e}")
        
        if prices:
            logging.info(f"کراول موفق: {len(prices)} قیمت معتبر استخراج شد")
        else:
            logging.warning("هیچ قیمتی از کراول بدست نیامد")
        
        return prices

    def get_currency_and_gold_prices(self):
        """دریافت قیمت ارز و طلا"""
        prices = {}
        
        # اول API امتحان کن
        api_prices = self.get_tgju_prices_api()
        if api_prices:
            prices.update(api_prices)
        
        # اگر چیزی کم است، کراول کن
        if len(prices) < 4:
            scraping_prices = self.get_tgju_prices_scraping()
            for key, value in scraping_prices.items():
                if key not in prices:
                    prices[key] = value
        
        # اگر هنوز چیزی کم است، از منابع دیگه استفاده کن
        if len(prices) < 4:
            fallback_prices = self.get_fallback_prices()
            for key, value in fallback_prices.items():
                if key not in prices or "آپدیت" not in prices[key]:
                    prices[key] = value
        
        # اضافه کردن تتر
        tether_price = self.get_tether_price()
        prices['تتر (USDT)'] = tether_price
        
        return prices

    def get_fallback_prices(self):
        """منابع جایگزین برای قیمت‌ها"""
        prices = {}
        
        # از nobitex برای ارز و طلا
        try:
            response = self.session.get('https://api.nobitex.ir/v2/orderbook/all', timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # استخراج قیمت‌ها از Nobitex
                if 'USDTIRT' in data:
                    usdt_price = int(float(data['USDTIRT']['lastTradePrice']) / 10)
                    if usdt_price > 1000:
                        # تخمین دلار از روی تتر
                        dollar_price = int(usdt_price * 1.02)  # معمولاً دلار 2% از تتر بیشتر است
                        prices['دلار آمریکا'] = f"{dollar_price:,} تومان"
                
                logging.info(f"قیمت از nobitex دریافت شد")
                
        except Exception as e:
            logging.error(f"خطا در nobitex: {e}")
        
        # از bonbast.com
        try:
            response = self.session.get('https://bonbast.com/', timeout=10)
            if response.status_code == 200:
                content = response.text
                
                # استخراج قیمت دلار
                usd_match = re.search(r'"usd":\s*{\s*"sell":\s*(\d+)', content)
                if usd_match:
                    usd_price_rial = int(usd_match.group(1))
                    usd_price_toman = usd_price_rial // 10
                    if usd_price_toman > 1000:
                        prices['دلار آمریکا'] = f"{usd_price_toman:,} تومان"
                
                # استخراج قیمت یورو
                eur_match = re.search(r'"eur":\s*{\s*"sell":\s*(\d+)', content)
                if eur_match:
                    eur_price_rial = int(eur_match.group(1))
                    eur_price_toman = eur_price_rial // 10
                    if eur_price_toman > 1000:
                        prices['یورو'] = f"{eur_price_toman:,} تومان"
                
                logging.info(f"قیمت از bonbast دریافت شد: {len(prices)} آیتم")
                
        except Exception as e:
            logging.error(f"خطا در bonbast: {e}")
        
        # اگر هنوز قیمت طلا و سکه نداریم
        if 'طلای 18 عیار' not in prices:
            prices['طلای 18 عیار'] = "🔄 در حال آپدیت"
        if 'سکه امامی' not in prices:
            prices['سکه امامی'] = "🔄 در حال آپدیت"
        
        return prices

    def get_tether_price(self):
        """دریافت قیمت تتر از صرافی‌های ایرانی"""
        
        # لیست صرافی‌ها برای دریافت قیمت تتر
        sources = [
            {
                'name': 'Nobitex',
                'url': 'https://api.nobitex.ir/v2/orderbook/USDTIRT',
                'parser': lambda data: int(float(data.get('lastTradePrice', 0)) / 10) if data.get('lastTradePrice') else 0
            },
            {
                'name': 'Nobitex-Stats',
                'url': 'https://api.nobitex.ir/market/stats?srcCurrency=usdt&dstCurrency=rls',
                'parser': lambda data: int(float(data.get('stats', {}).get('usdt-rls', {}).get('latest', 0)) / 10) if data.get('stats') else 0
            },
            {
                'name': 'Wallex',
                'url': 'https://api.wallex.ir/v1/markets',
                'parser': self._parse_wallex
            }
        ]
        
        for source in sources:
            try:
                response = self.session.get(source['url'], timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    price = source['parser'](data)
                    if price and price > 10000:  # حداقل 10 هزار تومان
                        logging.info(f"قیمت تتر از {source['name']}: {price:,} تومان")
                        return f"{price:,} تومان"
            except Exception as e:
                logging.error(f"خطا در دریافت تتر از {source['name']}: {e}")
                continue
        
        return "🔄 در حال آپدیت"

    def _parse_wallex(self, data):
        """پارس قیمت تتر از Wallex"""
        try:
            symbols = data.get('result', {}).get('symbols', [])
            for symbol in symbols:
                if symbol.get('symbol') == 'USDTTMN':
                    price = int(float(symbol.get('stats', {}).get('lastPrice', 0)))
                    if price > 0:
                        return price
        except:
            pass
        return 0

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
                    message += f"💳 {item}: {price}\n"
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
            logging.info(f"قیمت‌های اصلی: {main_prices}")
            
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
