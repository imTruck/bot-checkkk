#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
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

class HTMLPriceScraper:
    def __init__(self, bot_token, chat_id):
        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fa,en-US;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache'
        })

    def scrape_tgju_html(self):
        """خواندن همه قیمت‌ها از HTML صفحه اصلی TGJU"""
        prices = {}
        try:
            logging.info("درخواست HTML از TGJU...")
            response = self.session.get('https://www.tgju.org/', timeout=15)
            
            if response.status_code == 200:
                html = response.text
                logging.info(f"✓ صفحه TGJU دریافت شد ({len(html)} کاراکتر)")
                
                # جستجوی قیمت‌ها با regex - بدون محدودیت
                patterns = {
                    'دلار آمریکا': [
                        r'price_dollar_rl.*?(\d{2,3},\d{3})',
                        r'دلار.*?(\d{2,3},\d{3})',
                        r'USD.*?(\d{2,3},\d{3})',
                        r'"p":"(\d+)".*?"title":".*?دلار'
                    ],
                    'طلای 18 عیار': [
                        r'geram18.*?(\d{1,2},\d{3},\d{3})',
                        r'طلای?\s*18.*?(\d{1,2},\d{3},\d{3})',
                        r'18\s*عیار.*?(\d{1,2},\d{3},\d{3})',
                        r'"p":"(\d+)".*?"title":".*?طلا'
                    ],
                    'سکه امامی': [
                        r'sekee.*?(\d{2,3},\d{3},\d{3})',
                        r'سکه.*?(\d{2,3},\d{3},\d{3})',
                        r'امامی.*?(\d{2,3},\d{3},\d{3})',
                        r'"p":"(\d+)".*?"title":".*?سکه'
                    ],
                    'تتر': [
                        r'crypto-usdt.*?(\d{2,3},\d{3})',
                        r'USDT.*?(\d{2,3},\d{3})',
                        r'تتر.*?(\d{2,3},\d{3})',
                        r'"p":"(\d+)".*?"title":".*?تتر'
                    ]
                }
                
                for item_name, pattern_list in patterns.items():
                    for pattern in pattern_list:
                        matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
                        if matches:
                            for match in matches:
                                price_str = match.replace(',', '')
                                if price_str.isdigit():
                                    price_val = int(price_str)
                                    
                                    # فقط چک کنیم که عدد خیلی کوچک نباشد
                                    if price_val > 1000:
                                        # اگر سکه خیلی بزرگ است (ریال)، تبدیل به تومان
                                        if item_name == 'سکه امامی' and price_val > 100000000:
                                            price_val = price_val // 10
                                        
                                        prices[item_name] = f"{price_val:,} تومان"
                                        logging.info(f"✓ {item_name}: {price_val:,}")
                                        break
                        if item_name in prices:
                            break
        except Exception as e:
            logging.error(f"خطا در TGJU: {e}")
        
        return prices

    def scrape_bonbast_html(self):
        """خواندن قیمت از HTML صفحه Bonbast"""
        prices = {}
        try:
            logging.info("درخواست HTML از Bonbast...")
            response = self.session.get('https://bonbast.com/', timeout=15)
            
            if response.status_code == 200:
                html = response.text
                logging.info(f"✓ صفحه Bonbast دریافت شد ({len(html)} کاراکتر)")
                
                # جستجوی قیمت‌ها با regex - بدون محدودیت
                patterns = [
                    r'USD.*?(\d{2,3},\d{3})',
                    r'"usd".*?"sell".*?"(\d+)"',
                    r'دلار.*?(\d{2,3},\d{3})',
                    r'>(\d{2,3},\d{3})<.*?USD'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    for match in matches:
                        price_str = match.replace(',', '')
                        if price_str.isdigit():
                            price_val = int(price_str)
                            if price_val > 10000:  # فقط چک کنیم خیلی کوچک نباشد
                                prices['دلار آمریکا'] = f"{price_val:,} تومان"
                                logging.info(f"✓ دلار از Bonbast: {price_val:,}")
                                break
                    if 'دلار آمریکا' in prices:
                        break
                
                # طلا
                gold_patterns = [
                    r'طلا.*?(\d{1,2},\d{3},\d{3})',
                    r'gol18.*?(\d+)',
                    r'18.*?(\d{1,2},\d{3},\d{3})'
                ]
                
                for pattern in gold_patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    for match in matches:
                        price_str = match.replace(',', '')
                        if price_str.isdigit():
                            price_val = int(price_str)
                            if price_val > 100000:  # فقط چک کنیم خیلی کوچک نباشد
                                prices['طلای 18 عیار'] = f"{price_val:,} تومان"
                                logging.info(f"✓ طلا از Bonbast: {price_val:,}")
                                break
                    if 'طلای 18 عیار' in prices:
                        break
                
                # سکه
                coin_patterns = [
                    r'سکه.*?(\d{2,3},\d{3},\d{3})',
                    r'sekee.*?(\d+)',
                    r'امامی.*?(\d{2,3},\d{3},\d{3})'
                ]
                
                for pattern in coin_patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    for match in matches:
                        price_str = match.replace(',', '')
                        if price_str.isdigit():
                            price_val = int(price_str)
                            if price_val > 1000000:  # فقط چک کنیم خیلی کوچک نباشد
                                # اگر خیلی بزرگ است، از ریال به تومان
                                if price_val > 100000000:
                                    price_val = price_val // 10
                                prices['سکه امامی'] = f"{price_val:,} تومان"
                                logging.info(f"✓ سکه از Bonbast: {price_val:,}")
                                break
                    if 'سکه امامی' in prices:
                        break
                        
        except Exception as e:
            logging.error(f"خطا در Bonbast: {e}")
        
        return prices

    def scrape_tether_html(self):
        """خواندن قیمت تتر از HTML صفحات مختلف"""
        tether_price = None
        
        # منابع مختلف برای تتر
        sources = [
            {
                'name': 'Nobitex',
                'url': 'https://nobitex.ir/',
                'patterns': [
                    r'USDT.*?(\d{2,3},\d{3})',
                    r'تتر.*?(\d{2,3},\d{3})',
                    r'(\d{2,3},\d{3}).*?تومان.*?USDT'
                ]
            },
            {
                'name': 'Wallex',
                'url': 'https://wallex.ir/',
                'patterns': [
                    r'USDT.*?(\d{2,3},\d{3})',
                    r'تتر.*?(\d{2,3},\d{3})',
                    r'(\d{2,3},\d{3}).*?USDT'
                ]
            },
            {
                'name': 'BitPin',
                'url': 'https://bitpin.ir/',
                'patterns': [
                    r'USDT.*?(\d{2,3},\d{3})',
                    r'تتر.*?(\d{2,3},\d{3})',
                    r'(\d{2,3},\d{3}).*?USDT'
                ]
            }
        ]
        
        for source in sources:
            try:
                logging.info(f"تلاش برای دریافت تتر از {source['name']}...")
                response = self.session.get(source['url'], timeout=10)
                
                if response.status_code == 200:
                    html = response.text
                    
                    for pattern in source['patterns']:
                        matches = re.findall(pattern, html, re.IGNORECASE)
                        for match in matches:
                            price_str = match.replace(',', '')
                            if price_str.isdigit():
                                price_val = int(price_str)
                                if price_val > 10000:  # بدون محدودیت سخت
                                    tether_price = f"{price_val:,} تومان"
                                    logging.info(f"✓ تتر از {source['name']}: {price_val:,}")
                                    return tether_price
            except Exception as e:
                logging.error(f"خطا در {source['name']}: {e}")
        
        return tether_price

    def scrape_crypto_html(self):
        """خواندن قیمت کریپتو از HTML"""
        prices = {}
        
        # CoinMarketCap
        try:
            logging.info("درخواست کریپتو از CoinMarketCap...")
            
            # صفحه بیت‌کوین
            response = self.session.get('https://coinmarketcap.com/currencies/bitcoin/', timeout=15)
            if response.status_code == 200:
                html = response.text
                
                # جستجوی قیمت بیت‌کوین - بدون محدودیت
                btc_patterns = [
                    r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                    r'price.*?\$(\d{1,3}(?:,\d{3})*)',
                    r'"priceUsd":"(\d+\.?\d*)"'
                ]
                
                for pattern in btc_patterns:
                    matches = re.findall(pattern, html)
                    for match in matches:
                        price_str = match.replace(',', '')
                        try:
                            price_val = float(price_str)
                            if price_val > 1000:  # فقط چک کنیم خیلی کوچک نباشد
                                prices['بیت‌کوین'] = f"${price_val:,.0f}"
                                logging.info(f"✓ BTC: ${price_val:,.0f}")
                                break
                        except:
                            continue
                    if 'بیت‌کوین' in prices:
                        break
            
            # صفحه اتریوم
            response = self.session.get('https://coinmarketcap.com/currencies/ethereum/', timeout=15)
            if response.status_code == 200:
                html = response.text
                
                for pattern in btc_patterns:
                    matches = re.findall(pattern, html)
                    for match in matches:
                        price_str = match.replace(',', '')
                        try:
                            price_val = float(price_str)
                            if price_val > 100:  # فقط چک کنیم خیلی کوچک نباشد
                                prices['اتریوم'] = f"${price_val:,.0f}"
                                logging.info(f"✓ ETH: ${price_val:,.0f}")
                                break
                        except:
                            continue
                    if 'اتریوم' in prices:
                        break
                        
        except Exception as e:
            logging.error(f"خطا در CoinMarketCap: {e}")
        
        # اگر CoinMarketCap کار نکرد، CoinGecko امتحان کن
        if not prices:
            try:
                logging.info("درخواست کریپتو از CoinGecko...")
                response = self.session.get('https://www.coingecko.com/', timeout=15)
                if response.status_code == 200:
                    html = response.text
                    
                    # جستجوی قیمت در HTML
                    btc_match = re.search(r'bitcoin.*?\$(\d{1,3}(?:,\d{3})*)', html, re.IGNORECASE)
                    if btc_match:
                        try:
                            price_val = float(btc_match.group(1).replace(',', ''))
                            if price_val > 1000:
                                prices['بیت‌کوین'] = f"${price_val:,.0f}"
                                logging.info(f"✓ BTC از CoinGecko: ${price_val:,.0f}")
                        except:
                            pass
                    
                    eth_match = re.search(r'ethereum.*?\$(\d{1,5})', html, re.IGNORECASE)
                    if eth_match:
                        try:
                            price_val = float(eth_match.group(1).replace(',', ''))
                            if price_val > 100:
                                prices['اتریوم'] = f"${price_val:,.0f}"
                                logging.info(f"✓ ETH از CoinGecko: ${price_val:,.0f}")
                        except:
                            pass
            except Exception as e:
                logging.error(f"خطا در CoinGecko: {e}")
        
        return prices

    def collect_all_prices_html(self):
        """جمع‌آوری همه قیمت‌ها فقط از HTML"""
        all_prices = {}
        
        # TGJU HTML (همه چیز)
        tgju_prices = self.scrape_tgju_html()
        all_prices.update(tgju_prices)
        logging.info(f"TGJU HTML: {len(tgju_prices)} قیمت - {list(tgju_prices.keys())}")
        
        # Bonbast HTML (اگر چیزی از TGJU نگرفتیم)
        missing_items = ['دلار آمریکا', 'طلای 18 عیار', 'سکه امامی']
        if any(item not in all_prices for item in missing_items):
            bonbast_prices = self.scrape_bonbast_html()
            for key, value in bonbast_prices.items():
                if key not in all_prices:
                    all_prices[key] = value
            logging.info(f"Bonbast HTML: {len(bonbast_prices)} قیمت جدید")
        
        # تتر از صفحات تبادل
        if 'تتر' not in all_prices:
            tether = self.scrape_tether_html()
            if tether:
                all_prices['تتر'] = tether
        
        # کریپتو
        crypto_prices = self.scrape_crypto_html()
        
        return all_prices, crypto_prices

    def collect_and_send_prices(self):
        """جمع‌آوری و ارسال قیمت‌ها"""
        logging.info("=" * 70)
        logging.info("🌐 شروع HTML Scraping بدون محدودیت...")
        
        try:
            main_prices, crypto_prices = self.collect_all_prices_html()
            
            # فرمت پیام
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            message = f"📊 قیمت‌های لحظه‌ای\n"
            message += f"🕐 آپدیت: {current_time}\n\n"
            
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
            logging.info(f"📊 مجموع: {total} قیمت")
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
    
    logging.info("🌐 HTML Scraper بدون محدودیت شروع شد")
    scraper = HTMLPriceScraper(TELEGRAM_BOT_TOKEN, CHAT_ID)
    scraper.collect_and_send_prices()
    logging.info("✅ پایان")
    sys.exit(0)

if __name__ == "__main__":
    main()
