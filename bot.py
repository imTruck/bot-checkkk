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
import socket
import ssl

# تنظیمات
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# تنظیم لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class NetworkTester:
    def __init__(self, bot_token, chat_id):
        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id

    def test_basic_connectivity(self):
        """تست اتصال پایه"""
        results = {}
        
        # تست DNS
        try:
            socket.gethostbyname('google.com')
            results['DNS'] = "✅ کار می‌کند"
        except Exception as e:
            results['DNS'] = f"❌ خطا: {e}"
        
        # تست اتصال HTTP ساده
        try:
            response = requests.get('http://httpbin.org/status/200', timeout=5)
            results['HTTP'] = f"✅ کد: {response.status_code}"
        except Exception as e:
            results['HTTP'] = f"❌ خطا: {e}"
        
        # تست اتصال HTTPS
        try:
            response = requests.get('https://httpbin.org/status/200', timeout=5)
            results['HTTPS'] = f"✅ کد: {response.status_code}"
        except Exception as e:
            results['HTTPS'] = f"❌ خطا: {e}"
        
        return results

    def test_specific_sites(self):
        """تست سایت‌های خاص"""
        sites = {
            'TGJU Main': 'https://www.tgju.org/',
            'TGJU API': 'https://api.tgju.org/v1/data/sana/json',
            'Bonbast': 'https://bonbast.com/',
            'Binance': 'https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT',
            'Nobitex': 'https://api.nobitex.ir/market/stats?srcCurrency=usdt&dstCurrency=rls',
            'CoinGecko': 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd',
            'Google': 'https://www.google.com',
            'GitHub': 'https://api.github.com'
        }
        
        results = {}
        for name, url in sites.items():
            try:
                response = requests.get(url, timeout=10)
                results[name] = f"✅ {response.status_code} ({len(response.content)} bytes)"
                logging.info(f"{name}: {response.status_code}")
            except requests.exceptions.Timeout:
                results[name] = "⏰ Timeout"
            except requests.exceptions.ConnectionError as e:
                results[name] = f"🔌 Connection Error: {str(e)[:50]}..."
            except requests.exceptions.SSLError as e:
                results[name] = f"🔒 SSL Error: {str(e)[:50]}..."
            except Exception as e:
                results[name] = f"❌ {type(e).__name__}: {str(e)[:50]}..."
        
        return results

    def test_with_different_headers(self):
        """تست با headers مختلف"""
        headers_list = [
            {
                'name': 'Chrome Desktop',
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
            },
            {
                'name': 'Firefox',
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
                }
            },
            {
                'name': 'Curl',
                'headers': {
                    'User-Agent': 'curl/7.68.0'
                }
            },
            {
                'name': 'Python Requests',
                'headers': {
                    'User-Agent': 'python-requests/2.31.0'
                }
            }
        ]
        
        results = {}
        test_url = 'https://www.tgju.org/'
        
        for header_set in headers_list:
            try:
                response = requests.get(test_url, headers=header_set['headers'], timeout=10)
                results[header_set['name']] = f"✅ {response.status_code}"
            except Exception as e:
                results[header_set['name']] = f"❌ {type(e).__name__}"
        
        return results

    def get_working_prices(self):
        """دریافت قیمت از منابع کار کرده"""
        prices = {}
        
        # منابع مختلف برای تست
        sources = [
            {
                'name': 'ExchangeRate-API',
                'url': 'https://open.er-api.com/v6/latest/USD',
                'parser': self.parse_exchangerate
            },
            {
                'name': 'Fixer.io (free)',
                'url': 'https://api.fixer.io/latest?access_key=freekey&base=USD',
                'parser': self.parse_fixer
            },
            {
                'name': 'JSONVat (EU)',
                'url': 'https://jsonvat.com/',
                'parser': self.parse_jsonvat
            },
            {
                'name': 'CryptoCompare',
                'url': 'https://min-api.cryptocompare.com/data/price?fsym=BTC&tsyms=USD',
                'parser': self.parse_cryptocompare
            }
        ]
        
        for source in sources:
            try:
                response = requests.get(source['url'], timeout=10)
                if response.status_code == 200:
                    result = source['parser'](response)
                    if result:
                        prices[source['name']] = result
                        logging.info(f"✅ {source['name']}: {result}")
            except Exception as e:
                logging.error(f"❌ {source['name']}: {e}")
        
        return prices

    def parse_exchangerate(self, response):
        try:
            data = response.json()
            if data.get('result') == 'success':
                irr = data['rates'].get('IRR', 0)
                if irr > 0:
                    return f"USD/IRR رسمی: {int(irr):,} ریال"
        except:
            pass
        return None

    def parse_fixer(self, response):
        try:
            data = response.json()
            if data.get('success'):
                return "Fixer API جواب داد"
        except:
            pass
        return None

    def parse_jsonvat(self, response):
        if response.status_code == 200:
            return "JSONVat دسترسی دارد"
        return None

    def parse_cryptocompare(self, response):
        try:
            data = response.json()
            if 'USD' in data:
                btc = data['USD']
                return f"BTC: ${btc:,.0f}"
        except:
            pass
        return None

    def collect_and_send_diagnostic(self):
        """جمع‌آوری و ارسال گزارش تشخیصی"""
        logging.info("=" * 70)
        logging.info("🔍 شروع تشخیص مشکل...")
        
        try:
            # تست‌های مختلف
            basic = self.test_basic_connectivity()
            sites = self.test_specific_sites()
            headers = self.test_with_different_headers()
            working_prices = self.get_working_prices()
            
            # ساخت گزارش
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            message = f"🔍 گزارش تشخیص مشکل\n"
            message += f"🕐 زمان: {current_time}\n\n"
            
            # اتصال پایه
            message += "🌐 تست اتصال پایه:\n"
            for test, result in basic.items():
                message += f"  {test}: {result}\n"
            message += "\n"
            
            # سایت‌های خاص
            message += "🌍 تست سایت‌های خاص:\n"
            for site, result in sites.items():
                message += f"  {site}: {result}\n"
            message += "\n"
            
            # تست headers
            message += "📋 تست Headers برای TGJU:\n"
            for header, result in headers.items():
                message += f"  {header}: {result}\n"
            message += "\n"
            
            # منابع کار کرده
            if working_prices:
                message += "✅ منابع کار کرده:\n"
                for source, price in working_prices.items():
                    message += f"  {source}: {price}\n"
                message += "\n"
            else:
                message += "❌ هیچ منبع قیمتی کار نکرد\n\n"
            
            # نتیجه‌گیری
            if any('✅' in result for result in sites.values()):
                message += "🔧 راه‌حل: استفاده از منابع در دسترس\n"
            else:
                message += "🚨 مشکل: دسترسی شبکه محدود است\n"
            
            message += "\n📱 @asle_tehran"
            
            # ارسال
            success = asyncio.run(self.send_message(message))
            
            if success:
                logging.info("✅ گزارش ارسال شد")
            else:
                logging.error("❌ خطا در ارسال گزارش")
                
        except Exception as e:
            logging.error(f"❌ خطا در تشخیص: {e}")
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
    
    logging.info("🔍 شروع تشخیص مشکل")
    tester = NetworkTester(TELEGRAM_BOT_TOKEN, CHAT_ID)
    tester.collect_and_send_diagnostic()
    logging.info("✅ پایان تشخیص")
    sys.exit(0)

if __name__ == "__main__":
    main()
