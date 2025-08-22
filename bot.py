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

    def get_binance_prices(self):
        """قیمت از Binance"""
        prices = {}
        try:
            # بیت‌کوین
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', timeout=5)
            if response.status_code == 200:
                btc = float(response.json()['price'])
                prices['بیت‌کوین'] = f"${btc:,.0f}"
                logging.info(f"Binance BTC: ${btc:,.0f}")
            
            # اتریوم
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT', timeout=5)
            if response.status_code == 200:
                eth = float(response.json()['price'])
                prices['اتریوم'] = f"${eth:,.0f}"
                logging.info(f"Binance ETH: ${eth:,.0f}")
        except Exception as e:
            logging.error(f"Binance error: {e}")
        
        return prices

    def get_nobitex_prices(self):
        """قیمت از نوبیتکس"""
        prices = {}
        try:
            # تتر
            response = requests.get(
                'https://api.nobitex.ir/market/stats?srcCurrency=usdt&dstCurrency=rls',
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if 'stats' in data and 'usdt-rls' in data['stats']:
                    usdt = int(float(data['stats']['usdt-rls']['latest']) / 10)
                    prices['تتر (USDT)'] = f"{usdt:,} تومان"
                    logging.info(f"Nobitex USDT: {usdt:,}")
            
            # بیت‌کوین به تومان
            response = requests.get(
                'https://api.nobitex.ir/market/stats?srcCurrency=btc&dstCurrency=rls',
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if 'stats' in data and 'btc-rls' in data['stats']:
                    btc_rls = int(float(data['stats']['btc-rls']['latest']) / 10)
                    prices['بیت‌کوین (تومان)'] = f"{btc_rls:,} تومان"
                    logging.info(f"Nobitex BTC: {btc_rls:,}")
        except Exception as e:
            logging.error(f"Nobitex error: {e}")
        
        return prices

    def get_wallex_prices(self):
        """قیمت از والکس"""
        prices = {}
        try:
            response = requests.get('https://api.wallex.ir/v1/markets', timeout=5)
            if response.status_code == 200:
                data = response.json()
                markets = data.get('result', {}).get('symbols', {})
                
                # تتر
                if 'USDTTMN' in markets:
                    usdt = int(float(markets['USDTTMN']['stats']['bidPrice']))
                    if usdt > 40000:
                        prices['تتر (USDT)'] = f"{usdt:,} تومان"
                        logging.info(f"Wallex USDT: {usdt:,}")
                
                # بیت‌کوین
                if 'BTCTMN' in markets:
                    btc = int(float(markets['BTCTMN']['stats']['bidPrice']))
                    if btc > 1000000:
                        prices['بیت‌کوین (تومان)'] = f"{btc:,} تومان"
                        logging.info(f"Wallex BTC: {btc:,}")
        except Exception as e:
            logging.error(f"Wallex error: {e}")
        
        return prices

    def get_ramzinex_prices(self):
        """قیمت از رمزینکس"""
        prices = {}
        try:
            response = requests.get('https://publicapi.ramzinex.com/exchange/api/v1.0/exchange/pairs', timeout=5)
            if response.status_code == 200:
                data = response.json()
                for pair in data.get('data', []):
                    # تتر
                    if pair.get('base_currency_symbol') == 'usdt' and pair.get('quote_currency_symbol') == 'irr':
                        usdt = int(float(pair.get('sell', 0)) / 10)
                        if usdt > 40000:
                            prices['تتر (USDT)'] = f"{usdt:,} تومان"
                            logging.info(f"Ramzinex USDT: {usdt:,}")
                    
                    # بیت‌کوین
                    elif pair.get('base_currency_symbol') == 'btc' and pair.get('quote_currency_symbol') == 'irr':
                        btc = int(float(pair.get('sell', 0)) / 10)
                        if btc > 1000000:
                            prices['بیت‌کوین (تومان)'] = f"{btc:,} تومان"
                            logging.info(f"Ramzinex BTC: {btc:,}")
        except Exception as e:
            logging.error(f"Ramzinex error: {e}")
        
        return prices

    def get_bitpin_prices(self):
        """قیمت از بیت‌پین"""
        prices = {}
        try:
            response = requests.get('https://api.bitpin.ir/v1/mkt/markets/', timeout=5)
            if response.status_code == 200:
                data = response.json()
                for market in data.get('results', []):
                    # تتر
                    if market.get('currency1', {}).get('code') == 'USDT' and \
                       market.get('currency2', {}).get('code') == 'IRT':
                        usdt = int(float(market.get('price', 0)))
                        if usdt > 40000:
                            prices['تتر (USDT)'] = f"{usdt:,} تومان"
                            logging.info(f"BitPin USDT: {usdt:,}")
                    
                    # بیت‌کوین
                    elif market.get('currency1', {}).get('code') == 'BTC' and \
                         market.get('currency2', {}).get('code') == 'IRT':
                        btc = int(float(market.get('price', 0)))
                        if btc > 1000000:
                            prices['بیت‌کوین (تومان)'] = f"{btc:,} تومان"
                            logging.info(f"BitPin BTC: {btc:,}")
        except Exception as e:
            logging.error(f"BitPin error: {e}")
        
        return prices

    def get_coingecko_prices(self):
        """قیمت از CoinGecko"""
        prices = {}
        try:
            response = requests.get(
                'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,tether&vs_currencies=usd,irr',
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                
                # بیت‌کوین
                if 'bitcoin' in data:
                    btc_usd = data['bitcoin'].get('usd', 0)
                    if btc_usd > 0:
                        prices['بیت‌کوین'] = f"${btc_usd:,.0f}"
                        logging.info(f"CoinGecko BTC: ${btc_usd:,.0f}")
                    
                    btc_irr = data['bitcoin'].get('irr', 0)
                    if btc_irr > 0:
                        btc_tmn = int(btc_irr / 10)
                        prices['بیت‌کوین (تومان)'] = f"{btc_tmn:,} تومان"
                
                # اتریوم
                if 'ethereum' in data:
                    eth_usd = data['ethereum'].get('usd', 0)
                    if eth_usd > 0:
                        prices['اتریوم'] = f"${eth_usd:,.0f}"
                        logging.info(f"CoinGecko ETH: ${eth_usd:,.0f}")
        except Exception as e:
            logging.error(f"CoinGecko error: {e}")
        
        return prices

    def get_coincap_prices(self):
        """قیمت از CoinCap"""
        prices = {}
        try:
            response = requests.get('https://api.coincap.io/v2/assets?limit=10', timeout=5)
            if response.status_code == 200:
                data = response.json()
                for asset in data.get('data', []):
                    if asset['id'] == 'bitcoin':
                        btc = float(asset['priceUsd'])
                        prices['بیت‌کوین'] = f"${btc:,.0f}"
                        logging.info(f"CoinCap BTC: ${btc:,.0f}")
                    elif asset['id'] == 'ethereum':
                        eth = float(asset['priceUsd'])
                        prices['اتریوم'] = f"${eth:,.0f}"
                        logging.info(f"CoinCap ETH: ${eth:,.0f}")
        except Exception as e:
            logging.error(f"CoinCap error: {e}")
        
        return prices

    def get_metals_prices(self):
        """قیمت طلا از metals.live"""
        prices = {}
        try:
            response = requests.get('https://api.metals.live/v1/spot/gold', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    gold = float(data[0]['price'])
                    prices['طلا (اونس)'] = f"${gold:,.0f}"
                    logging.info(f"Gold: ${gold:,.0f}/oz")
        except Exception as e:
            logging.error(f"Metals error: {e}")
        
        return prices

    def get_exchangerate_prices(self):
        """نرخ ارز از ExchangeRate-API"""
        prices = {}
        try:
            response = requests.get('https://open.er-api.com/v6/latest/USD', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data['result'] == 'success':
                    rates = data['rates']
                    
                    # یورو به دلار
                    if 'EUR' in rates:
                        eur = rates['EUR']
                        prices['یورو/دلار'] = f"{eur:.4f}"
                        logging.info(f"EUR/USD: {eur}")
                    
                    # ریال به دلار (رسمی)
                    if 'IRR' in rates:
                        irr = int(rates['IRR'] / 10)
                        prices['دلار (رسمی)'] = f"{irr:,} تومان"
                        logging.info(f"USD official: {irr:,}")
        except Exception as e:
            logging.error(f"ExchangeRate error: {e}")
        
        return prices

    def collect_all_prices(self):
        """جمع‌آوری همه قیمت‌ها از منابع مختلف"""
        all_prices = {}
        
        logging.info("Getting prices from Binance...")
        all_prices.update(self.get_binance_prices())
        
        logging.info("Getting prices from Nobitex...")
        all_prices.update(self.get_nobitex_prices())
        
        logging.info("Getting prices from Wallex...")
        wallex = self.get_wallex_prices()
        for key, value in wallex.items():
            if key not in all_prices:
                all_prices[key] = value
        
        logging.info("Getting prices from CoinGecko...")
        coingecko = self.get_coingecko_prices()
        for key, value in coingecko.items():
            if key not in all_prices:
                all_prices[key] = value
        
        logging.info("Getting prices from CoinCap...")
        coincap = self.get_coincap_prices()
        for key, value in coincap.items():
            if key not in all_prices:
                all_prices[key] = value
        
        logging.info("Getting prices from ExchangeRate...")
        all_prices.update(self.get_exchangerate_prices())
        
        logging.info("Getting gold price...")
        all_prices.update(self.get_metals_prices())
        
        return all_prices

    def format_message(self, prices):
        """فرمت کردن پیام"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"📊 گزارش قیمت‌های لحظه‌ای\n"
        message += f"🕐 زمان: {current_time}\n\n"
        
        if prices:
            # ارزهای دیجیتال دلاری
            crypto_usd = []
            if 'بیت‌کوین' in prices:
                crypto_usd.append(f"🟠 بیت‌کوین: {prices['بیت‌کوین']}")
            if 'اتریوم' in prices:
                crypto_usd.append(f"🔵 اتریوم: {prices['اتریوم']}")
            
            if crypto_usd:
                message += "₿ ارزهای دیجیتال (دلار):\n"
                message += "\n".join(crypto_usd) + "\n\n"
            
            # ارزهای دیجیتال تومانی
            crypto_tmn = []
            if 'تتر (USDT)' in prices:
                crypto_tmn.append(f"🟢 تتر: {prices['تتر (USDT)']}")
            if 'بیت‌کوین (تومان)' in prices:
                crypto_tmn.append(f"🟠 بیت‌کوین: {prices['بیت‌کوین (تومان)']}")
            
            if crypto_tmn:
                message += "💰 ارزهای دیجیتال (تومان):\n"
                message += "\n".join(crypto_tmn) + "\n\n"
            
            # سایر قیمت‌ها
            others = []
            if 'دلار (رسمی)' in prices:
                others.append(f"💵 دلار رسمی: {prices['دلار (رسمی)']}")
            if 'یورو/دلار' in prices:
                others.append(f"💶 نرخ یورو/دلار: {prices['یورو/دلار']}")
            if 'طلا (اونس)' in prices:
                others.append(f"🥇 طلا: {prices['طلا (اونس)']}")
            
            if others:
                message += "📈 سایر قیمت‌ها:\n"
                message += "\n".join(others) + "\n\n"
            
            message += f"📊 تعداد: {len(prices)} قیمت از منابع مختلف\n\n"
        else:
            message += "⚠️ هیچ قیمتی دریافت نشد\n\n"
        
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
        logging.info("=" * 60)
        logging.info("🚀 شروع جمع‌آوری قیمت‌ها...")
        
        try:
            prices = self.collect_all_prices()
            
            logging.info(f"📊 تعداد قیمت‌های دریافتی: {len(prices)}")
            for name, price in prices.items():
                logging.info(f"  ✓ {name}: {price}")
            
            message = self.format_message(prices)
            success = asyncio.run(self.send_message(message))
            
            if success:
                logging.info("✅ عملیات موفق")
            else:
                logging.error("❌ خطا در ارسال")
                
        except Exception as e:
            logging.error(f"❌ خطا: {e}")
            import traceback
            traceback.print_exc()

def main():
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        print("❌ لطفاً TELEGRAM_BOT_TOKEN و CHAT_ID را تنظیم کنید!")
        sys.exit(1)
    
    logging.info("🤖 ربات شروع شد")
    monitor = PriceMonitor(TELEGRAM_BOT_TOKEN, CHAT_ID)
    monitor.collect_and_send_prices()
    logging.info("✅ پایان")
    sys.exit(0)

if __name__ == "__main__":
    main()
