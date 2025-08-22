#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import logging
import os
from datetime import datetime
import asyncio
from telegram import Bot
import re
import sys
import json

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
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'en-US,en;q=0.9,fa;q=0.8'
        })

    def get_currency_from_bonbast(self):
        """دریافت قیمت ارز از Bonbast API"""
        prices = {}
        try:
            logging.info("درخواست به Bonbast API...")
            
            # Bonbast unofficial API
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
            
            # گرفتن توکن
            token_response = self.session.get('https://bonbast.com/json', headers=headers, timeout=10)
            if token_response.status_code == 200:
                try:
                    data = token_response.json()
                    
                    # دلار
                    if 'usd' in data:
                        usd_sell = data['usd'].get('sell', '').replace(',', '')
                        if usd_sell and usd_sell.isdigit():
                            prices['دلار آمریکا'] = f"{int(usd_sell):,} تومان"
                            logging.info(f"دلار از Bonbast: {usd_sell}")
                    
                    # یورو
                    if 'eur' in data:
                        eur_sell = data['eur'].get('sell', '').replace(',', '')
                        if eur_sell and eur_sell.isdigit():
                            prices['یورو'] = f"{int(eur_sell):,} تومان"
                            logging.info(f"یورو از Bonbast: {eur_sell}")
                            
                except json.JSONDecodeError:
                    # اگر JSON نبود، HTML را پارس کن
                    html = token_response.text
                    
                    # دلار
                    usd_match = re.search(r'USD.*?(\d{2},?\d{3})', html)
                    if usd_match:
                        usd_price = int(usd_match.group(1).replace(',', ''))
                        prices['دلار آمریکا'] = f"{usd_price:,} تومان"
                        logging.info(f"دلار از HTML: {usd_price}")
                    
                    # یورو
                    eur_match = re.search(r'EUR.*?(\d{2},?\d{3})', html)
                    if eur_match:
                        eur_price = int(eur_match.group(1).replace(',', ''))
                        prices['یورو'] = f"{eur_price:,} تومان"
                        logging.info(f"یورو از HTML: {eur_price}")
                        
        except Exception as e:
            logging.error(f"خطا در Bonbast: {e}")
        
        return prices

    def get_gold_from_tgju_api(self):
        """دریافت قیمت طلا و سکه از TGJU"""
        prices = {}
        try:
            logging.info("درخواست به TGJU API...")
            
            # API endpoint های مختلف TGJU
            endpoints = [
                'https://api.tgju.org/v1/data/sana/json',
                'https://cdn.tgju.org/api/v1/data/sana/json',
                'https://api.tgju.org/v1/data/live'
            ]
            
            for endpoint in endpoints:
                try:
                    response = self.session.get(endpoint, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        
                        # پارس کردن داده‌ها بسته به فرمت
                        if isinstance(data, dict):
                            # طلا
                            if 'geram18' in data:
                                gold_price = data['geram18'].get('p', '').replace(',', '')
                                if gold_price and gold_price.isdigit():
                                    prices['طلای 18 عیار'] = f"{int(gold_price):,} تومان"
                                    logging.info(f"طلا: {gold_price}")
                            
                            # سکه
                            if 'sekee' in data:
                                coin_price = data['sekee'].get('p', '').replace(',', '')
                                if coin_price and coin_price.isdigit():
                                    # سکه معمولا به ریال است، تبدیل به تومان
                                    coin_toman = int(coin_price) // 10 if int(coin_price) > 1000000 else int(coin_price)
                                    prices['سکه امامی'] = f"{coin_toman:,} تومان"
                                    logging.info(f"سکه: {coin_toman}")
                        
                        if prices:
                            break
                            
                except Exception as e:
                    logging.error(f"خطا در endpoint {endpoint}: {e}")
                    continue
                    
        except Exception as e:
            logging.error(f"خطا در TGJU: {e}")
        
        return prices

    def get_currency_and_gold_prices(self):
        """دریافت همه قیمت‌های ارز و طلا"""
        all_prices = {}
        
        # ارز از Bonbast
        currency_prices = self.get_currency_from_bonbast()
        all_prices.update(currency_prices)
        
        # اگر Bonbast کار نکرد، از منبع دیگر
        if 'دلار آمریکا' not in all_prices:
            try:
                logging.info("تلاش برای دریافت از منابع جایگزین...")
                
                # سعی کن از API ساده‌تر
                response = self.session.get(
                    'https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json',
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    if 'usd' in data:
                        irr_rate = data['usd'].get('irr', 0)
                        if irr_rate > 0:
                            # نرخ آزاد حدود 1.4 برابر نرخ رسمی
                            toman_price = int((irr_rate / 10) * 1.4)
                            if toman_price > 40000:
                                all_prices['دلار آمریکا'] = f"{toman_price:,} تومان"
                                
                                # محاسبه یورو (حدود 1.09 برابر دلار)
                                eur_price = int(toman_price * 1.09)
                                all_prices['یورو'] = f"{eur_price:,} تومان"
                                logging.info("قیمت ارز از منبع جایگزین")
            except Exception as e:
                logging.error(f"خطا در منبع جایگزین: {e}")
        
        # طلا و سکه از TGJU
        gold_prices = self.get_gold_from_tgju_api()
        all_prices.update(gold_prices)
        
        # اگر طلا و سکه نگرفتیم، از محاسبه استفاده کن
        if 'طلای 18 عیار' not in all_prices and 'دلار آمریکا' in all_prices:
            try:
                # قیمت جهانی طلا
                response = self.session.get(
                    'https://api.metals.live/v1/spot/gold',
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    gold_usd_per_oz = float(data[0]['price'])  # قیمت هر اونس به دلار
                    
                    # تبدیل به گرم و ضرب در نرخ دلار
                    gold_usd_per_gram = gold_usd_per_oz / 31.1035
                    dollar_price = int(all_prices['دلار آمریکا'].replace(',', '').replace(' تومان', ''))
                    
                    # طلای 18 عیار = 75% طلای خالص + حق ساخت
                    gold_18_price = int(gold_usd_per_gram * dollar_price * 0.75 * 1.15)
                    all_prices['طلای 18 عیار'] = f"{gold_18_price:,} تومان"
                    
                    # سکه حدود 8.13 گرم طلا + حق ضرب
                    coin_price = int(gold_18_price * 8.13 * 1.3)
                    all_prices['سکه امامی'] = f"{coin_price:,} تومان"
                    logging.info("قیمت طلا و سکه محاسبه شد")
            except Exception as e:
                logging.error(f"خطا در محاسبه طلا: {e}")
        
        return all_prices

    def get_tether_price(self):
        """دریافت قیمت تتر"""
        # Nobitex
        try:
            response = self.session.get(
                'https://api.nobitex.ir/market/stats?srcCurrency=usdt&dstCurrency=rls',
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if 'stats' in data and 'usdt-rls' in data['stats']:
                    price_rial = float(data['stats']['usdt-rls']['latest'])
                    if price_rial > 0:
                        tether_price = int(price_rial / 10)
                        if tether_price > 40000:
                            logging.info(f"تتر از Nobitex: {tether_price}")
                            return f"{tether_price:,} تومان"
        except Exception as e:
            logging.error(f"خطا در Nobitex: {e}")
        
        # Wallex
        try:
            response = self.session.get(
                'https://api.wallex.ir/v1/markets',
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                markets = data.get('result', {}).get('symbols', {})
                if 'USDTTMN' in markets:
                    tether_price = int(float(markets['USDTTMN']['stats']['bidPrice']))
                    if tether_price > 40000:
                        logging.info(f"تتر از Wallex: {tether_price}")
                        return f"{tether_price:,} تومان"
        except Exception as e:
            logging.error(f"خطا در Wallex: {e}")
        
        # BitPin
        try:
            response = self.session.get(
                'https://api.bitpin.ir/v1/mkt/markets/',
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                for market in data.get('results', []):
                    if market.get('currency1', {}).get('code') == 'USDT' and \
                       market.get('currency2', {}).get('code') == 'IRT':
                        tether_price = int(float(market.get('price', 0)))
                        if tether_price > 40000:
                            logging.info(f"تتر از BitPin: {tether_price}")
                            return f"{tether_price:,} تومان"
        except Exception as e:
            logging.error(f"خطا در BitPin: {e}")
        
        return None

    def get_crypto_prices(self):
        """دریافت قیمت کریپتو"""
        prices = {}
        
        # Binance API
        try:
            # بیت‌کوین
            btc_response = self.session.get(
                'https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT',
                timeout=5
            )
            if btc_response.status_code == 200:
                btc_price = float(btc_response.json()['price'])
                if btc_price > 0:
                    prices['بیت‌کوین'] = f"${btc_price:,.0f}"
                    logging.info(f"BTC: ${btc_price:,.0f}")
            
            # اتریوم
            eth_response = self.session.get(
                'https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT',
                timeout=5
            )
            if eth_response.status_code == 200:
                eth_price = float(eth_response.json()['price'])
                if eth_price > 0:
                    prices['اتریوم'] = f"${eth_price:,.0f}"
                    logging.info(f"ETH: ${eth_price:,.0f}")
                    
        except Exception as e:
            logging.error(f"خطا در Binance: {e}")
        
        # قیمت تتر
        tether_price = self.get_tether_price()
        if tether_price:
            prices['تتر (USDT)'] = tether_price
        
        return prices

    def format_message(self, main_prices, crypto_prices):
        """فرمت کردن پیام"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"📊 گزارش قیمت‌های لحظه‌ای\n"
        message += f"🕐 زمان: {current_time}\n\n"
        
        # ارز و طلا
        if main_prices:
            message += "💰 بازار ارز و طلا:\n"
            if 'دلار آمریکا' in main_prices:
                message += f"💵 دلار آمریکا: {main_prices['دلار آمریکا']}\n"
            if 'یورو' in main_prices:
                message += f"💶 یورو: {main_prices['یورو']}\n"
            if 'طلای 18 عیار' in main_prices:
                message += f"🥇 طلای 18 عیار: {main_prices['طلای 18 عیار']}\n"
            if 'سکه امامی' in main_prices:
                message += f"🪙 سکه امامی: {main_prices['سکه امامی']}\n"
            message += "\n"
        
        # کریپتو
        if crypto_prices:
            message += "₿ ارزهای دیجیتال:\n"
            if 'بیت‌کوین' in crypto_prices:
                message += f"🟠 بیت‌کوین: {crypto_prices['بیت‌کوین']}\n"
            if 'اتریوم' in crypto_prices:
                message += f"🔵 اتریوم: {crypto_prices['اتریوم']}\n"
            if 'تتر (USDT)' in crypto_prices:
                message += f"🟢 تتر: {crypto_prices['تتر (USDT)']}\n"
            message += "\n"
        
        message += "🔄 آپدیت بعدی: 30 دقیقه دیگر\n"
        message += "📱 @asle_tehran"
        
        return message

    async def send_message(self, message):
        """ارسال پیام به تلگرام"""
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message)
            logging.info("✅ پیام ارسال شد")
            return True
        except Exception as e:
            logging.error(f"❌ خطا در ارسال: {e}")
            return False

    def collect_and_send_prices(self):
        """جمع‌آوری و ارسال قیمت‌ها"""
        logging.info("=" * 50)
        logging.info("شروع جمع‌آوری قیمت‌ها...")
        
        try:
            main_prices = self.get_currency_and_gold_prices()
            crypto_prices = self.get_crypto_prices()
            
            logging.info(f"قیمت‌های دریافتی: ارز={len(main_prices)}, کریپتو={len(crypto_prices)}")
            
            # نمایش قیمت‌ها در لاگ
            all_prices = {**main_prices, **crypto_prices}
            for name, price in all_prices.items():
                logging.info(f"  ✓ {name}: {price}")
            
            message = self.format_message(main_prices, crypto_prices)
            
            success = asyncio.run(self.send_message(message))
            
            if success:
                logging.info("✅ پیام با موفقیت ارسال شد")
            else:
                logging.error("❌ خطا در ارسال پیام")
                
        except Exception as e:
            logging.error(f"❌ خطای کلی: {e}")
            import traceback
            traceback.print_exc()

def main():
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        print("❌ لطفاً TELEGRAM_BOT_TOKEN و CHAT_ID را تنظیم کنید!")
        sys.exit(1)
    
    logging.info("🚀 شروع ربات قیمت")
    monitor = PriceMonitor(TELEGRAM_BOT_TOKEN, CHAT_ID)
    monitor.collect_and_send_prices()
    logging.info("✅ اجرا کامل شد")
    sys.exit(0)

if __name__ == "__main__":
    main()
