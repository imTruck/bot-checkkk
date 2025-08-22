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
        """خواندن قیمت از HTML صفحه اصلی TGJU"""
        prices = {}
        try:
            logging.info("درخواست HTML از TGJU...")
            response = self.session.get('https://www.tgju.org/', timeout=15)
            
            if response.status_code == 200:
                html = response.text
                logging.info(f"✓ صفحه TGJU دریافت شد ({len(html)} کاراکتر)")
                
                # جستجوی قیمت‌ها با regex
                patterns = {
                    'دلار آمریکا': [
                        r'price_dollar_rl.*?(\d{2},\d{3})',
                        r'دلار.*?(\d{2},\d{3})',
                        r'>(\d{2},\d{3})<.*?دلار',
                        r'USD.*?(\d{2},\d{3})'
                    ],
                    'طلای 18 عیار': [
                        r'geram18.*?(\d{1,2},\d{3},\d{3})',
                        r'طلای 18.*?(\d{1,2},\d{3},\d{3})',
                        r'18 عیار.*?(\d{1,2},\d{3},\d{3})',
                        r'>(\d{1,2},\d{3},\d{3})<.*?طلا'
                    ],
                    'سکه امامی': [
                        r'sekee.*?(\d{2,3},\d{3},\d{3})',
                        r'سکه.*?(\d{2,3},\d{3},\d{3})',
                        r'امامی.*?(\d{2,3},\d{3},\d{3})',
                        r'>(\d{2,3},\d{3},\d{3})<.*?سکه'
                    ],
                    'تتر': [
                        r'crypto-usdt.*?(\d{2,3},\d{3})',
                        r'USDT.*?(\d{2,3},\d{3})',
                        r'تتر.*?(\d{2,3},\d{3})',
                        r'>(\d{2,3},\d{3})<.*?تتر'
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
                                    
                                    # بررسی منطقی بودن قیمت
                                    if item_name == 'دلار آمریکا' and 50000 <= price_val <= 150000:
                                        prices[item_name] = f"{price_val:,} تومان"
                                        logging.info(f"✓ {item_name}: {price_val:,}")
                                        break
                                    elif item_name == 'طلای 18 عیار' and 2000000 <= price_val <= 5000000:
                                        prices[item_name] = f"{price_val:,} تومان"
                                        logging.info(f"✓ {item_name}: {price_val:,}")
                                        break
                                    elif item_name == 'سکه امامی' and 30000000 <= price_val <= 80000000:
                                        prices[item_name] = f"{price_val:,} تومان"
                                        logging.info(f"✓ {item_name}: {price_val:,}")
                                        break
                                    elif item_name == 'تتر' and 70000 <= price_val <= 120000:
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
                
                # پارس کردن HTML
                soup = BeautifulSoup(html, 'html.parser')
                
                # جستجوی جدول قیمت‌ها
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 3:
                            currency = cells[0].text.strip()
                            
                            # دلار
                            if 'USD' in currency or 'دلار' in currency:
                                try:
                                    sell_price = cells[2].text.strip().replace(',', '')
                                    if sell_price.isdigit():
                                        price_val = int(sell_price)
                                        if 50000 <= price_val <= 150000:
                                            prices['دلار آمریکا'] = f"{price_val:,} تومان"
                                            logging.info(f"✓ دلار از جدول: {price_val:,}")
                                except:
                                    pass
                            
                            # طلا
                            elif 'طلا' in currency or 'Gold' in currency or '18' in currency:
                                try:
                                    price = cells[1].text.strip().replace(',', '')
                                    if price.isdigit():
                                        price_val = int(price)
                                        if 2000000 <= price_val <= 5000000:
                                            prices['طلای 18 عیار'] = f"{price_val:,} تومان"
                                            logging.info(f"✓ طلا از جدول: {price_val:,}")
                                except:
                                    pass
                
                # اگر جدول کار نکرد، regex استفاده کن
                if not prices:
                    patterns = [
                        r'USD.*?(\d{2},\d{3})',
                        r'"usd".*?"sell".*?"(\d+)"',
                        r'دلار.*?(\d{2},\d{3})'
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, html, re.IGNORECASE)
                        if match:
                            price_str = match.group(1).replace(',', '')
                            if price_str.isdigit():
                                price_val = int(price_str)
                                if 50000 <= price_val <= 150000:
                                    prices['دلار آمریکا'] = f"{price_val:,} تومان"
                                    logging.info(f"✓ دلار از regex: {price_val:,}")
                                    break
        except Exception as e:
            logging.error(f"خطا در Bonbast: {e}")
        
        return prices

    def scrape_coinmarketcap_html(self):
        """خواندن قیمت کریپتو از HTML صفحه CoinMarketCap"""
        prices = {}
        try:
            logging.info("درخواست HTML از CoinMarketCap...")
            
            # صفحه بیت‌کوین
            response = self.session.get('https://coinmarketcap.com/currencies/bitcoin/', timeout=15)
            if response.status_code == 200:
                html = response.text
                
                # جستجوی قیمت بیت‌کوین
                btc_patterns = [
                    r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                    r'price.*?\$(\d{1,3}(?:,\d{3})*)',
                    r'"price".*?(\d+\.?\d*)'
                ]
                
                for pattern in btc_patterns:
                    matches = re.findall(pattern, html)
                    for match in matches:
                        price_str = match.replace(',', '')
                        try:
                            price_val = float(price_str)
                            if 50000 <= price_val <= 200000:  # محدوده منطقی برای BTC
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
                
                # جستجوی قیمت اتریوم
                for pattern in btc_patterns:
                    matches = re.findall(pattern, html)
                    for match in matches:
                        price_str = match.replace(',', '')
                        try:
                            price_val = float(price_str)
                            if 1000 <= price_val <= 10000:  # محدوده منطقی برای ETH
                                prices['اتریوم'] = f"${price_val:,.0f}"
                                logging.info(f"✓ ETH: ${price_val:,.0f}")
                                break
                        except:
                            continue
                    if 'اتریوم' in prices:
                        break
                        
        except Exception as e:
            logging.error(f"خطا در CoinMarketCap: {e}")
        
        return prices

    def scrape_coingecko_html(self):
        """خواندن قیمت کریپتو از HTML صفحه CoinGecko"""
        prices = {}
        try:
            logging.info("درخواست HTML از CoinGecko...")
            
            # صفحه اصلی CoinGecko
            response = self.session.get('https://www.coingecko.com/', timeout=15)
            if response.status_code == 200:
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                
                # جستجوی جدول قیمت‌ها
                rows = soup.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 3:
                        name_cell = cells[1] if len(cells) > 1 else cells[0]
                        price_cell = cells[2] if len(cells) > 2 else None
                        
                        if name_cell and price_cell:
                            name = name_cell.text.strip().lower()
                            price_text = price_cell.text.strip()
                            
                            # بیت‌کوین
                            if 'bitcoin' in name or 'btc' in name:
                                match = re.search(r'\$(\d{1,3}(?:,\d{3})*)', price_text)
                                if match:
                                    try:
                                        price_val = float(match.group(1).replace(',', ''))
                                        if 50000 <= price_val <= 200000:
                                            prices['بیت‌کوین'] = f"${price_val:,.0f}"
                                            logging.info(f"✓ BTC از جدول: ${price_val:,.0f}")
                                    except:
                                        pass
                            
                            # اتریوم
                            elif 'ethereum' in name or 'eth' in name:
                                match = re.search(r'\$(\d{1,5}(?:,\d{3})*)', price_text)
                                if match:
                                    try:
                                        price_val = float(match.group(1).replace(',', ''))
                                        if 1000 <= price_val <= 10000:
                                            prices['اتریوم'] = f"${price_val:,.0f}"
                                            logging.info(f"✓ ETH از جدول: ${price_val:,.0f}")
                                    except:
                                        pass
        except Exception as e:
            logging.error(f"خطا در CoinGecko: {e}")
        
        return prices

    def collect_all_prices_html(self):
        """جمع‌آوری همه قیمت‌ها فقط از HTML"""
        all_prices = {}
        
        # TGJU HTML
        tgju_prices = self.scrape_tgju_html()
        all_prices.update(tgju_prices)
        logging.info(f"TGJU HTML: {len(tgju_prices)} قیمت")
        
        # Bonbast HTML (فقط اگر دلار نگرفتیم)
        if 'دلار آمریکا' not in all_prices:
            bonbast_prices = self.scrape_bonbast_html()
            all_prices.update(bonbast_prices)
            logging.info(f"Bonbast HTML: {len(bonbast_prices)} قیمت")
        
        # کریپتو از CoinMarketCap
        crypto_prices = self.scrape_coinmarketcap_html()
        
        # اگر CoinMarketCap کار نکرد، CoinGecko امتحان کن
        if not crypto_prices:
            crypto_prices = self.scrape_coingecko_html()
        
        logging.info(f"Crypto HTML: {len(crypto_prices)} قیمت")
        
        return all_prices, crypto_prices

    def collect_and_send_prices(self):
        """جمع‌آوری و ارسال قیمت‌ها"""
        logging.info("=" * 70)
        logging.info("🌐 شروع HTML Scraping...")
        
        try:
            main_prices, crypto_prices = self.collect_all_prices_html()
            
            # فرمت پیام
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            message = f"📊 قیمت‌ها از HTML سایت‌ها\n"
            message += f"🕐 زمان: {current_time}\n\n"
            
            # قیمت‌های اصلی
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
            
            # کریپتو
            if crypto_prices:
                message += "₿ ارزهای دیجیتال:\n"
                if 'بیت‌کوین' in crypto_prices:
                    message += f"🟠 بیت‌کوین: {crypto_prices['بیت‌کوین']}\n"
                if 'اتریوم' in crypto_prices:
                    message += f"🔵 اتریوم: {crypto_prices['اتریوم']}\n"
                message += "\n"
            
            # خلاصه
            total = len(main_prices) + len(crypto_prices)
            message += f"📈 مجموع: {total} قیمت (فقط از HTML)\n\n"
            
            if total == 0:
                message += "❌ هیچ قیمتی از HTML دریافت نشد\n\n"
            elif total < 6:
                message += "⚠️ برخی قیمت‌ها دریافت نشد\n\n"
            else:
                message += "✅ همه قیمت‌ها دریافت شد\n\n"
            
            message += "🔄 آپدیت بعدی: 30 دقیقه دیگر\n"
            message += "📱 @asle_tehran"
            
            # لاگ
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
    
    logging.info("🌐 HTML Scraper شروع شد")
    scraper = HTMLPriceScraper(TELEGRAM_BOT_TOKEN, CHAT_ID)
    scraper.collect_and_send_prices()
    logging.info("✅ پایان")
    sys.exit(0)

if __name__ == "__main__":
    main()
