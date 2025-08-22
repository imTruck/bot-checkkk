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

    def get_dollar_price(self):
        """دریافت قیمت دلار آزاد از تتر"""
        try:
            # قیمت تتر از نوبیتکس
            response = requests.get(
                'https://api.nobitex.ir/market/stats?srcCurrency=usdt&dstCurrency=rls',
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if 'stats' in data and 'usdt-rls' in data['stats']:
                    usdt = int(float(data['stats']['usdt-rls']['latest']) / 10)
                    # دلار معمولا 2% کمتر از تتر
                    dollar = int(usdt * 0.98)
                    logging.info(f"دلار محاسبه شده از تتر: {dollar:,}")
                    return f"{dollar:,} تومان"
        except Exception as e:
            logging.error(f"خطا در محاسبه دلار: {e}")
        return None

    def get_tether_price(self):
        """دریافت قیمت تتر"""
        # نوبیتکس
        try:
            response = requests.get(
                'https://api.nobitex.ir/market/stats?srcCurrency=usdt&dstCurrency=rls',
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if 'stats' in data and 'usdt-rls' in data['stats']:
                    usdt = int(float(data['stats']['usdt-rls']['latest']) / 10)
                    logging.info(f"Nobitex USDT: {usdt:,}")
                    return f"{usdt:,} تومان"
        except:
            pass
        
        # والکس
        try:
            response = requests.get('https://api.wallex.ir/v1/markets', timeout=5)
            if response.status_code == 200:
                data = response.json()
                markets = data.get('result', {}).get('symbols', {})
                if 'USDTTMN' in markets:
                    usdt = int(float(markets['USDTTMN']['stats']['bidPrice']))
                    if usdt > 40000:
                        logging.info(f"Wallex USDT: {usdt:,}")
                        return f"{usdt:,} تومان"
        except:
            pass
        
        return None

    def get_gold_price(self):
        """دریافت قیمت طلای 18 عیار"""
        try:
            # API طلای ایران (اگر کار کند)
            response = requests.get(
                'https://api.tgju.org/v1/data/sana/json',
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if 'geram18' in data:
                    gold_price = data['geram18'].get('p', '').replace(',', '')
                    if gold_price and gold_price.isdigit():
                        gold_toman = int(gold_price)
                        logging.info(f"طلا از TGJU: {gold_toman:,}")
                        return f"{gold_toman:,} تومان"
        except:
            pass
        
        # محاسبه از قیمت جهانی
        try:
            response = requests.get('https://api.metals.live/v1/spot/gold', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data:
                    gold_usd_oz = float(data[0]['price'])
                    gold_usd_gram = gold_usd_oz / 31.1035
                    
                    # گرفتن قیمت تتر برای تبدیل
                    tether = self.get_tether_price()
                    if tether:
                        tether_price = int(tether.replace(',', '').replace(' تومان', ''))
                        # طلای 18 عیار = 75% خلوص + 20% سود
                        gold_18 = int(gold_usd_gram * tether_price * 0.75 * 1.20)
                        logging.info(f"طلا محاسبه شده: {gold_18:,}")
                        return f"{gold_18:,} تومان"
        except:
            pass
        
        return None

    def get_coin_price(self):
        """دریافت قیمت سکه امامی"""
        try:
            # API سکه (اگر کار کند)
            response = requests.get(
                'https://api.tgju.org/v1/data/sana/json',
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if 'sekee' in data:
                    coin_price = data['sekee'].get('p', '').replace(',', '')
                    if coin_price and coin_price.isdigit():
                        # اگر به ریال است تبدیل به تومان
                        coin_toman = int(coin_price) // 10 if int(coin_price) > 100000000 else int(coin_price)
                        logging.info(f"سکه از TGJU: {coin_toman:,}")
                        return f"{coin_toman:,} تومان"
        except:
            pass
        
        # محاسبه از طلا (8.133 گرم + 40% حباب)
        gold = self.get_gold_price()
        if gold:
            try:
                gold_price = int(gold.replace(',', '').replace(' تومان', ''))
                coin_price = int(gold_price * 8.133 * 1.40)
                logging.info(f"سکه محاسبه شده: {coin_price:,}")
                return f"{coin_price:,} تومان"
            except:
                pass
        
        return None

    def get_crypto_prices(self):
        """دریافت قیمت بیت‌کوین و اتریوم به دلار"""
        prices = {}
        
        # Binance
        try:
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', timeout=5)
            if response.status_code == 200:
                btc = float(response.json()['price'])
                prices['بیت‌کوین'] = f"${btc:,.0f}"
                logging.info(f"BTC: ${btc:,.0f}")
            
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT', timeout=5)
            if response.status_code == 200:
                eth = float(response.json()['price'])
                prices['اتریوم'] = f"${eth:,.0f}"
                logging.info(f"ETH: ${eth:,.0f}")
        except:
            pass
        
        # CoinGecko (backup)
        if not prices:
            try:
                response = requests.get(
                    'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd',
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    if 'bitcoin' in data:
                        prices['بیت‌کوین'] = f"${data['bitcoin']['usd']:,.0f}"
                    if 'ethereum' in data:
                        prices['اتریوم'] = f"${data['ethereum']['usd']:,.0f}"
            except:
                pass
        
        return prices

    def collect_and_send_prices(self):
        """جمع‌آوری و ارسال قیمت‌ها"""
        logging.info("=" * 60)
        logging.info("🚀 شروع جمع‌آوری قیمت‌ها...")
        
        try:
            # جمع‌آوری قیمت‌ها
            main_prices = {}
            
            # تتر (اول برای محاسبات)
            tether = self.get_tether_price()
            if tether:
                main_prices['تتر'] = tether
            
            # دلار
            dollar = self.get_dollar_price()
            if dollar:
                main_prices['دلار آمریکا'] = dollar
            
            # طلا
            gold = self.get_gold_price()
            if gold:
                main_prices['طلای 18 عیار'] = gold
            
            # سکه
            coin = self.get_coin_price()
            if coin:
                main_prices['سکه امامی'] = coin
            
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
            logging.info(f"📊 تعداد قیمت‌ها: {total}")
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
