#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import time
import logging
import os
from datetime import datetime
import asyncio
from telegram import Bot
from telegram.error import TelegramError
import json
import re
import sys

# تنظیمات - از Environment Variables می‌خواند
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/html',
            'Accept-Language': 'fa-IR,fa;q=0.9,en;q=0.8',
            'Referer': 'https://www.tgju.org/'
        })

    def get_tgju_prices_api(self):
        """دریافت قیمت از API مستقیم TGJU"""
        prices = {}
        
        api_endpoints = [
            'https://api.tgju.org/v1/market/indicator/summary-table-data/',
            'https://call6.tgju.org/ajax.json',
        ]
        
        for api_url in api_endpoints:
            try:
                response = self.session.get(api_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    
                    if isinstance(data, dict):
                        current = data.get('current', {})
                        if 'usd' in current:
                            usd_price = int(current['usd'].get('p', 0))
                            prices['دلار آمریکا'] = f"{usd_price // 10:,} تومان"
                        if 'eur' in current:
                            eur_price = int(current['eur'].get('p', 0))
                            prices['یورو'] = f"{eur_price // 10:,} تومان"
                        if 'gold' in current:
                            gold_price = int(current['gold'].get('p', 0))
                            prices['طلای 18 عیار'] = f"{gold_price // 10:,} تومان"
                        if 'sekee' in current:
                            coin_price = int(current['sekee'].get('p', 0))
                            prices['سکه امامی'] = f"{coin_price // 10:,} تومان"
                    
                    if prices:
                        logging.info(f"API موفق: {len(prices)} قیمت")
                        return prices
            except Exception as e:
                logging.error(f"خطا در API: {e}")
        
        return prices

    def get_fallback_prices(self):
        """منابع جایگزین برای قیمت‌ها"""
        prices = {}
        
        # bonbast.com
        try:
            response = self.session.get('https://bonbast.com/', timeout=10)
            if response.status_code == 200:
                content = response.text
                
                usd_match = re.search(r'"usd":\s*{\s*"sell":\s*(\d+)', content)
                if usd_match:
                    prices['دلار آمریکا'] = f"{int(usd_match.group(1)) // 10:,} تومان"
                
                eur_match = re.search(r'"eur":\s*{\s*"sell":\s*(\d+)', content)
                if eur_match:
                    prices['یورو'] = f"{int(eur_match.group(1)) // 10:,} تومان"
                    
                logging.info(f"قیمت از bonbast: {len(prices)} آیتم")
        except Exception as e:
            logging.error(f"خطا در bonbast: {e}")
        
        return prices

    def get_currency_and_gold_prices(self):
        """دریافت قیمت ارز و طلا"""
        prices = self.get_tgju_prices_api()
        
        if not prices:
            prices = self.get_fallback_prices()
        
        if not prices:
            prices = {
                'دلار آمریکا': "🔄 در حال آپدیت",
                'یورو': "🔄 در حال آپدیت",
                'طلای 18 عیار': "🔄 در حال آپدیت",
                'سکه امامی': "🔄 در حال آپدیت"
            }
        
        return prices

    def get_crypto_prices(self):
        """دریافت قیمت کریپتو"""
        prices = {}
        
        # Binance API
        try:
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', timeout=5)
            if response.status_code == 200:
                btc_price = float(response.json()['price'])
                prices['بیت‌کوین'] = f"${btc_price:,.0f}"
        except:
            pass
        
        try:
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT', timeout=5)
            if response.status_code == 200:
                eth_price = float(response.json()['price'])
                prices['اتریوم'] = f"${eth_price:,.0f}"
        except:
            pass
        
        # Nobitex API برای تتر
        try:
            response = requests.get('https://api.nobitex.ir/market/stats?srcCurrency=usdt&dstCurrency=rls', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'stats' in data and 'usdt-rls' in data['stats']:
                    tether_price = int(float(data['stats']['usdt-rls']['latest']) / 10)
                    if tether_price > 40000:
                        prices['تتر (USDT)'] = f"{tether_price:,} تومان"
        except:
            pass
        
        if 'بیت‌کوین' not in prices:
            prices['بیت‌کوین'] = "🔄 در حال آپدیت"
        if 'اتریوم' not in prices:
            prices['اتریوم'] = "🔄 در حال آپدیت"
        if 'تتر (USDT)' not in prices:
            prices['تتر (USDT)'] = "🔄 در حال آپدیت"
        
        return prices

    def format_message(self, main_prices, crypto_prices):
        """فرمت کردن پیام"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"📊 گزارش قیمت‌های لحظه‌ای\n"
        message += f"🕐 آپدیت: {current_time}\n\n"
        
        # ارز و طلا
        if main_prices:
            message += "💰 بازار ارز و طلا:\n"
            for item, price in main_prices.items():
                if 'دلار' in item:
                    message += f"💵 {item}: {price}\n"
                elif 'یورو' in item:
                    message += f"💶 {item}: {price}\n"
                elif 'طلا' in item:
                    message += f"🥇 {item}: {price}\n"
                elif 'سکه' in item:
                    message += f"🪙 {item}: {price}\n"
            message += "\n"
        
        # کریپتو
        if crypto_prices:
            message += "₿ ارزهای دیجیتال:\n"
            for crypto, price in crypto_prices.items():
                if 'بیت‌کوین' in crypto:
                    message += f"🟠 {crypto}: {price}\n"
                elif 'اتریوم' in crypto:
                    message += f"🔵 {crypto}: {price}\n"
                elif 'تتر' in crypto:
                    message += f"🟢 {crypto}: {price}\n"
            message += "\n"
        
        message += "🔄 آپدیت بعدی: 30 دقیقه دیگر\n"
        message += "📱 @asle_tehran"
        
        return message

    async def send_message(self, message):
        """ارسال پیام به تلگرام"""
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message)
            logging.info("پیام ارسال شد")
            return True
        except Exception as e:
            logging.error(f"خطا در تلگرام: {e}")
            return False

    def collect_and_send_prices(self):
        """جمع‌آوری و ارسال قیمت‌ها"""
        logging.info("شروع جمع‌آوری قیمت‌ها...")
        
        try:
            main_prices = self.get_currency_and_gold_prices()
            crypto_prices = self.get_crypto_prices()
            
            logging.info(f"قیمت‌ها: اصلی={len(main_prices)}, کریپتو={len(crypto_prices)}")
            
            message = self.format_message(main_prices, crypto_prices)
            
            success = asyncio.run(self.send_message(message))
            
            if success:
                logging.info("✅ آپدیت موفق")
            else:
                logging.error("❌ خطا در ارسال")
                
        except Exception as e:
            logging.error(f"خطای کلی: {e}")

def main():
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        print("❌ لطفاً TELEGRAM_BOT_TOKEN و CHAT_ID را در Secrets تنظیم کنید!")
        sys.exit(1)
    
    monitor = PriceMonitor(TELEGRAM_BOT_TOKEN, CHAT_ID)
    monitor.collect_and_send_prices()
    logging.info("اجرا کامل شد")
    sys.exit(0)

if __name__ == "__main__":
    main()
