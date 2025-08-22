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

class PriceBot:
    def __init__(self, bot_token, chat_id):
        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id

    def get_crypto_prices(self):
        """کریپتو از Binance - همون قبلی که کار می‌کرد"""
        prices = {}
        
        try:
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', timeout=10)
            if response.status_code == 200:
                btc_price = float(response.json()['price'])
                prices['بیت‌کوین'] = f"${btc_price:,.0f}"
                logging.info(f"✓ BTC: ${btc_price:,.0f}")
        except Exception as e:
            logging.error(f"خطا BTC: {e}")
        
        try:
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT', timeout=10)
            if response.status_code == 200:
                eth_price = float(response.json()['price'])
                prices['اتریوم'] = f"${eth_price:,.0f}"
                logging.info(f"✓ ETH: ${eth_price:,.0f}")
        except Exception as e:
            logging.error(f"خطا ETH: {e}")
        
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

    def get_tether_price(self):
        """تتر از Nobitex - همون قبلی که کار می‌کرد"""
        try:
            logging.info("دریافت USDT از Nobitex...")
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

    def get_dollar_price(self):
        """دلار با روش ساده"""
        
        # روش 1: Bonbast JSON
        try:
            logging.info("دلار: Bonbast JSON...")
            response = requests.get('https://bonbast.com/json', timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and 'usd' in data:
                    usd_data = data['usd']
                    if isinstance(usd_data, dict) and 'sell' in usd_data:
                        sell_price = str(usd_data['sell']).replace(',', '').strip()
                        if sell_price.isdigit():
                            price = int(sell_price)
                            logging.info(f"✓ دلار از Bonbast JSON: {price:,}")
                            return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا Bonbast JSON: {e}")
        
        # روش 2: TGJU API
        try:
            logging.info("دلار: TGJU API...")
            response = requests.get('https://api.tgju.org/v1/data/sana/json', timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and 'price_dollar_rl' in data:
                    dollar_data = data['price_dollar_rl']
                    if isinstance(dollar_data, dict) and 'p' in dollar_data:
                        price_str = str(dollar_data['p']).replace(',', '').strip()
                        if price_str.isdigit():
                            price = int(price_str)
                            logging.info(f"✓ دلار از TGJU API: {price:,}")
                            return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا TGJU API: {e}")
        
        return None

    def get_gold_price(self):
        """طلا - همون قبلی که کار می‌کرد"""
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

    def get_coin_price(self):
        """سکه - همون قبلی که کار می‌کرد"""
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
        logging.info("🚀 ربات ساده...")
        
        try:
            # جمع‌آوری
            crypto_prices = self.get_crypto_prices()
            tether = self.get_tether_price()
            dollar = self.get_dollar_price()
            gold = self.get_gold_price()
            coin = self.get_coin_price()
            
            # ساخت پیام
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
            
            # لاگ
            all_prices = {
                'دلار آمریکا': dollar,
                'تتر': tether,
                'طلای 18 عیار': gold,
                'سکه امامی': coin,
                **crypto_prices
            }
            
            success_count = sum(1 for v in all_prices.values() if v is not None)
            logging.info(f"📊 نتیجه: {success_count}/6 قیمت")
            
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
    
    logging.info("🤖 ربات ساده شروع شد")
    bot = PriceBot(TELEGRAM_BOT_TOKEN, CHAT_ID)
    bot.collect_and_send_prices()
    logging.info("✅ پایان")
    sys.exit(0)

if __name__ == "__main__":
    main()
