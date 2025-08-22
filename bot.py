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

class SimplePriceCollector:
    def __init__(self, bot_token, chat_id):
        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id

    def get_crypto_from_api(self):
        """دریافت کریپتو از API های ساده"""
        prices = {}
        
        # بیت‌کوین از Binance
        try:
            logging.info("API: درخواست BTC...")
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', timeout=8)
            if response.status_code == 200:
                btc_price = float(response.json()['price'])
                prices['بیت‌کوین'] = f"${btc_price:,.0f}"
                logging.info(f"✓ BTC: ${btc_price:,.0f}")
        except Exception as e:
            logging.error(f"خطا BTC: {e}")
        
        # اتریوم از Binance
        try:
            logging.info("API: درخواست ETH...")
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT', timeout=8)
            if response.status_code == 200:
                eth_price = float(response.json()['price'])
                prices['اتریوم'] = f"${eth_price:,.0f}"
                logging.info(f"✓ ETH: ${eth_price:,.0f}")
        except Exception as e:
            logging.error(f"خطا ETH: {e}")
        
        # اگر Binance کار نکرد، CoinGecko API
        if not prices:
            try:
                logging.info("API: درخواست از CoinGecko...")
                response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd', timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'bitcoin' in data:
                        prices['بیت‌کوین'] = f"${data['bitcoin']['usd']:,.0f}"
                    if 'ethereum' in data:
                        prices['اتریوم'] = f"${data['ethereum']['usd']:,.0f}"
                    logging.info("✓ کریپتو از CoinGecko")
            except Exception as e:
                logging.error(f"خطا CoinGecko: {e}")
        
        # تتر از Nobitex API
        try:
            logging.info("API: درخواست USDT...")
            response = requests.get('https://api.nobitex.ir/market/stats?srcCurrency=usdt&dstCurrency=rls', timeout=8)
            if response.status_code == 200:
                data = response.json()
                if 'stats' in data and 'usdt-rls' in data['stats']:
                    tether_rial = float(data['stats']['usdt-rls']['latest'])
                    tether_toman = int(tether_rial / 10)
                    prices['تتر'] = f"{tether_toman:,} تومان"
                    logging.info(f"✓ USDT: {tether_toman:,}")
        except Exception as e:
            logging.error(f"خطا USDT: {e}")
        
        return prices

    def get_prices_from_html(self):
        """دریافت قیمت‌ها از HTML با روش ساده"""
        prices = {}
        
        # دلار از Bonbast
        try:
            logging.info("HTML: درخواست دلار از Bonbast...")
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get('https://bonbast.com/', headers=headers, timeout=10)
            
            if response.status_code == 200:
                html = response.text
                logging.info(f"Bonbast HTML دریافت شد: {len(html)} کاراکتر")
                
                # جستجوی ساده برای دلار
                dollar_matches = re.findall(r'(\d{2},\d{3})', html)
                for match in dollar_matches:
                    price = int(match.replace(',', ''))
                    if 60000 <= price <= 120000:  # محدوده دلار
                        prices['دلار آمریکا'] = f"{price:,} تومان"
                        logging.info(f"✓ دلار: {price:,}")
                        break
        except Exception as e:
            logging.error(f"خطا Bonbast: {e}")
        
        # طلا از TGJU
        try:
            logging.info("HTML: درخواست طلا از TGJU...")
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get('https://www.tgju.org/', headers=headers, timeout=15)
            
            if response.status_code == 200:
                html = response.text
                logging.info(f"TGJU HTML دریافت شد: {len(html)} کاراکتر")
                
                # جستجوی طلا (7 رقمی)
                gold_matches = re.findall(r'(\d{1,2},\d{3},\d{3})', html)
                for match in gold_matches:
                    price = int(match.replace(',', ''))
                    if 2000000 <= price <= 6000000:  # محدوده طلا
                        prices['طلای 18 عیار'] = f"{price:,} تومان"
                        logging.info(f"✓ طلا: {price:,}")
                        break
                
                # جستجوی سکه (8 رقمی)
                coin_matches = re.findall(r'(\d{2,3},\d{3},\d{3})', html)
                for match in coin_matches:
                    price = int(match.replace(',', ''))
                    # اگر خیلی بزرگ است (ریال)، تبدیل به تومان
                    if price > 100000000:
                        price = price // 10
                    if 25000000 <= price <= 80000000:  # محدوده سکه
                        prices['سکه امامی'] = f"{price:,} تومان"
                        logging.info(f"✓ سکه: {price:,}")
                        break
        except Exception as e:
            logging.error(f"خطا TGJU: {e}")
        
        # اگر از TGJU نگرفتیم، از صفحات مستقیم
        if 'طلای 18 عیار' not in prices:
            try:
                logging.info("HTML: تلاش مجدد برای طلا...")
                response = requests.get('https://www.tgju.org/profile/geram18', headers=headers, timeout=10)
                if response.status_code == 200:
                    numbers = re.findall(r'(\d{1,2},\d{3},\d{3})', response.text)
                    for num in numbers:
                        price = int(num.replace(',', ''))
                        if 2000000 <= price <= 6000000:
                            prices['طلای 18 عیار'] = f"{price:,} تومان"
                            logging.info(f"✓ طلا از صفحه مستقیم: {price:,}")
                            break
            except:
                pass
        
        if 'سکه امامی' not in prices:
            try:
                logging.info("HTML: تلاش مجدد برای سکه...")
                response = requests.get('https://www.tgju.org/profile/sekee', headers=headers, timeout=10)
                if response.status_code == 200:
                    numbers = re.findall(r'(\d{2,3},\d{3},\d{3})', response.text)
                    for num in numbers:
                        price = int(num.replace(',', ''))
                        if price > 100000000:
                            price = price // 10
                        if 25000000 <= price <= 80000000:
                            prices['سکه امامی'] = f"{price:,} تومان"
                            logging.info(f"✓ سکه از صفحه مستقیم: {price:,}")
                            break
            except:
                pass
        
        return prices

    def collect_and_send_prices(self):
        """جمع‌آوری و ارسال"""
        logging.info("=" * 50)
        logging.info("🚀 شروع جمع‌آوری قیمت‌ها...")
        
        try:
            # API برای کریپتو و تتر
            api_prices = self.get_crypto_from_api()
            
            # HTML برای دلار، طلا، سکه
            html_prices = self.get_prices_from_html()
            
            # ترکیب نتایج
            all_prices = {**html_prices, **api_prices}
            
            # ساخت پیام
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            message = f"📊 قیمت‌های لحظه‌ای\n"
            message += f"🕐 آپدیت: {current_time}\n\n"
            
            # بازار ارز و طلا
            message += "💰 بازار ارز و طلا:\n"
            message += f"💵 دلار آمریکا: {all_prices.get('دلار آمریکا', '🔄 در حال آپدیت')}\n"
            message += f"💳 تتر: {all_prices.get('تتر', '🔄 در حال آپدیت')}\n"
            message += f"🥇 طلای 18 عیار: {all_prices.get('طلای 18 عیار', '🔄 در حال آپدیت')}\n"
            message += f"🪙 سکه امامی: {all_prices.get('سکه امامی', '🔄 در حال آپدیت')}\n\n"
            
            # ارزهای دیجیتال
            message += "₿ ارزهای دیجیتال:\n"
            message += f"🟠 بیت‌کوین: {all_prices.get('بیت‌کوین', '🔄 در حال آپدیت')}\n"
            message += f"🔵 اتریوم: {all_prices.get('اتریوم', '🔄 در حال آپدیت')}\n\n"
            
            message += "🔄 آپدیت بعدی: 30 دقیقه دیگر\n"
            message += "📱 @asle_tehran"
            
            # لاگ نتایج
            target_items = ['دلار آمریکا', 'تتر', 'طلای 18 عیار', 'سکه امامی', 'بیت‌کوین', 'اتریوم']
            success_count = sum(1 for item in target_items if item in all_prices)
            
            logging.info(f"📊 نتیجه: {success_count}/6 قیمت موفق")
            for item in target_items:
                status = "✓" if item in all_prices else "✗"
                price = all_prices.get(item, "ناموفق")
                logging.info(f"  {status} {item}: {price}")
            
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
    collector = SimplePriceCollector(TELEGRAM_BOT_TOKEN, CHAT_ID)
    collector.collect_and_send_prices()
    logging.info("✅ پایان")
    sys.exit(0)

if __name__ == "__main__":
    main()
