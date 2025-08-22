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
        """کریپتو فقط از API"""
        prices = {}
        
        # Binance API
        try:
            logging.info("API: Binance BTC...")
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', timeout=10)
            if response.status_code == 200:
                btc_price = float(response.json()['price'])
                prices['بیت‌کوین'] = f"${btc_price:,.0f}"
                logging.info(f"✓ BTC: ${btc_price:,.0f}")
        except Exception as e:
            logging.error(f"خطا Binance BTC: {e}")
        
        try:
            logging.info("API: Binance ETH...")
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT', timeout=10)
            if response.status_code == 200:
                eth_price = float(response.json()['price'])
                prices['اتریوم'] = f"${eth_price:,.0f}"
                logging.info(f"✓ ETH: ${eth_price:,.0f}")
        except Exception as e:
            logging.error(f"خطا Binance ETH: {e}")
        
        # CoinGecko API (اگر Binance کار نکرد)
        if not prices:
            try:
                logging.info("API: CoinGecko...")
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
        """تتر فقط از API"""
        # Nobitex API
        try:
            logging.info("API: Nobitex USDT...")
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
        
        # Wallex API
        try:
            logging.info("API: Wallex USDT...")
            response = requests.get('https://api.wallex.ir/v1/markets', timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'result' in data and 'symbols' in data['result']:
                    symbols = data['result']['symbols']
                    if 'USDTTMN' in symbols:
                        price = int(float(symbols['USDTTMN']['stats']['bidPrice']))
                        logging.info(f"✓ USDT از Wallex: {price:,}")
                        return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا Wallex: {e}")
        
        return None

    def get_dollar_from_sources(self):
        """دلار فقط از منابع واقعی"""
        
        # Bonbast JSON API
        try:
            logging.info("API: Bonbast JSON...")
            response = requests.get('https://bonbast.com/json', timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'usd' in data and 'sell' in data['usd']:
                    price_str = str(data['usd']['sell']).replace(',', '')
                    if price_str.isdigit():
                        price = int(price_str)
                        logging.info(f"✓ دلار از Bonbast JSON: {price:,}")
                        return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا Bonbast JSON: {e}")
        
        # Bonbast HTML
        try:
            logging.info("HTML: Bonbast...")
            response = requests.get('https://bonbast.com/', 
                                  headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            if response.status_code == 200:
                html = response.text
                
                # جستجوی ساده برای عدد دلار
                numbers = re.findall(r'(\d{2},\d{3})', html)
                for num in numbers:
                    price = int(num.replace(',', ''))
                    if price > 50000:  # فقط چک کنیم که کوچک نباشد
                        logging.info(f"✓ دلار از Bonbast HTML: {price:,}")
                        return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا Bonbast HTML: {e}")
        
        # TGJU HTML
        try:
            logging.info("HTML: TGJU دلار...")
            response = requests.get('https://www.tgju.org/profile/price_dollar_rl', 
                                  headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            if response.status_code == 200:
                html = response.text
                
                # جستجوی عدد در HTML
                numbers = re.findall(r'(\d{2},\d{3})', html)
                for num in numbers:
                    price = int(num.replace(',', ''))
                    if price > 50000:
                        logging.info(f"✓ دلار از TGJU: {price:,}")
                        return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا TGJU دلار: {e}")
        
        return None

    def get_gold_from_sources(self):
        """طلا فقط از منابع واقعی"""
        
        # TGJU API
        try:
            logging.info("API: TGJU طلا...")
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
        
        # TGJU HTML
        try:
            logging.info("HTML: TGJU طلا...")
            response = requests.get('https://www.tgju.org/profile/geram18', 
                                  headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            if response.status_code == 200:
                html = response.text
                
                # جستجوی اعداد 7 رقمی (طلا)
                numbers = re.findall(r'(\d{1,2},\d{3},\d{3})', html)
                for num in numbers:
                    price = int(num.replace(',', ''))
                    if price > 1000000:  # فقط چک کنیم بزرگ باشد
                        logging.info(f"✓ طلا از TGJU HTML: {price:,}")
                        return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا TGJU HTML طلا: {e}")
        
        # TalaOnline HTML
        try:
            logging.info("HTML: TalaOnline...")
            response = requests.get('https://www.talaonline.com/', 
                                  headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            if response.status_code == 200:
                html = response.text
                
                # جستجو در محتوا
                numbers = re.findall(r'(\d{1,2},\d{3},\d{3})', html)
                for num in numbers:
                    price = int(num.replace(',', ''))
                    if price > 1000000:
                        logging.info(f"✓ طلا از TalaOnline: {price:,}")
                        return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا TalaOnline: {e}")
        
        return None

    def get_coin_from_sources(self):
        """سکه فقط از منابع واقعی"""
        
        # TGJU API
        try:
            logging.info("API: TGJU سکه...")
            response = requests.get('https://api.tgju.org/v1/data/sana/json', timeout=15)
            if response.status_code == 200:
                data = response.json()
                if 'sekee' in data and 'p' in data['sekee']:
                    price_str = str(data['sekee']['p']).replace(',', '')
                    if price_str.isdigit():
                        price = int(price_str)
                        # اگر خیلی بزرگ است، ریال است و تبدیل به تومان
                        if price > 100000000:
                            price = price // 10
                        logging.info(f"✓ سکه از TGJU API: {price:,}")
                        return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا TGJU API سکه: {e}")
        
        # TGJU HTML
        try:
            logging.info("HTML: TGJU سکه...")
            response = requests.get('https://www.tgju.org/profile/sekee', 
                                  headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            if response.status_code == 200:
                html = response.text
                
                # جستجوی اعداد 8 رقمی (سکه)
                numbers = re.findall(r'(\d{2,3},\d{3},\d{3})', html)
                for num in numbers:
                    price = int(num.replace(',', ''))
                    # تبدیل ریال به تومان اگر لازم باشد
                    if price > 100000000:
                        price = price // 10
                    if price > 10000000:  # فقط چک کنیم بزرگ باشد
                        logging.info(f"✓ سکه از TGJU HTML: {price:,}")
                        return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا TGJU HTML سکه: {e}")
        
        # TalaOnline HTML
        try:
            logging.info("HTML: TalaOnline سکه...")
            response = requests.get('https://www.talaonline.com/', 
                                  headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            if response.status_code == 200:
                html = response.text
                
                numbers = re.findall(r'(\d{2,3},\d{3},\d{3})', html)
                for num in numbers:
                    price = int(num.replace(',', ''))
                    if price > 100000000:
                        price = price // 10
                    if price > 10000000:
                        logging.info(f"✓ سکه از TalaOnline: {price:,}")
                        return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا TalaOnline سکه: {e}")
        
        return None

    def collect_and_send_prices(self):
        """جمع‌آوری و ارسال"""
        logging.info("=" * 50)
        logging.info("🚀 دریافت قیمت‌های واقعی...")
        
        try:
            # جمع‌آوری از منابع واقعی
            crypto_prices = self.get_crypto_from_api()
            tether = self.get_tether_from_api()
            dollar = self.get_dollar_from_sources()
            gold = self.get_gold_from_sources()
            coin = self.get_coin_from_sources()
            
            # ساخت پیام
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            message = f"📊 قیمت‌های لحظه‌ای\n"
            message += f"🕐 آپدیت: {current_time}\n\n"
            
            # بازار ارز و طلا
            message += "💰 بازار ارز و طلا:\n"
            message += f"💵 دلار آمریکا: {dollar if dollar else '🔄 در حال آپدیت'}\n"
            message += f"💳 تتر: {tether if tether else '🔄 در حال آپدیت'}\n"
            message += f"🥇 طلای 18 عیار: {gold if gold else '🔄 در حال آپدیت'}\n"
            message += f"🪙 سکه امامی: {coin if coin else '🔄 در حال آپدیت'}\n\n"
            
            # ارزهای دیجیتال
            message += "₿ ارزهای دیجیتال:\n"
            message += f"🟠 بیت‌کوین: {crypto_prices.get('بیت‌کوین', '🔄 در حال آپدیت')}\n"
            message += f"🔵 اتریوم: {crypto_prices.get('اتریوم', '🔄 در حال آپدیت')}\n\n"
            
            message += "🔄 آپدیت بعدی: 30 دقیقه دیگر\n"
            message += "📱 @asle_tehran"
            
            # لاگ نتایج
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
    
    logging.info("🤖 ربات منابع واقعی شروع شد")
    bot = RealPriceBot(TELEGRAM_BOT_TOKEN, CHAT_ID)
    bot.collect_and_send_prices()
    logging.info("✅ پایان")
    sys.exit(0)

if __name__ == "__main__":
    main()
