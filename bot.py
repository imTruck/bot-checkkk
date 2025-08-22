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

class PriceBot:
    def __init__(self, bot_token, chat_id):
        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id

    def get_crypto_prices(self):
        """کریپتو - کار می‌کنه، دست نمی‌زنیم"""
        prices = {}
        
        try:
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', timeout=10)
            if response.status_code == 200:
                btc_price = float(response.json()['price'])
                prices['بیت‌کوین'] = f"${btc_price:,.0f}"
                logging.info(f"✓ BTC: ${btc_price:,.0f}")
        except:
            pass
        
        try:
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT', timeout=10)
            if response.status_code == 200:
                eth_price = float(response.json()['price'])
                prices['اتریوم'] = f"${eth_price:,.0f}"
                logging.info(f"✓ ETH: ${eth_price:,.0f}")
        except:
            pass
        
        return prices

    def get_tether_simple(self):
        """تتر خیلی ساده"""
        try:
            # Nobitex API
            response = requests.get('https://api.nobitex.ir/market/stats?srcCurrency=usdt&dstCurrency=rls', timeout=10)
            if response.status_code == 200:
                text = response.text
                logging.info(f"Nobitex response: {text[:100]}...")
                
                data = response.json()
                stats = data.get('stats', {})
                usdt_rls = stats.get('usdt-rls', {})
                latest = usdt_rls.get('latest')
                
                if latest:
                    price_rial = float(latest)
                    price_toman = int(price_rial / 10)
                    logging.info(f"✓ USDT: {price_toman:,}")
                    return f"{price_toman:,} تومان"
        except Exception as e:
            logging.error(f"خطا تتر: {e}")
        
        return None

    def get_dollar_tgju_html(self):
        """دلار فقط از HTML سایت TGJU"""
        try:
            logging.info("دلار: TGJU HTML...")
            
            # صفحه اصلی TGJU
            response = requests.get('https://www.tgju.org/', 
                                  headers={'User-Agent': 'Mozilla/5.0'}, 
                                  timeout=15)
            
            if response.status_code == 200:
                html = response.text
                logging.info(f"TGJU HTML length: {len(html)}")
                
                # جستجوی همه اعداد 5 رقمی
                all_5digit_numbers = re.findall(r'\d{2},\d{3}', html)
                logging.info(f"Found {len(all_5digit_numbers)} 5-digit numbers")
                
                # اولین عدد 5 رقمی که بیشتر از 50000 باشد احتمالا دلار است
                for num in all_5digit_numbers:
                    price = int(num.replace(',', ''))
                    if price > 50000:
                        logging.info(f"✓ دلار از TGJU HTML: {price:,}")
                        return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا TGJU HTML: {e}")
        
        # اگر صفحه اصلی کار نکرد، صفحه مستقیم دلار
        try:
            logging.info("دلار: TGJU صفحه مستقیم...")
            
            response = requests.get('https://www.tgju.org/profile/price_dollar_rl', 
                                  headers={'User-Agent': 'Mozilla/5.0'}, 
                                  timeout=15)
            
            if response.status_code == 200:
                html = response.text
                logging.info(f"TGJU dollar page length: {len(html)}")
                
                # جستجوی اعداد 5 رقمی
                all_5digit_numbers = re.findall(r'\d{2},\d{3}', html)
                logging.info(f"Found {len(all_5digit_numbers)} numbers in dollar page")
                
                for num in all_5digit_numbers:
                    price = int(num.replace(',', ''))
                    if price > 50000:
                        logging.info(f"✓ دلار از TGJU مستقیم: {price:,}")
                        return f"{price:,} تومان"
        except Exception as e:
            logging.error(f"خطا TGJU مستقیم: {e}")
        
        return None

    def get_gold_price(self):
        """طلا - کار می‌کنه، دست نمی‌زنیم"""
        try:
            response = requests.get('https://api.tgju.org/v1/data/sana/json', timeout=15)
            if response.status_code == 200:
                data = response.json()
                if 'geram18' in data and 'p' in data['geram18']:
                    price_str = str(data['geram18']['p']).replace(',', '')
                    if price_str.isdigit():
                        price = int(price_str)
                        logging.info(f"✓ طلا: {price:,}")
                        return f"{price:,} تومان"
        except:
            pass
        
        try:
            response = requests.get('https://www.tgju.org/profile/geram18', 
                                  headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            if response.status_code == 200:
                html = response.text
                numbers = re.findall(r'(\d{1,2},\d{3},\d{3})', html)
                for num in numbers:
                    price = int(num.replace(',', ''))
                    if price > 1000000:
                        logging.info(f"✓ طلا HTML: {price:,}")
                        return f"{price:,} تومان"
        except:
            pass
        
        return None

    def get_coin_price(self):
        """سکه - کار می‌کنه، دست نمی‌زنیم"""
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
                        logging.info(f"✓ سکه: {price:,}")
                        return f"{price:,} تومان"
        except:
            pass
        
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
                        logging.info(f"✓ سکه HTML: {price:,}")
                        return f"{price:,} تومان"
        except:
            pass
        
        return None

    def collect_and_send_prices(self):
        """جمع‌آوری و ارسال"""
        logging.info("=" * 50)
        logging.info("🚀 شروع...")
        
        try:
            # جمع‌آوری
            crypto_prices = self.get_crypto_prices()
            tether = self.get_tether_simple()
            dollar = self.get_dollar_tgju_html()
            gold = self.get_gold_price()
            coin = self.get_coin_price()
            
            # پیام
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
            
            # لاگ
            logging.info(f"دلار: {dollar}")
            logging.info(f"تتر: {tether}")
            logging.info(f"طلا: {gold}")
            logging.info(f"سکه: {coin}")
            logging.info(f"کریپتو: {len(crypto_prices)} قیمت")
            
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
    bot = PriceBot(TELEGRAM_BOT_TOKEN, CHAT_ID)
    bot.collect_and_send_prices()
    logging.info("✅ پایان")
    sys.exit(0)

if __name__ == "__main__":
    main()
