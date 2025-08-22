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

class AccuratePriceScraper:
    def __init__(self, bot_token, chat_id):
        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fa,en;q=0.9',
            'Cache-Control': 'no-cache'
        })

    def get_dollar_from_multiple_sources(self):
        """دریافت قیمت دلار از چندین منبع"""
        dollar_price = None
        
        # منبع 1: صفحه مستقیم دلار TGJU
        try:
            logging.info("گرفتن دلار از صفحه مستقیم TGJU...")
            response = self.session.get('https://www.tgju.org/profile/price_dollar_rl', timeout=15)
            if response.status_code == 200:
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                
                # جستجوی قیمت در عناصر HTML
                price_elements = soup.find_all(['span', 'div', 'td'], class_=re.compile(r'price|nf|value'))
                for elem in price_elements:
                    text = elem.get_text().strip()
                    match = re.search(r'(\d{2},\d{3})', text)
                    if match:
                        price_str = match.group(1).replace(',', '')
                        if price_str.isdigit():
                            price_val = int(price_str)
                            if 50000 <= price_val <= 120000:  # محدوده منطقی
                                dollar_price = f"{price_val:,} تومان"
                                logging.info(f"✓ دلار از TGJU: {price_val:,}")
                                return dollar_price
        except Exception as e:
            logging.error(f"خطا در TGJU دلار: {e}")
        
        # منبع 2: Arzdigital
        try:
            logging.info("گرفتن دلار از Arzdigital...")
            response = self.session.get('https://arzdigital.com/coins/us-dollar-price/', timeout=10)
            if response.status_code == 200:
                html = response.text
                match = re.search(r'(\d{2},\d{3})\s*تومان', html)
                if match:
                    price_str = match.group(1).replace(',', '')
                    if price_str.isdigit():
                        price_val = int(price_str)
                        if 50000 <= price_val <= 120000:
                            dollar_price = f"{price_val:,} تومان"
                            logging.info(f"✓ دلار از Arzdigital: {price_val:,}")
                            return dollar_price
        except Exception as e:
            logging.error(f"خطا در Arzdigital: {e}")
        
        # منبع 3: Sarrafionline
        try:
            logging.info("گرفتن دلار از Sarrafionline...")
            response = self.session.get('https://sarrafionline.com/', timeout=10)
            if response.status_code == 200:
                html = response.text
                match = re.search(r'دلار.*?(\d{2},\d{3})', html)
                if match:
                    price_str = match.group(1).replace(',', '')
                    if price_str.isdigit():
                        price_val = int(price_str)
                        if 50000 <= price_val <= 120000:
                            dollar_price = f"{price_val:,} تومان"
                            logging.info(f"✓ دلار از Sarrafionline: {price_val:,}")
                            return dollar_price
        except Exception as e:
            logging.error(f"خطا در Sarrafionline: {e}")
        
        return dollar_price

    def get_gold_from_multiple_sources(self):
        """دریافت قیمت طلا از چندین منبع"""
        gold_price = None
        
        # منبع 1: صفحه مستقیم طلا TGJU
        try:
            logging.info("گرفتن طلا از صفحه مستقیم TGJU...")
            response = self.session.get('https://www.tgju.org/profile/geram18', timeout=15)
            if response.status_code == 200:
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                
                price_elements = soup.find_all(['span', 'div', 'td'], class_=re.compile(r'price|nf|value'))
                for elem in price_elements:
                    text = elem.get_text().strip()
                    match = re.search(r'(\d{1,2},\d{3},\d{3})', text)
                    if match:
                        price_str = match.group(1).replace(',', '')
                        if price_str.isdigit():
                            price_val = int(price_str)
                            if 2000000 <= price_val <= 6000000:  # محدوده منطقی
                                gold_price = f"{price_val:,} تومان"
                                logging.info(f"✓ طلا از TGJU: {price_val:,}")
                                return gold_price
        except Exception as e:
            logging.error(f"خطا در TGJU طلا: {e}")
        
        # منبع 2: Talaonline
        try:
            logging.info("گرفتن طلا از Talaonline...")
            response = self.session.get('https://talaonline.com/', timeout=10)
            if response.status_code == 200:
                html = response.text
                match = re.search(r'18.*?عیار.*?(\d{1,2},\d{3},\d{3})', html)
                if match:
                    price_str = match.group(1).replace(',', '')
                    if price_str.isdigit():
                        price_val = int(price_str)
                        if 2000000 <= price_val <= 6000000:
                            gold_price = f"{price_val:,} تومان"
                            logging.info(f"✓ طلا از Talaonline: {price_val:,}")
                            return gold_price
        except Exception as e:
            logging.error(f"خطا در Talaonline: {e}")
        
        return gold_price

    def get_coin_from_multiple_sources(self):
        """دریافت قیمت سکه از چندین منبع"""
        coin_price = None
        
        # منبع 1: صفحه مستقیم سکه TGJU
        try:
            logging.info("گرفتن سکه از صفحه مستقیم TGJU...")
            response = self.session.get('https://www.tgju.org/profile/sekee', timeout=15)
            if response.status_code == 200:
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                
                price_elements = soup.find_all(['span', 'div', 'td'], class_=re.compile(r'price|nf|value'))
                for elem in price_elements:
                    text = elem.get_text().strip()
                    # سکه معمولا 8 رقمی است
                    match = re.search(r'(\d{2},\d{3},\d{3})', text)
                    if match:
                        price_str = match.group(1).replace(',', '')
                        if price_str.isdigit():
                            price_val = int(price_str)
                            if 20000000 <= price_val <= 80000000:  # محدوده منطقی
                                coin_price = f"{price_val:,} تومان"
                                logging.info(f"✓ سکه از TGJU: {price_val:,}")
                                return coin_price
        except Exception as e:
            logging.error(f"خطا در TGJU سکه: {e}")
        
        # منبع 2: Talaonline
        try:
            logging.info("گرفتن سکه از Talaonline...")
            response = self.session.get('https://talaonline.com/', timeout=10)
            if response.status_code == 200:
                html = response.text
                match = re.search(r'سکه.*?امامی.*?(\d{2},\d{3},\d{3})', html)
                if match:
                    price_str = match.group(1).replace(',', '')
                    if price_str.isdigit():
                        price_val = int(price_str)
                        if 20000000 <= price_val <= 80000000:
                            coin_price = f"{price_val:,} تومان"
                            logging.info(f"✓ سکه از Talaonline: {price_val:,}")
                            return coin_price
        except Exception as e:
            logging.error(f"خطا در Talaonline سکه: {e}")
        
        return coin_price

    def get_tether_from_exchanges(self):
        """دریافت قیمت تتر از صرافی‌ها"""
        tether_price = None
        
        # منبع 1: Nobitex
        try:
            logging.info("گرفتن تتر از Nobitex...")
            response = self.session.get('https://nobitex.ir/app/market/USDT-IRT', timeout=10)
            if response.status_code == 200:
                html = response.text
                match = re.search(r'(\d{2},\d{3})\s*ریال', html)
                if match:
                    price_rial = int(match.group(1).replace(',', ''))
                    price_toman = price_rial // 10
                    if 50000 <= price_toman <= 120000:
                        tether_price = f"{price_toman:,} تومان"
                        logging.info(f"✓ تتر از Nobitex: {price_toman:,}")
                        return tether_price
        except Exception as e:
            logging.error(f"خطا در Nobitex: {e}")
        
        # منبع 2: Wallex
        try:
            logging.info("گرفتن تتر از Wallex...")
            response = self.session.get('https://wallex.ir/exchange/USDT_TMN', timeout=10)
            if response.status_code == 200:
                html = response.text
                match = re.search(r'(\d{2},\d{3})', html)
                if match:
                    price_str = match.group(1).replace(',', '')
                    if price_str.isdigit():
                        price_val = int(price_str)
                        if 50000 <= price_val <= 120000:
                            tether_price = f"{price_val:,} تومان"
                            logging.info(f"✓ تتر از Wallex: {price_val:,}")
                            return tether_price
        except Exception as e:
            logging.error(f"خطا در Wallex: {e}")
        
        # منبع 3: BitPin
        try:
            logging.info("گرفتن تتر از BitPin...")
            response = self.session.get('https://bitpin.ir/market/USDT_IRT/', timeout=10)
            if response.status_code == 200:
                html = response.text
                match = re.search(r'(\d{2},\d{3})', html)
                if match:
                    price_str = match.group(1).replace(',', '')
                    if price_str.isdigit():
                        price_val = int(price_str)
                        if 50000 <= price_val <= 120000:
                            tether_price = f"{price_val:,} تومان"
                            logging.info(f"✓ تتر از BitPin: {price_val:,}")
                            return tether_price
        except Exception as e:
            logging.error(f"خطا در BitPin: {e}")
        
        return tether_price

    def get_crypto_from_binance(self):
        """دریافت قیمت کریپتو از Binance HTML"""
        prices = {}
        
        try:
            logging.info("گرفتن کریپتو از Binance...")
            
            # بیت‌کوین
            response = self.session.get('https://www.binance.com/en/price/bitcoin', timeout=10)
            if response.status_code == 200:
                html = response.text
                match = re.search(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', html)
                if match:
                    price_str = match.group(1).replace(',', '')
                    try:
                        price_val = float(price_str)
                        if price_val > 10000:
                            prices['بیت‌کوین'] = f"${price_val:,.0f}"
                            logging.info(f"✓ BTC از Binance HTML: ${price_val:,.0f}")
                    except:
                        pass
            
            # اتریوم
            response = self.session.get('https://www.binance.com/en/price/ethereum', timeout=10)
            if response.status_code == 200:
                html = response.text
                match = re.search(r'\$(\d{1,5}(?:\.\d{2})?)', html)
                if match:
                    price_str = match.group(1).replace(',', '')
                    try:
                        price_val = float(price_str)
                        if price_val > 1000:
                            prices['اتریوم'] = f"${price_val:,.0f}"
                            logging.info(f"✓ ETH از Binance HTML: ${price_val:,.0f}")
                    except:
                        pass
                        
        except Exception as e:
            logging.error(f"خطا در Binance HTML: {e}")
        
        # اگر Binance کار نکرد، CoinGecko امتحان کن
        if not prices:
            try:
                response = self.session.get('https://www.coingecko.com/', timeout=10)
                if response.status_code == 200:
                    html = response.text
                    
                    btc_match = re.search(r'bitcoin.*?\$(\d{1,3}(?:,\d{3})*)', html, re.IGNORECASE)
                    if btc_match:
                        price_val = float(btc_match.group(1).replace(',', ''))
                        if price_val > 10000:
                            prices['بیت‌کوین'] = f"${price_val:,.0f}"
                    
                    eth_match = re.search(r'ethereum.*?\$(\d{1,5})', html, re.IGNORECASE)
                    if eth_match:
                        price_val = float(eth_match.group(1).replace(',', ''))
                        if price_val > 1000:
                            prices['اتریوم'] = f"${price_val:,.0f}"
            except:
                pass
        
        return prices

    def collect_and_send_prices(self):
        """جمع‌آوری و ارسال قیمت‌ها"""
        logging.info("=" * 70)
        logging.info("🎯 شروع دریافت قیمت‌های دقیق...")
        
        try:
            main_prices = {}
            
            # دریافت از منابع مختلف
            dollar = self.get_dollar_from_multiple_sources()
            if dollar:
                main_prices['دلار آمریکا'] = dollar
            
            tether = self.get_tether_from_exchanges()
            if tether:
                main_prices['تتر'] = tether
            
            gold = self.get_gold_from_multiple_sources()
            if gold:
                main_prices['طلای 18 عیار'] = gold
            
            coin = self.get_coin_from_multiple_sources()
            if coin:
                main_prices['سکه امامی'] = coin
            
            crypto_prices = self.get_crypto_from_binance()
            
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
    
    logging.info("🎯 دریافت قیمت‌های دقیق شروع شد")
    scraper = AccuratePriceScraper(TELEGRAM_BOT_TOKEN, CHAT_ID)
    scraper.collect_and_send_prices()
    logging.info("✅ پایان")
    sys.exit(0)

if __name__ == "__main__":
    main()
