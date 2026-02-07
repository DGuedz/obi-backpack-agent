
import os
import sys
import asyncio
import aiohttp
import pandas as pd
from datetime import datetime

# Adicionar caminhos
sys.path.append(os.getcwd())

class MarketFlowAnalyzer:
    def __init__(self):
        self.base_url = "https://api.backpack.exchange"
        
    async def get_recent_trades(self, session, symbol, limit=1000):
        url = f"{self.base_url}/api/v1/trades?symbol={symbol}&limit={limit}"
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                return []
        except Exception as e:
            print(f"Erro ao buscar trades para {symbol}: {e}")
            return []

    async def get_depth(self, session, symbol):
        url = f"{self.base_url}/api/v1/depth?symbol={symbol}"
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                return {}
        except:
            return {}

    def analyze_trades(self, trades, symbol):
        if not trades:
            return None
            
        df = pd.DataFrame(trades)
        
        # Backpack Trade Schema: 
        # { "id": "...", "price": "...", "quantity": "...", "quoteQuantity": "...", "time": "...", "isBuyerMaker": bool }
        
        df['price'] = df['price'].astype(float)
        df['quantity'] = df['quantity'].astype(float)
        df['quoteQuantity'] = df['quoteQuantity'].astype(float)
        
        # Interpretar Lado do Taker (Quem agrediu)
        # Se isBuyerMaker = True -> O Maker era Comprador (Bid no Livro). Logo, Taker Vendeu (Sell).
        # Se isBuyerMaker = False -> O Maker era Vendedor (Ask no Livro). Logo, Taker Comprou (Buy).
        
        df['side'] = df['isBuyerMaker'].apply(lambda x: 'SELL' if x else 'BUY')
        
        total_vol = df['quoteQuantity'].sum()
        buy_vol = df[df['side'] == 'BUY']['quoteQuantity'].sum()
        sell_vol = df[df['side'] == 'SELL']['quoteQuantity'].sum()
        
        delta = buy_vol - sell_vol
        delta_pct = (delta / total_vol) * 100 if total_vol > 0 else 0
        
        # Whale Detection (Trades > 95th percentile)
        whale_thresh = df['quoteQuantity'].quantile(0.95)
        whale_trades = df[df['quoteQuantity'] >= whale_thresh]
        
        whale_buy_vol = whale_trades[whale_trades['side'] == 'BUY']['quoteQuantity'].sum()
        whale_sell_vol = whale_trades[whale_trades['side'] == 'SELL']['quoteQuantity'].sum()
        whale_delta = whale_buy_vol - whale_sell_vol
        
        return {
            "symbol": symbol,
            "price": df['price'].iloc[-1], # Último preço
            "total_vol": total_vol,
            "buy_vol": buy_vol,
            "sell_vol": sell_vol,
            "delta": delta,
            "delta_pct": delta_pct,
            "whale_delta": whale_delta,
            "whale_count": len(whale_trades),
            "last_trade_time": datetime.fromtimestamp(int(trades[-1]['timestamp'])/1000).strftime('%H:%M:%S') if 'timestamp' in trades[-1] else "N/A"
        }

    async def run_analysis(self):
        symbols = [
            "BTC_USDC_PERP", "ETH_USDC_PERP", "SOL_USDC_PERP", 
            "HYPE_USDC_PERP", "DOGE_USDC_PERP", "SUI_USDC_PERP"
        ]
        
        print("\n ON-CHAIN FLOW ANALYZER (Backpack Market Data)")
        print("Analisando fluxo de Taker (Agressão) e Baleias nos últimos 1000 trades...")
        print("-" * 110)
        print(f"{'SYMBOL':<15} | {'PRICE':<10} | {'DELTA VOL($)':<14} | {'SENTIMENT':<10} | {'WHALE FLOW':<12} | {'VERDICT':<10}")
        print("-" * 110)
        
        async with aiohttp.ClientSession() as session:
            tasks = [self.get_recent_trades(session, sym) for sym in symbols]
            results = await asyncio.gather(*tasks)
            
            for i, trades in enumerate(results):
                symbol = symbols[i]
                data = self.analyze_trades(trades, symbol)
                
                if not data:
                    continue
                    
                # Formatação
                price_fmt = f"{data['price']:.4f}"
                delta_fmt = f"${data['delta']:,.0f}"
                
                # Sentiment
                if data['delta_pct'] > 5: sentiment = "🟢 BULLISH"
                elif data['delta_pct'] < -5: sentiment = " BEARISH"
                else: sentiment = " NEUTRAL"
                
                # Whale Flow
                whale_emoji = " BUY" if data['whale_delta'] > 0 else " SELL"
                if abs(data['whale_delta']) < (data['total_vol'] * 0.05): whale_emoji = " FLAT"
                
                # Verdict
                verdict = "WAIT"
                if "BULL" in sentiment and "BUY" in whale_emoji: verdict = " LONG"
                if "BEAR" in sentiment and "SELL" in whale_emoji: verdict = " SHORT"
                
                print(f"{symbol:<15} | {price_fmt:<10} | {delta_fmt:<14} | {sentiment:<10} | {whale_emoji:<12} | {verdict:<10}")

if __name__ == "__main__":
    analyzer = MarketFlowAnalyzer()
    asyncio.run(analyzer.run_analysis())
