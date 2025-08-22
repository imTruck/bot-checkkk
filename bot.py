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

class PriceCollector:
    def __init__(self, bot_token, chat_id):
        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id

    def get_crypto_from_api(self):
        """دریافت کریپتو از API - بدون تغییر"""
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
        
        return prices

    def get_dollar_enhanced(self):
        """دریافت دلار با روش‌های بهبود یافته"""
        
        # روش 1: Bonbast با JSON
        try:
            logging.info("دلار: تست Bonbast JSON...")
            response = requests.get('https://bonbast.com/json', timeout=10)
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'usd' in data and 'sell' in data['usd']:
                        dollar_price = int(data['usd']['sell'].replace(',', ''))
                        if 60000 <= dollar_price <= 120000:
                            logging.info(f"✓ دلار از Bonbast JSON: {dollar_price:,}")
                            return f"{dollar_price:,} تومان"
                except:
                    pass
        except Exception as e:
            logging.error(f"خطا Bonbast JSON: {e}")
        
        # روش 2: Bonbast HTML با regex بهتر
        try:
            logging.info("دلار: تست Bonbast HTML...")
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get('https://bonbast.com/', headers=headers, timeout=10)
            if response.status_code == 200:
                html = response.text
                
                # الگوهای مختلف برای دلار
                patterns = [
                    r'"usd":\s*{[^}]*"sell":\s*"?(\d+)"?',
                    r'USD[^>]*>.*?(\d{2},\d{3})',
                    r'دلار.*?(\d{2},\d{3})',
                    r'(\d{2},\d{3})\s*</td>\s*</tr>\s*</tbody>\s*</table>'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
                    for match in matches:
                        price_str = match.replace(',', '')
                        if price_str.isdigit():
                            dollar_price = int(price_str)
                            if 60000 <= dollar_price <= 120000:
                                logging.info(f"✓ دلار از Bonbast HTML: {dollar_price:,}")
                                return f"{dollar_price:,} تومان"
        except Exception as e:
            logging.error(f"خطا Bonbast HTML: {e}")
        
        # روش 3: TGJU مستقیم
        try:
            logging.info("دلار: تست TGJU...")
            response = requests.get('https://www.tgju.org/profile/price_dollar_rl', headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            if response.status_code == 200:
                html = response.text
                
                # جستجو در صفحه دلار
                patterns = [
                    r'قیمت\s*فعلی.*?(\d{2},\d{3})',
                    r'نرخ\s*روز.*?(\d{2},\d{3})',
                    r'(\d{2},\d{3})\s*تومان',
                    r'>(\d{2},\d{3})<'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    for match in matches:
                        price_str = match.replace(',', '')
                        if price_str.isdigit():
                            dollar_price = int(price_str)
                            if 60000 <= dollar_price <= 120000:
                                logging.info(f"✓ دلار از TGJU: {dollar_price:,}")
                                return f"{dollar_price:,} تومان"
        except Exception as e:
            logging.error(f"خطا TGJU دلار: {e}")
        
        # روش 4: محاسبه از تتر (اگر تتر موجود باشد)
        try:
            logging.info("دلار: محاسبه از تتر...")
            tether_response = requests.get('https://api.nobitex.ir/market/stats?srcCurrency=usdt&dstCurrency=rls', timeout=5)
            if tether_response.status_code == 200:
                data = tether_response.json()
                if 'stats' in data and 'usdt-rls' in data['stats']:
                    tether_rial = float(data['stats']['usdt-rls']['latest'])
                    tether_toman = int(tether_rial / 10)
                    # دلار معمولا 2-3% کمتر از تتر
                    dollar_price = int(tether_toman * 0.97)
                    if 60000 <= dollar_price <= 120000:
                        logging.info(f"✓ دلار از تتر: {dollar_price:,}")
                        return f"{dollar_price:,} تومان"
        except Exception as e:
            logging.error(f"خطا محاسبه دلار: {e}")
        
        return None

    def get_tether_enhanced(self):
        """دریافت تتر با روش‌های بهبود یافته"""
        
        # روش 1: Nobitex API
        try:
            logging.info("تتر: تست Nobitex API...")
            response = requests.get('https://api.nobitex.ir/market/stats?srcCurrency=usdt&dstCurrency=rls', timeout=8)
            if response.status_code == 200:
                data = response.json()
                if 'stats' in data and 'usdt-rls' in data['stats']:
                    tether_rial = float(data['stats']['usdt-rls']['latest'])
                    tether_toman = int(tether_rial / 10)
                    if 60000 <= tether_toman <= 120000:
                        logging.info(f"✓ تتر از Nobitex: {tether_toman:,}")
                        return f"{tether_toman:,} تومان"
        except Exception as e:
            logging.error(f"خطا Nobitex: {e}")
        
        # روش 2: Wallex API (اگر دسترسی داشتیم)
        try:
            logging.info("تتر: تست Wallex...")
            response = requests.get('https://api.wallex.ir/v1/markets', timeout=8)
            if response.status_code == 200:
                data = response.json()
                if 'result' in data and 'symbols' in data['result']:
                    symbols = data['result']['symbols']
                    if 'USDTTMN' in symbols:
                        tether_price = int(float(symbols['USDTTMN']['stats']['bidPrice']))
                        if 60000 <= tether_price <= 120000:
                            logging.info(f"✓ تتر از Wallex: {tether_price:,}")
                            return f"{tether_price:,} تومان"
        except Exception as e:
            logging.error(f"خطا Wallex: {e}")
        
        # روش 3: BitPin API
        try:
            logging.info("تتر: تست BitPin...")
            response = requests.get('https://api.bitpin.ir/v1/mkt/markets/', timeout=8)
            if response.status_code == 200:
                data = response.json()
                for market in data.get('results', []):
                    if (market.get('currency1', {}).get('code') == 'USDT' and 
                        market.get('currency2', {}).get('code') == 'IRT'):
                        tether_price = int(float(market.get('price', 0)))
                        if 60000 <= tether_price <= 120000:
                            logging.info(f"✓ تتر از BitPin: {tether_price:,}")
                            return f"{tether_price:,} تومان"
        except Exception as e:
            logging.error(f"خطا BitPin: {e}")
        
        # روش 4: Ramzinex API
        try:
            logging.info("تتر: تست Ramzinex...")
            response = requests.get('https://publicapi.ramzinex.com/exchange/api/v1.0/exchange/pairs', timeout=8)
            if response.status_code == 200:
                data = response.json()
                for pair in data.get('data', []):
                    if (pair.get('base_currency_symbol') == 'usdt' and 
                        pair.get('quote_currency_symbol') == 'irr'):
                        tether_rial = float(pair.get('sell', 0))
                        tether_toman = int(tether_rial / 10)
                        if 60000 <= tether_toman <= 120000:
                            logging.info(f"✓ تتر از Ramzinex: {tether_toman:,}")
                            return f"{tether_toman:,} تومان"
        except Exception as e:
            logging.error(f"خطا Ramzinex: {e}")
        
        return None

    def get_gold_coin_from_html(self):
        """دریافت طلا و سکه - بدون تغییر"""
        prices = {}
        
        try:
            logging.info("HTML: درخواست طلا و سکه از TGJU...")
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get('https://www.tgju.org/', headers=headers, timeout=15)
            
            if response.status_code == 200:
                html = response.text
                
                # جستجوی طلا (7 رقمی)
                gold_matches = re.findall(r'(\d{1,2},\d{3},\d{3})', html)
                for match in gold_matches:
                    price = int(match.replace(',', ''))
                    if 2000000 <= price <= 6000000:
                        prices['طلای 18 عیار'] = f"{price:,} تومان"
                        logging.info(f"✓ طلا: {price:,}")
                        break
                
                # جستجوی سکه (8 رقمی)
                coin_matches = re.findall(r'(\d{2,3},\d{3},\d{3})', html)
                for match in coin_matches:
                    price = int(match.replace(',', ''))
                    if price > 100000000:
                        price = price // 10
                    if 25000000 <= price <= 80000000:
                        prices['سکه امامی'] = f"{price:,} تومان"
                        logging.info(f"✓ سکه: {price:,}")
                        break
        except Exception as e:
            logging.error(f"خطا TGJU: {e}")
        
        return prices

    def collect_and_send_prices(self):
        """جمع‌آوری و ارسال"""
        logging.info("=" * 50)
        logging.info("🚀 شروع جمع‌آوری قیمت‌ها...")
        
        try:
            # کریپتو (بدون تغییر)
            crypto_prices = self.get_crypto_from_api()
            
            # دلار و تتر (بهبود یافته)
            dollar = self.get_dollar_enhanced()
            tether = self.get_tether_enhanced()
            
            # طلا و سکه (بدون تغییر)
            gold_coin_prices = self.get_gold_coin_from_html()
            
            # ترکیب همه
            all_prices = {}
            if dollar:
                all_prices['دلار آمریکا'] = dollar
            if tether:
                all_prices['تتر'] = tether
            all_prices.update(gold_coin_prices)
            all_prices.update(crypto_prices)
            
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
    
    logging.info("🤖 ربات بهبود یافته شروع شد")
    collector = PriceCollector(TELEGRAM_BOT_TOKEN, CHAT_ID)
    collector.collect_and_send_prices()
    logging.info("✅ پایان")
    sys.exit(0)

if __name__ == "__main__":
    main()
