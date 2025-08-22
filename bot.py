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

class PriceBot:
    def __init__(self, bot_token, chat_id):
        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id

    def get_crypto_prices(self):
        """کریپتو - دست نمی‌زنیم"""
        prices = {}
        
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

    def get_tether_from_sites(self):
        """تتر - دست نمی‌زنیم"""
        try:
            url = 'https://api.nobitex.ir/market/stats?srcCurrency=usdt&dstCurrency=rls'
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'stats' in data:
                    if 'usdt-rls' in data['stats']:
                        if 'latest' in data['stats']['usdt-rls']:
                            price_rial = data['stats']['usdt-rls']['latest']
                            price_toman = int(float(price_rial) / 10)
                            logging.info(f"✓ تتر Nobitex: {price_toman:,}")
                            return f"{price_toman:,} تومان"
        except Exception as e:
            logging.error(f"خطا Nobitex: {e}")
        
        return None

    def get_dollar_correct(self):
        """دلار با روش دقیق‌تر"""
        
        # روش 1: TGJU با BeautifulSoup
        try:
            logging.info("دلار: TGJU با BeautifulSoup...")
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get('https://www.tgju.org/', headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # جستجوی tr با data-market-row
                dollar_row = soup.find('tr', {'data-market-row': 'price_dollar_rl'})
                if dollar_row:
                    # جستجوی td ها
                    tds = dollar_row.find_all('td')
                    for td in tds:
                        text = td.get_text().strip()
                        # عدد 5 یا 6 رقمی
                        if re.match(r'^\d{2,3},?\d{3}$', text):
                            price_str = text.replace(',', '')
                            price = int(price_str)
                            logging.info(f"✓ دلار TGJU: {price:,}")
                            return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا TGJU: {e}")
        
        # روش 2: صفحه مستقیم دلار TGJU
        try:
            logging.info("دلار: صفحه مستقیم TGJU...")
            response = requests.get('https://www.tgju.org/profile/price_dollar_rl', 
                                  headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # جستجوی span با class مربوط به قیمت
                price_spans = soup.find_all('span', class_=re.compile(r'price|value'))
                for span in price_spans:
                    text = span.get_text().strip()
                    if re.match(r'^\d{2,3},?\d{3}$', text):
                        price_str = text.replace(',', '')
                        price = int(price_str)
                        logging.info(f"✓ دلار صفحه مستقیم: {price:,}")
                        return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا صفحه مستقیم: {e}")
        
        # روش 3: Bonbast
        try:
            logging.info("دلار: Bonbast...")
            response = requests.get('https://bonbast.com/', 
                                  headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # جستجوی td هایی که USD دارند
                tds = soup.find_all('td')
                for i, td in enumerate(tds):
                    if 'USD' in td.get_text():
                        # چک کردن td های بعدی برای قیمت
                        for j in range(i+1, min(i+4, len(tds))):
                            text = tds[j].get_text().strip()
                            if re.match(r'^\d{2,3},?\d{3}$', text):
                                price_str = text.replace(',', '')
                                price = int(price_str)
                                logging.info(f"✓ دلار Bonbast: {price:,}")
                                return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا Bonbast: {e}")
        
        return None

    def get_gold_correct(self):
        """طلا با روش دقیق‌تر"""
        
        # روش 1: TGJU API
        try:
            logging.info("طلا: TGJU API...")
            response = requests.get('https://api.tgju.org/v1/data/sana/json', timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if 'geram18' in data and 'p' in data['geram18']:
                    price_str = str(data['geram18']['p']).replace(',', '')
                    if price_str.isdigit():
                        price = int(price_str)
                        logging.info(f"✓ طلا API: {price:,}")
                        return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا طلا API: {e}")
        
        # روش 2: TGJU HTML
        try:
            logging.info("طلا: TGJU HTML...")
            response = requests.get('https://www.tgju.org/', 
                                  headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # جستجوی tr با data-market-row
                gold_row = soup.find('tr', {'data-market-row': 'geram18'})
                if gold_row:
                    tds = gold_row.find_all('td')
                    for td in tds:
                        text = td.get_text().strip()
                        # عدد 7 رقمی
                        if re.match(r'^\d{1,2},?\d{3},?\d{3}$', text):
                            price_str = text.replace(',', '')
                            price = int(price_str)
                            logging.info(f"✓ طلا HTML: {price:,}")
                            return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا طلا HTML: {e}")
        
        # روش 3: صفحه مستقیم طلا
        try:
            logging.info("طلا: صفحه مستقیم...")
            response = requests.get('https://www.tgju.org/profile/geram18', 
                                  headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                price_spans = soup.find_all('span', class_=re.compile(r'price|value'))
                for span in price_spans:
                    text = span.get_text().strip()
                    if re.match(r'^\d{1,2},?\d{3},?\d{3}$', text):
                        price_str = text.replace(',', '')
                        price = int(price_str)
                        logging.info(f"✓ طلا صفحه مستقیم: {price:,}")
                        return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا طلا مستقیم: {e}")
        
        return None

    def get_coin_correct(self):
        """سکه با روش دقیق‌تر"""
        
        # روش 1: TGJU API
        try:
            logging.info("سکه: TGJU API...")
            response = requests.get('https://api.tgju.org/v1/data/sana/json', timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if 'sekee' in data and 'p' in data['sekee']:
                    price_str = str(data['sekee']['p']).replace(',', '')
                    if price_str.isdigit():
                        price = int(price_str)
                        # اگر ریال بود
                        if price > 100000000:
                            price = price // 10
                        logging.info(f"✓ سکه API: {price:,}")
                        return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا سکه API: {e}")
        
        # روش 2: TGJU HTML
        try:
            logging.info("سکه: TGJU HTML...")
            response = requests.get('https://www.tgju.org/', 
                                  headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # جستجوی tr با data-market-row
                coin_row = soup.find('tr', {'data-market-row': 'sekee'})
                if coin_row:
                    tds = coin_row.find_all('td')
                    for td in tds:
                        text = td.get_text().strip()
                        # عدد 8 یا 9 رقمی
                        if re.match(r'^\d{2,3},?\d{3},?\d{3}$', text):
                            price_str = text.replace(',', '')
                            price = int(price_str)
                            if price > 100000000:
                                price = price // 10
                            logging.info(f"✓ سکه HTML: {price:,}")
                            return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا سکه HTML: {e}")
        
        # روش 3: صفحه مستقیم سکه
        try:
            logging.info("سکه: صفحه مستقیم...")
            response = requests.get('https://www.tgju.org/profile/sekee', 
                                  headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                price_spans = soup.find_all('span', class_=re.compile(r'price|value'))
                for span in price_spans:
                    text = span.get_text().strip()
                    if re.match(r'^\d{2,3},?\d{3},?\d{3}$', text):
                        price_str = text.replace(',', '')
                        price = int(price_str)
                        if price > 100000000:
                            price = price // 10
                        logging.info(f"✓ سکه صفحه مستقیم: {price:,}")
                        return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا سکه مستقیم: {e}")
        
        return None

    def collect_and_send_prices(self):
        """جمع‌آوری و ارسال"""
        logging.info("=" * 50)
        logging.info("🚀 شروع...")
        
        try:
            # کریپتو و تتر - دست نمی‌زنیم
            crypto = self.get_crypto_prices()
            tether = self.get_tether_from_sites()
            
            # دلار، طلا، سکه - روش‌های جدید
            dollar = self.get_dollar_correct()
            gold = self.get_gold_correct()
            coin = self.get_coin_correct()
            
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
    
    logging.info("🤖 ربات شروع شد")
    bot = PriceBot(TELEGRAM_BOT_TOKEN, CHAT_ID)
    bot.collect_and_send_prices()
    logging.info("✅ پایان")
    sys.exit(0)

if __name__ == "__main__":
    main()
