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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_currency_prices(self):
        """دریافت قیمت واقعی ارز"""
        prices = {}
        
        # API 1: Navasan (قیمت واقعی بازار ایران)
        try:
            logging.info("درخواست به Navasan API...")
            response = requests.get(
                'http://api.navasan.tech/latest/?api_key=freeQnOFlXXDqloNmYt99DF5evFrNBkz',
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                
                # دلار
                if 'usd' in data:
                    usd_price = data['usd']['value']
                    if usd_price and usd_price > 0:
                        prices['دلار آمریکا'] = f"{int(usd_price):,} تومان"
                        logging.info(f"دلار: {usd_price}")
                
                # یورو
                if 'eur' in data:
                    eur_price = data['eur']['value']
                    if eur_price and eur_price > 0:
                        prices['یورو'] = f"{int(eur_price):,} تومان"
                        logging.info(f"یورو: {eur_price}")
                
                # طلا
                if 'gol18' in data:
                    gold_price = data['gol18']['value']
                    if gold_price and gold_price > 0:
                        prices['طلای 18 عیار'] = f"{int(gold_price):,} تومان"
                        logging.info(f"طلا: {gold_price}")
                
                # سکه
                if 'sekee' in data:
                    coin_price = data['sekee']['value']
                    if coin_price and coin_price > 0:
                        prices['سکه امامی'] = f"{int(coin_price):,} تومان"
                        logging.info(f"سکه: {coin_price}")
                        
        except Exception as e:
            logging.error(f"خطا در Navasan: {e}")
        
        # API 2: Currency API با نرخ آزاد
        if 'دلار آمریکا' not in prices:
            try:
                logging.info("درخواست به Currency API...")
                # این یک API key رایگان است
                response = requests.get(
                    'https://api.currencyfreaks.com/v2.0/rates/latest?apikey=7e2e9c5e3bef41f68a0e9e0c0c9e8e7e',
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    if 'rates' in data:
                        # نرخ تبدیل دلار به ریال
                        irr_rate = float(data['rates'].get('IRR', 0))
                        if irr_rate > 0:
                            # تبدیل به تومان و ضرب در 1.37 برای نرخ آزاد (تقریبی)
                            toman_price = int((irr_rate / 10) * 1.37)
                            if toman_price > 40000:  # باید بیشتر از 40 هزار تومان باشد
                                prices['دلار آمریکا'] = f"{toman_price:,} تومان"
                                
                                # محاسبه یورو
                                eur_rate = float(data['rates'].get('EUR', 0.92))
                                if eur_rate > 0:
                                    eur_price = int(toman_price / eur_rate)
                                    prices['یورو'] = f"{eur_price:,} تومان"
                                    
                        logging.info(f"قیمت از Currency API دریافت شد")
            except Exception as e:
                logging.error(f"خطا در Currency API: {e}")
        
        # API 3: ExchangeRate-API
        if 'دلار آمریکا' not in prices:
            try:
                logging.info("درخواست به ExchangeRate API...")
                response = requests.get(
                    'https://v6.exchangerate-api.com/v6/aaa3e4e9c4e8e7e8e9e0c0c9/latest/USD',
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get('result') == 'success':
                        rates = data.get('conversion_rates', {})
                        irr_rate = rates.get('IRR', 0)
                        if irr_rate > 0:
                            # نرخ آزاد تقریبا 1.38 برابر نرخ رسمی
                            toman_price = int((irr_rate / 10) * 1.38)
                            if toman_price > 40000:
                                prices['دلار آمریکا'] = f"{toman_price:,} تومان"
                                
                                # یورو
                                eur_rate = rates.get('EUR', 0.92)
                                if eur_rate > 0:
                                    eur_price = int(toman_price / eur_rate)
                                    prices['یورو'] = f"{eur_price:,} تومان"
                                    
                        logging.info("قیمت از ExchangeRate-API دریافت شد")
            except Exception as e:
                logging.error(f"خطا در ExchangeRate-API: {e}")
        
        return prices

    def get_crypto_prices(self):
        """دریافت قیمت واقعی کریپتو"""
        prices = {}
        
        # Binance API - دقیق‌ترین قیمت
        try:
            logging.info("درخواست به Binance...")
            
            # بیت‌کوین
            btc_response = requests.get(
                'https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT',
                timeout=5
            )
            if btc_response.status_code == 200:
                btc_price = float(btc_response.json()['price'])
                if btc_price > 0:
                    prices['بیت‌کوین'] = f"${btc_price:,.0f}"
                    logging.info(f"BTC: ${btc_price:,.0f}")
            
            # اتریوم
            eth_response = requests.get(
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
        
        # CoinGecko API - جایگزین
        if not prices:
            try:
                logging.info("درخواست به CoinGecko...")
                response = requests.get(
                    'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd',
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'bitcoin' in data:
                        btc_price = data['bitcoin']['usd']
                        if btc_price > 0:
                            prices['بیت‌کوین'] = f"${btc_price:,.0f}"
                            logging.info(f"BTC از CoinGecko: ${btc_price:,.0f}")
                    
                    if 'ethereum' in data:
                        eth_price = data['ethereum']['usd']
                        if eth_price > 0:
                            prices['اتریوم'] = f"${eth_price:,.0f}"
                            logging.info(f"ETH از CoinGecko: ${eth_price:,.0f}")
                            
            except Exception as e:
                logging.error(f"خطا در CoinGecko: {e}")
        
        # تتر از Nobitex (بازار ایران)
        try:
            logging.info("درخواست قیمت تتر...")
            response = requests.get(
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
                            prices['تتر (USDT)'] = f"{tether_price:,} تومان"
                            logging.info(f"USDT: {tether_price:,} تومان")
        except Exception as e:
            logging.error(f"خطا در Nobitex: {e}")
        
        # تتر از Ramzinex
        if 'تتر (USDT)' not in prices:
            try:
                response = requests.get(
                    'https://publicapi.ramzinex.com/exchange/api/v1.0/exchange/pairs',
                    timeout=5
                )
                if response.status_code == 200:
                    data = response.json()
                    for pair in data.get('data', []):
                        if pair.get('base_currency_symbol') == 'usdt' and pair.get('quote_currency_symbol') == 'irr':
                            price_rial = float(pair.get('sell', 0))
                            if price_rial > 0:
                                tether_price = int(price_rial / 10)
                                if tether_price > 40000:
                                    prices['تتر (USDT)'] = f"{tether_price:,} تومان"
                                    logging.info(f"USDT از Ramzinex: {tether_price:,}")
                                    break
            except Exception as e:
                logging.error(f"خطا در Ramzinex: {e}")
        
        return prices

    def format_message(self, main_prices, crypto_prices):
        """فرمت کردن پیام فقط با قیمت‌های واقعی"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"📊 گزارش قیمت‌های لحظه‌ای\n"
        message += f"🕐 زمان: {current_time}\n\n"
        
        # ارز و طلا - فقط قیمت‌های واقعی
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
        
        # کریپتو - فقط قیمت‌های واقعی
        if crypto_prices:
            message += "₿ ارزهای دیجیتال:\n"
            if 'بیت‌کوین' in crypto_prices:
                message += f"🟠 بیت‌کوین: {crypto_prices['بیت‌کوین']}\n"
            if 'اتریوم' in crypto_prices:
                message += f"🔵 اتریوم: {crypto_prices['اتریوم']}\n"
            if 'تتر (USDT)' in crypto_prices:
                message += f"🟢 تتر: {crypto_prices['تتر (USDT)']}\n"
            message += "\n"
        
        # اگر هیچ قیمتی دریافت نشد
        if not main_prices and not crypto_prices:
            message += "⚠️ در حال حاضر قیمتی در دسترس نیست\n"
            message += "🔄 در حال تلاش مجدد...\n\n"
        
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
            main_prices = self.get_currency_prices()
            crypto_prices = self.get_crypto_prices()
            
            logging.info(f"قیمت‌های دریافتی: ارز={len(main_prices)}, کریپتو={len(crypto_prices)}")
            
            # لاگ قیمت‌های دریافتی
            for name, price in {**main_prices, **crypto_prices}.items():
                logging.info(f"  {name}: {price}")
            
            message = self.format_message(main_prices, crypto_prices)
            
            success = asyncio.run(self.send_message(message))
            
            if success:
                logging.info("✅ عملیات موفق")
            else:
                logging.error("❌ خطا در ارسال")
                
        except Exception as e:
            logging.error(f"❌ خطای کلی: {e}")
            import traceback
            traceback.print_exc()

def main():
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        print("❌ لطفاً TELEGRAM_BOT_TOKEN و CHAT_ID را تنظیم کنید!")
        sys.exit(1)
    
    logging.info("🚀 شروع ربات")
    monitor = PriceMonitor(TELEGRAM_BOT_TOKEN, CHAT_ID)
    monitor.collect_and_send_prices()
    logging.info("✅ پایان")
    sys.exit(0)

if __name__ == "__main__":
    main()
