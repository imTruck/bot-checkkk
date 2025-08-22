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

    def get_dollar_from_sites(self):
        """دلار فقط از سایت‌ها"""
        
        # روش 1: TGJU HTML
        try:
            logging.info("دلار: خواندن از TGJU...")
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get('https://www.tgju.org/', headers=headers, timeout=15)
            
            if response.status_code == 200:
                html = response.text
                
                # جستجوی همه اعداد 5 رقمی
                numbers = re.findall(r'\d{2},\d{3}', html)
                for num in numbers:
                    price = int(num.replace(',', ''))
                    # اولین عدد 5 رقمی
                    logging.info(f"✓ دلار TGJU: {price:,}")
                    return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا TGJU: {e}")
        
        # روش 2: Bonbast HTML
        try:
            logging.info("دلار: خواندن از Bonbast...")
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get('https://bonbast.com/', headers=headers, timeout=15)
            
            if response.status_code == 200:
                html = response.text
                
                # جستجوی اعداد 5 رقمی
                numbers = re.findall(r'\d{2},\d{3}', html)
                for num in numbers:
                    price = int(num.replace(',', ''))
                    logging.info(f"✓ دلار Bonbast: {price:,}")
                    return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا Bonbast: {e}")
        
        return None

    def get_tether_from_sites(self):
        """تتر فقط از API صرافی‌ها"""
        
        # Nobitex API
        try:
            logging.info("تتر: خواندن از Nobitex API...")
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
        
        # Wallex API
        try:
            logging.info("تتر: خواندن از Wallex API...")
            url = 'https://api.wallex.ir/v1/markets'
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'result' in data:
                    if 'symbols' in data['result']:
                        if 'USDTTMN' in data['result']['symbols']:
                            price = data['result']['symbols']['USDTTMN']['stats']['bidPrice']
                            price_int = int(float(price))
                            logging.info(f"✓ تتر Wallex: {price_int:,}")
                            return f"{price_int:,} تومان"
        except Exception as e:
            logging.error(f"خطا Wallex: {e}")
        
        return None

    def get_gold_from_sites(self):
        """طلا فقط از سایت‌ها"""
        
        # TGJU API
        try:
            logging.info("طلا: خواندن از TGJU API...")
            url = 'https://api.tgju.org/v1/data/sana/json'
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if 'geram18' in data:
                    if 'p' in data['geram18']:
                        price_str = str(data['geram18']['p']).replace(',', '')
                        if price_str.isdigit():
                            price = int(price_str)
                            logging.info(f"✓ طلا TGJU: {price:,}")
                            return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا TGJU API: {e}")
        
        # TGJU HTML
        try:
            logging.info("طلا: خواندن از TGJU HTML...")
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get('https://www.tgju.org/', headers=headers, timeout=15)
            
            if response.status_code == 200:
                html = response.text
                
                # جستجوی اعداد 7 رقمی
                numbers = re.findall(r'\d{1,2},\d{3},\d{3}', html)
                for num in numbers:
                    price = int(num.replace(',', ''))
                    logging.info(f"✓ طلا HTML: {price:,}")
                    return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا TGJU HTML: {e}")
        
        return None

    def get_coin_from_sites(self):
        """سکه فقط از سایت‌ها"""
        
        # TGJU API
        try:
            logging.info("سکه: خواندن از TGJU API...")
            url = 'https://api.tgju.org/v1/data/sana/json'
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if 'sekee' in data:
                    if 'p' in data['sekee']:
                        price_str = str(data['sekee']['p']).replace(',', '')
                        if price_str.isdigit():
                            price = int(price_str)
                            # اگر عدد خیلی بزرگ بود (ریال) تقسیم بر 10
                            if price > 100000000:
                                price = price // 10
                            logging.info(f"✓ سکه TGJU: {price:,}")
                            return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا TGJU API: {e}")
        
        # TGJU HTML
        try:
            logging.info("سکه: خواندن از TGJU HTML...")
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get('https://www.tgju.org/', headers=headers, timeout=15)
            
            if response.status_code == 200:
                html = response.text
                
                # جستجوی اعداد 8 رقمی
                numbers = re.findall(r'\d{2,3},\d{3},\d{3}', html)
                for num in numbers:
                    price = int(num.replace(',', ''))
                    if price > 100000000:
                        price = price // 10
                    logging.info(f"✓ سکه HTML: {price:,}")
                    return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا TGJU HTML: {e}")
        
        return None

    def collect_and_send_prices(self):
        """جمع‌آوری و ارسال"""
        logging.info("=" * 50)
        logging.info("🚀 شروع خواندن از سایت‌ها...")
        
        try:
            # کریپتو (دست نمی‌زنیم)
            crypto = self.get_crypto_prices()
            
            # از سایت‌ها
            dollar = self.get_dollar_from_sites()
            tether = self.get_tether_from_sites()
            gold = self.get_gold_from_sites()
            coin = self.get_coin_from_sites()
            
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
