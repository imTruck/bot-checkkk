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
import json

# تنظیمات
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# تنظیم لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class IranianPriceBot:
    def __init__(self, bot_token, chat_id):
        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fa,en;q=0.9'
        }

    def get_dollar_price(self):
        """دلار از منابع ایرانی"""
        
        # روش 1: TGJU مستقیم
        try:
            logging.info("دلار: TGJU...")
            url = 'https://www.tgju.org/'
            response = requests.get(url, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # جستجوی ردیف دلار
                dollar_row = soup.find('tr', {'data-market-row': 'price_dollar_rl'})
                if dollar_row:
                    # جستجوی td با قیمت
                    price_cells = dollar_row.find_all('td')
                    for cell in price_cells:
                        text = cell.text.strip()
                        # بررسی عدد 5 رقمی (مثل 95,060)
                        if re.match(r'\d{2},\d{3}', text):
                            price = int(text.replace(',', ''))
                            if 80000 <= price <= 120000:  # محدوده منطقی دلار
                                logging.info(f"✓ دلار TGJU: {price:,}")
                                return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا TGJU دلار: {e}")
        
        # روش 2: Bonbast
        try:
            logging.info("دلار: Bonbast...")
            url = 'https://bonbast.com/'
            response = requests.get(url, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                html = response.text
                
                # جستجوی قیمت دلار فروش
                pattern = r'USD.*?Sell.*?(\d{2},?\d{3})'
                match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
                if match:
                    price = int(match.group(1).replace(',', ''))
                    if 80000 <= price <= 120000:
                        logging.info(f"✓ دلار Bonbast: {price:,}")
                        return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا Bonbast: {e}")
        
        # روش 3: Arzdigital
        try:
            logging.info("دلار: Arzdigital...")
            url = 'https://arzdigital.com/coins/us-dollar/'
            response = requests.get(url, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # جستجوی قیمت در صفحه
                price_div = soup.find('div', class_='arz-coin-page-data__price-irt')
                if price_div:
                    text = price_div.text.strip()
                    match = re.search(r'(\d{2},?\d{3})', text)
                    if match:
                        price = int(match.group(1).replace(',', ''))
                        if 80000 <= price <= 120000:
                            logging.info(f"✓ دلار Arzdigital: {price:,}")
                            return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا Arzdigital: {e}")
        
        return None

    def get_tether_price(self):
        """تتر از صرافی‌های ایرانی"""
        
        # روش 1: Nobitex
        try:
            logging.info("تتر: Nobitex...")
            url = 'https://api.nobitex.ir/market/stats?srcCurrency=usdt&dstCurrency=rls'
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'stats' in data and 'usdt-rls' in data['stats']:
                    if 'latest' in data['stats']['usdt-rls']:
                        price_rial = float(data['stats']['usdt-rls']['latest'])
                        price_toman = int(price_rial / 10)
                        if 80000 <= price_toman <= 120000:
                            logging.info(f"✓ تتر Nobitex: {price_toman:,}")
                            return f"{price_toman:,} تومان"
        except Exception as e:
            logging.error(f"خطا Nobitex: {e}")
        
        # روش 2: Ramzinex
        try:
            logging.info("تتر: Ramzinex...")
            url = 'https://publicapi.ramzinex.com/exchange/api/v1.0/exchange/pairs'
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for pair in data.get('data', []):
                    if pair.get('base_currency_symbol') == 'usdt' and pair.get('quote_currency_symbol') == 'irr':
                        price_rial = float(pair.get('sell', 0))
                        price_toman = int(price_rial / 10)
                        if 80000 <= price_toman <= 120000:
                            logging.info(f"✓ تتر Ramzinex: {price_toman:,}")
                            return f"{price_toman:,} تومان"
        except Exception as e:
            logging.error(f"خطا Ramzinex: {e}")
        
        return None

    def get_gold_price(self):
        """طلای 18 عیار از منابع ایرانی"""
        
        # روش 1: TGJU
        try:
            logging.info("طلا: TGJU...")
            url = 'https://www.tgju.org/'
            response = requests.get(url, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # جستجوی ردیف طلا 18
                gold_row = soup.find('tr', {'data-market-row': 'geram18'})
                if gold_row:
                    price_cells = gold_row.find_all('td')
                    for cell in price_cells:
                        text = cell.text.strip()
                        # عدد 7 رقمی (مثل 3,200,000)
                        if re.match(r'\d{1,2},\d{3},\d{3}', text):
                            price = int(text.replace(',', ''))
                            if 2000000 <= price <= 5000000:  # محدوده منطقی طلا
                                logging.info(f"✓ طلا TGJU: {price:,}")
                                return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا TGJU طلا: {e}")
        
        # روش 2: Bonbast
        try:
            logging.info("طلا: Bonbast...")
            url = 'https://bonbast.com/'
            response = requests.get(url, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                html = response.text
                
                # جستجوی قیمت طلا 18
                pattern = r'18.*?Karat.*?(\d{1,2},?\d{3},?\d{3})'
                match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
                if match:
                    price = int(match.group(1).replace(',', ''))
                    if 2000000 <= price <= 5000000:
                        logging.info(f"✓ طلا Bonbast: {price:,}")
                        return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا Bonbast طلا: {e}")
        
        # روش 3: Tala.ir
        try:
            logging.info("طلا: Tala.ir...")
            url = 'https://www.tala.ir/'
            response = requests.get(url, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # جستجوی قیمت طلا 18
                gold_elements = soup.find_all(text=re.compile(r'طلای?\s*18'))
                for elem in gold_elements:
                    parent = elem.parent
                    if parent:
                        text = parent.get_text()
                        match = re.search(r'(\d{1,2},\d{3},\d{3})', text)
                        if match:
                            price = int(match.group(1).replace(',', ''))
                            if 2000000 <= price <= 5000000:
                                logging.info(f"✓ طلا Tala.ir: {price:,}")
                                return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا Tala.ir: {e}")
        
        return None

    def get_coin_price(self):
        """سکه امامی از منابع ایرانی"""
        
        # روش 1: TGJU
        try:
            logging.info("سکه: TGJU...")
            url = 'https://www.tgju.org/'
            response = requests.get(url, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # جستجوی ردیف سکه
                coin_row = soup.find('tr', {'data-market-row': 'sekee'})
                if coin_row:
                    price_cells = coin_row.find_all('td')
                    for cell in price_cells:
                        text = cell.text.strip()
                        # عدد 8 رقمی (مثل 47,000,000)
                        if re.match(r'\d{2,3},\d{3},\d{3}', text):
                            price = int(text.replace(',', ''))
                            # اگر ریال بود تبدیل به تومان
                            if price > 100000000:
                                price = price // 10
                            if 30000000 <= price <= 80000000:  # محدوده منطقی سکه
                                logging.info(f"✓ سکه TGJU: {price:,}")
                                return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا TGJU سکه: {e}")
        
        # روش 2: Bonbast
        try:
            logging.info("سکه: Bonbast...")
            url = 'https://bonbast.com/'
            response = requests.get(url, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                html = response.text
                
                # جستجوی قیمت سکه امامی
                pattern = r'Emami.*?(\d{2,3},?\d{3},?\d{3})'
                match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
                if match:
                    price = int(match.group(1).replace(',', ''))
                    if price > 100000000:
                        price = price // 10
                    if 30000000 <= price <= 80000000:
                        logging.info(f"✓ سکه Bonbast: {price:,}")
                        return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا Bonbast سکه: {e}")
        
        return None

    def get_crypto_prices(self):
        """کریپتو از API های معتبر"""
        prices = {}
        
        # CoinGecko
        try:
            url = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd'
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if 'bitcoin' in data:
                    prices['بیت‌کوین'] = f"${data['bitcoin']['usd']:,.0f}"
                if 'ethereum' in data:
                    prices['اتریوم'] = f"${data['ethereum']['usd']:,.0f}"
                logging.info("✓ کریپتو از CoinGecko")
        except:
            pass
        
        # Binance
        if not prices:
            try:
                response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', timeout=10)
                if response.status_code == 200:
                    btc = float(response.json()['price'])
                    prices['بیت‌کوین'] = f"${btc:,.0f}"
                
                response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT', timeout=10)
                if response.status_code == 200:
                    eth = float(response.json()['price'])
                    prices['اتریوم'] = f"${eth:,.0f}"
                logging.info("✓ کریپتو از Binance")
            except:
                pass
        
        return prices

    def collect_and_send_prices(self):
        """جمع‌آوری و ارسال"""
        logging.info("=" * 50)
        logging.info("🚀 شروع دریافت از منابع ایرانی...")
        
        try:
            # جمع‌آوری
            dollar = self.get_dollar_price()
            tether = self.get_tether_price()
            gold = self.get_gold_price()
            coin = self.get_coin_price()
            crypto = self.get_crypto_prices()
            
            # پیام
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            message = f"📊 قیمت‌های لحظه‌ای\n"
            message += f"🕐 آپدیت: {current_time}\n\n"
            
            message += "💰 بازار ارز و طلا:\n"
            message += f"💵 دلار آمریکا: {dollar if dollar else '🔄 در حال آپدیت'}\n"
            message += f"💳 تتر: {tether if tether else '🔄 در حال آپدیت'}\n"
            message += f"🥇 طلای 18 عیار: {gold if gold else '🔄 در حال آپدیت'}\n"
            message += f"🪙 سکه امامی: {coin if coin else '🔄 در حال آپدیت'}\n\n"
            
            message += "₿ ارزهای دیجیتال:\n"
            message += f"🟠 بیت‌کوین: {crypto.get('بیت‌کوین', '🔄 در حال آپدیت')}\n"
            message += f"🔵 اتریوم: {crypto.get('اتریوم', '🔄 در حال آپدیت')}\n\n"
            
            message += "🔄 آپدیت بعدی: 30 دقیقه دیگر\n"
            message += "📱 @asle_tehran"
            
            # لاگ
            logging.info("نتایج:")
            logging.info(f"  دلار: {dollar}")
            logging.info(f"  تتر: {tether}")
            logging.info(f"  طلا: {gold}")
            logging.info(f"  سکه: {coin}")
            logging.info(f"  کریپتو: {crypto}")
            
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
        """ارسال پیام"""
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message)
            return True
        except Exception as e:
            logging.error(f"خطا در ارسال: {e}")
            return False

def main():
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        print("❌ توکن و چت آیدی را تنظیم کنید!")
        sys.exit(1)
    
    logging.info("🤖 ربات منابع ایرانی شروع شد")
    bot = IranianPriceBot(TELEGRAM_BOT_TOKEN, CHAT_ID)
    bot.collect_and_send_prices()
    logging.info("✅ پایان")
    sys.exit(0)

if __name__ == "__main__":
    main()
