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

    def get_dollar_from_tgju_span(self):
        """دلار دقیقاً از span با کلاس info-price"""
        try:
            logging.info("Getting dollar from TGJU span...")
            
            # صفحه دلار TGJU
            url = 'https://www.tgju.org/profile/price_dollar_rl'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            logging.info(f"TGJU response status: {response.status_code}")
            
            if response.status_code == 200:
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                
                # جستجوی span با کلاس info-price
                price_span = soup.find('span', class_='info-price')
                
                if price_span:
                    price_text = price_span.text.strip()
                    logging.info(f"Found span text: {price_text}")
                    
                    # حذف کاما و تبدیل به عدد
                    price_str = price_text.replace(',', '')
                    if price_str.isdigit():
                        price = int(price_str)
                        # اگر 6 رقمی است (مثل 950600)، تقسیم بر 10
                        if price > 500000:
                            price = price // 10
                        
                        logging.info(f"✓ Dollar from TGJU span: {price:,}")
                        return f"{price:,} تومان"
                else:
                    logging.warning("span with class 'info-price' not found")
                    
        except Exception as e:
            logging.error(f"TGJU span error: {e}")
        
        # اگر span پیدا نشد، از روش regex
        try:
            logging.info("Trying regex method...")
            url = 'https://www.tgju.org/profile/price_dollar_rl'
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            
            if response.status_code == 200:
                html = response.text
                
                # جستجوی pattern
                pattern = r'<span[^>]*class="info-price"[^>]*>([^<]+)</span>'
                match = re.search(pattern, html)
                
                if match:
                    price_text = match.group(1).strip()
                    price_str = price_text.replace(',', '')
                    if price_str.isdigit():
                        price = int(price_str)
                        if price > 500000:
                            price = price // 10
                        logging.info(f"✓ Dollar from regex: {price:,}")
                        return f"{price:,} تومان"
                        
        except Exception as e:
            logging.error(f"Regex error: {e}")
        
        return None

    def get_tether_from_nobitex(self):
        """تتر از Nobitex"""
        try:
            url = 'https://api.nobitex.ir/market/stats?srcCurrency=usdt&dstCurrency=rls'
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'stats' in data and 'usdt-rls' in data['stats']:
                    price_rial = float(data['stats']['usdt-rls']['latest'])
                    price_toman = int(price_rial / 10)
                    logging.info(f"✓ Tether: {price_toman:,}")
                    return f"{price_toman:,} تومان"
        except Exception as e:
            logging.error(f"Nobitex error: {e}")
        
        return None

    def get_gold_from_tgju(self):
        """طلا از TGJU"""
        try:
            # API
            url = 'https://api.tgju.org/v1/data/sana/json'
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if 'geram18' in data and 'p' in data['geram18']:
                    price_str = str(data['geram18']['p']).replace(',', '')
                    if price_str.isdigit():
                        price = int(price_str)
                        logging.info(f"✓ Gold: {price:,}")
                        return f"{price:,} تومان"
        except:
            pass
        
        # HTML اگر API کار نکرد
        try:
            url = 'https://www.tgju.org/profile/geram18'
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                price_span = soup.find('span', class_='info-price')
                
                if price_span:
                    price_text = price_span.text.strip().replace(',', '')
                    if price_text.isdigit():
                        price = int(price_text)
                        logging.info(f"✓ Gold from span: {price:,}")
                        return f"{price:,} تومان"
        except:
            pass
        
        return None

    def get_coin_from_tgju(self):
        """سکه از TGJU"""
        try:
            # API
            url = 'https://api.tgju.org/v1/data/sana/json'
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if 'sekee' in data and 'p' in data['sekee']:
                    price_str = str(data['sekee']['p']).replace(',', '')
                    if price_str.isdigit():
                        price = int(price_str)
                        if price > 100000000:
                            price = price // 10
                        logging.info(f"✓ Coin: {price:,}")
                        return f"{price:,} تومان"
        except:
            pass
        
        # HTML اگر API کار نکرد
        try:
            url = 'https://www.tgju.org/profile/sekee'
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                price_span = soup.find('span', class_='info-price')
                
                if price_span:
                    price_text = price_span.text.strip().replace(',', '')
                    if price_text.isdigit():
                        price = int(price_text)
                        if price > 100000000:
                            price = price // 10
                        logging.info(f"✓ Coin from span: {price:,}")
                        return f"{price:,} تومان"
        except:
            pass
        
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
                logging.info(f"✓ Crypto from CoinGecko")
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
                
                logging.info(f"✓ Crypto from Binance")
            except:
                pass
        
        return prices

    def collect_and_send_prices(self):
        """جمع‌آوری و ارسال"""
        logging.info("=" * 50)
        logging.info("🚀 Starting with TGJU span method...")
        
        try:
            # جمع‌آوری
            dollar = self.get_dollar_from_tgju_span()
            tether = self.get_tether_from_nobitex()
            gold = self.get_gold_from_tgju()
            coin = self.get_coin_from_tgju()
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
            logging.info("Results:")
            logging.info(f"  Dollar: {dollar}")
            logging.info(f"  Tether: {tether}")
            logging.info(f"  Gold: {gold}")
            logging.info(f"  Coin: {coin}")
            logging.info(f"  Crypto: {crypto}")
            
            # ارسال
            success = asyncio.run(self.send_message(message))
            
            if success:
                logging.info("✅ Message sent")
            else:
                logging.error("❌ Failed to send")
                
        except Exception as e:
            logging.error(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

    async def send_message(self, message):
        """ارسال پیام"""
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message)
            return True
        except Exception as e:
            logging.error(f"Send error: {e}")
            return False

def main():
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        print("❌ Set TELEGRAM_BOT_TOKEN and CHAT_ID!")
        sys.exit(1)
    
    logging.info("🤖 Bot started")
    bot = PriceBot(TELEGRAM_BOT_TOKEN, CHAT_ID)
    bot.collect_and_send_prices()
    logging.info("✅ Done")
    sys.exit(0)

if __name__ == "__main__":
    main()
