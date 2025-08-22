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
        """کریپتو فقط از API - بدون تغییر"""
        prices = {}
        
        try:
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', timeout=10)
            if response.status_code == 200:
                btc_price = float(response.json()['price'])
                prices['بیت‌کوین'] = f"${btc_price:,.0f}"
                logging.info(f"✓ BTC: ${btc_price:,.0f}")
        except Exception as e:
            logging.error(f"خطا Binance BTC: {e}")
        
        try:
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT', timeout=10)
            if response.status_code == 200:
                eth_price = float(response.json()['price'])
                prices['اتریوم'] = f"${eth_price:,.0f}"
                logging.info(f"✓ ETH: ${eth_price:,.0f}")
        except Exception as e:
            logging.error(f"خطا Binance ETH: {e}")
        
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

    def get_tether_from_api(self):
        """تتر فقط از API - بدون تغییر"""
        try:
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
        
        try:
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

    def get_dollar_enhanced(self):
        """دلار بهبود یافته از Bonbast و TGJU"""
        
        # روش 1: Bonbast جدید با regex دقیق‌تر
        try:
            logging.info("دلار: Bonbast صفحه اصلی...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'fa,en;q=0.5'
            }
            response = requests.get('https://bonbast.com/', headers=headers, timeout=15)
            if response.status_code == 200:
                html = response.text
                logging.info(f"Bonbast HTML length: {len(html)}")
                
                # الگوهای مختلف برای دلار
                patterns = [
                    # JSON در HTML
                    r'"usd":\s*{\s*"sell":\s*"?(\d+)"?',
                    # جدول HTML
                    r'<tr[^>]*>\s*<td[^>]*>USD</td>\s*<td[^>]*>[^<]*</td>\s*<td[^>]*>(\d{2},\d{3})</td>',
                    # متن ساده
                    r'USD.*?فروش.*?(\d{2},\d{3})',
                    r'دلار.*?(\d{2},\d{3})',
                    # هر عدد 5 رقمی که ممکن است دلار باشد
                    r'(\d{2},\d{3})'
                ]
                
                found_prices = []
                for pattern in patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
                    for match in matches:
                        price_str = match.replace(',', '')
                        if price_str.isdigit():
                            price = int(price_str)
                            if price > 80000:  # بیشتر از 80 هزار (تقریبا قیمت معقول امروز)
                                found_prices.append(price)
                
                if found_prices:
                    # بالاترین قیمت (معمولا قیمت فروش)
                    dollar_price = max(found_prices)
                    logging.info(f"✓ دلار از Bonbast: {dollar_price:,} (از {len(found_prices)} قیمت)")
                    return f"{dollar_price:,} تومان"
                    
        except Exception as e:
            logging.error(f"خطا Bonbast: {e}")
        
        # روش 2: TGJU صفحه اصلی
        try:
            logging.info("دلار: TGJU صفحه اصلی...")
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get('https://www.tgju.org/', headers=headers, timeout=15)
            if response.status_code == 200:
                html = response.text
                logging.info(f"TGJU HTML length: {len(html)}")
                
                # جستجوی دلار در صفحه اصلی
                patterns = [
                    r'price_dollar_rl.*?(\d{2},\d{3})',
                    r'دلار.*?(\d{2},\d{3})',
                    r'USD.*?(\d{2},\d{3})',
                    r'(\d{2},\d{3})'
                ]
                
                found_prices = []
                for pattern in patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    for match in matches:
                        price_str = match.replace(',', '')
                        if price_str.isdigit():
                            price = int(price_str)
                            if price > 80000:
                                found_prices.append(price)
                
                if found_prices:
                    dollar_price = max(found_prices)
                    logging.info(f"✓ دلار از TGJU: {dollar_price:,}")
                    return f"{dollar_price:,} تومان"
                    
        except Exception as e:
            logging.error(f"خطا TGJU: {e}")
        
        # روش 3: TGJU صفحه مستقیم دلار
        try:
            logging.info("دلار: TGJU صفحه مستقیم...")
            response = requests.get('https://www.tgju.org/profile/price_dollar_rl', 
                                  headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            if response.status_code == 200:
                html = response.text
                
                # جستجوی دقیق‌تر در صفحه مستقیم
                patterns = [
                    r'data-last-price="(\d+)"',
                    r'"p":"(\d+)"',
                    r'قیمت.*?(\d{2},\d{3})',
                    r'نرخ.*?(\d{2},\d{3})',
                    r'(\d{2},\d{3})'
                ]
                
                found_prices = []
                for pattern in patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    for match in matches:
                        price_str = match.replace(',', '')
                        if price_str.isdigit():
                            price = int(price_str)
                            if price > 80000:
                                found_prices.append(price)
                
                if found_prices:
                    dollar_price = max(found_prices)
                    logging.info(f"✓ دلار از TGJU مستقیم: {dollar_price:,}")
                    return f"{dollar_price:,} تومان"
                    
        except Exception as e:
            logging.error(f"خطا TGJU مستقیم: {e}")
        
        # روش 4: Bonbast JSON مستقیم
        try:
            logging.info("دلار: Bonbast JSON...")
            response = requests.get('https://bonbast.com/json', timeout=10)
            if response.status_code == 200:
                data = response.json()
                logging.info(f"Bonbast JSON keys: {list(data.keys()) if isinstance(data, dict) else 'not dict'}")
                
                if 'usd' in data:
                    usd_data = data['usd']
                    sell_price = usd_data.get('sell', '')
                    buy_price = usd_data.get('buy', '')
                    
                    # چک کردن قیمت فروش
                    if sell_price:
                        price_str = str(sell_price).replace(',', '')
                        if price_str.isdigit():
                            price = int(price_str)
                            if price > 80000:
                                logging.info(f"✓ دلار از Bonbast JSON: {price:,}")
                                return f"{price:,} تومان"
                    
                    # چک کردن قیمت خرید
                    if buy_price:
                        price_str = str(buy_price).replace(',', '')
                        if price_str.isdigit():
                            price = int(price_str)
                            if price > 80000:
                                logging.info(f"✓ دلار از Bonbast JSON (buy): {price:,}")
                                return f"{price:,} تومان"
                                
        except Exception as e:
            logging.error(f"خطا Bonbast JSON: {e}")
        
        return None

    def get_gold_from_sources(self):
        """طلا - بدون تغییر"""
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

    def get_coin_from_sources(self):
        """سکه - بدون تغییر"""
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
        logging.info("🚀 دریافت قیمت‌های واقعی...")
        
        try:
            crypto_prices = self.get_crypto_from_api()
            tether = self.get_tether_from_api()
            dollar = self.get_dollar_enhanced()  # ← تغییر اینجا
            gold = self.get_gold_from_sources()
            coin = self.get_coin_from_sources()
            
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
    
    logging.info("🤖 ربات با دلار بهبود یافته شروع شد")
    bot = RealPriceBot(TELEGRAM_BOT_TOKEN, CHAT_ID)
    bot.collect_and_send_prices()
    logging.info("✅ پایان")
    sys.exit(0)

if __name__ == "__main__":
    main()
