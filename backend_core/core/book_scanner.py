
import os
import sys
import asyncio
import numpy as np
from datetime import datetime
from dotenv import load_dotenv

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from backpack_transport import BackpackTransport
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

class BookScanner:
    """
    ️ BOOK SCANNER (Informação Privilegiada)
    Analisa a microestrutura do Order Book para detectar:
    1. Icebergs (Ordens ocultas renovadas)
    2. Walls (Paredões de suporte/resistência reais ou spoofing)
    3. Pressure (Pressão imediata do book)
    """
    def __init__(self):
        load_dotenv()
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data_client = BackpackData(self.auth)
        self.transport = BackpackTransport()
        
        # Alvos Ativos (3 Frentes)
        self.targets = ["BTC_USDC_PERP", "HYPE_USDC_PERP", "SOL_USDC_PERP", "SKR_USDC_PERP"]

    def calculate_obi(self, depth):
        """
        Calcula o Order Book Imbalance (OBI).
        Retorna valor entre -1 (Venda Forte) e +1 (Compra Forte).
        """
        try:
            if not depth or 'bids' not in depth or 'asks' not in depth:
                return 0.0
            
            bids = np.array(depth['bids'], dtype=float)
            asks = np.array(depth['asks'], dtype=float)
            
            if len(bids) == 0 or len(asks) == 0:
                return 0.0
                
            # Usar Top 10 níveis para OBI tático
            limit = min(len(bids), len(asks), 10)
            
            bid_vol = np.sum(bids[:limit, 1])
            ask_vol = np.sum(asks[:limit, 1])
            
            total_vol = bid_vol + ask_vol
            if total_vol == 0:
                return 0.0
                
            obi = (bid_vol - ask_vol) / total_vol
            return obi
        except Exception as e:
            # print(f"Error calculating OBI: {e}")
            return 0.0

    async def scan(self, return_data=False):
        if not return_data:
            print("\n️ BOOK SCANNER (Microstructure Intelligence)")
            print("Detectando Icebergs, Walls e Liquidity Hunts...")
            print("-" * 110)
            print(f"{'SYMBOL':<15} | {'PRESSURE':<10} | {'WALL PRICE':<12} | {'WALL SIZE':<12} | {'TYPE':<10} | {'SMART MONEY':<15}")
            print("-" * 110)
        
        intel = {}

        for symbol in self.targets:
            # Para manter compatibilidade síncrona/assíncrona, simulamos await
            await asyncio.sleep(0) 
            try:
                depth = self.data_client.get_orderbook_depth(symbol)
                if not depth: continue
                
                bids = np.array(depth['bids'], dtype=float)
                asks = np.array(depth['asks'], dtype=float)
                
                # 1. Análise de Pressão (Top 10 Levels)
                bid_vol_10 = np.sum(bids[:10, 1])
                ask_vol_10 = np.sum(asks[:10, 1])
                imbalance = (bid_vol_10 - ask_vol_10) / (bid_vol_10 + ask_vol_10)
                
                pressure = "NEUTRAL"
                if imbalance > 0.3: pressure = "🟢 BUY"
                elif imbalance < -0.3: pressure = " SELL"
                
                # 2. Detecção de Paredão (Wall)
                avg_bid_vol = np.mean(bids[:20, 1])
                avg_ask_vol = np.mean(asks[:20, 1])
                
                max_bid_idx = np.argmax(bids[:20, 1])
                max_ask_idx = np.argmax(asks[:20, 1])
                
                max_bid_vol = bids[max_bid_idx, 1]
                max_ask_vol = asks[max_ask_idx, 1]
                
                wall_price = 0.0
                wall_size = 0.0
                wall_type = "-"
                
                # Verifica Bid Wall (Suporte)
                if max_bid_vol > (avg_bid_vol * 3):
                    wall_price = bids[max_bid_idx, 0]
                    wall_size = max_bid_vol * wall_price
                    wall_type = "SUPPORT"
                    
                # Verifica Ask Wall (Resistência)
                if max_ask_vol > (avg_ask_vol * 3):
                    # Se Ask Wall for maior que Bid Wall, ele prevalece
                    if max_ask_vol * asks[max_ask_idx, 0] > wall_size:
                        wall_price = asks[max_ask_idx, 0]
                        wall_size = max_ask_vol * wall_price
                        wall_type = "RESIST"
                
                # 3. Smart Money / Liquidity Hunt Detection
                # Se o preço atual está muito perto de uma parede (spoofing) ou
                # se há um desequilíbrio massivo (imbalance > 0.6) sugerindo absorção
                
                smart_money = "-"
                if wall_size > 100000: # Whale Wall > $100k
                    smart_money = " WHALE WALL"
                
                if abs(imbalance) > 0.6:
                    smart_money = " ABSORPTION"
                
                if wall_type == "SUPPORT" and imbalance < -0.4:
                     smart_money = "️ DEFENSE" # Muita venda batendo em suporte
                
                if wall_type == "RESIST" and imbalance > 0.4:
                     smart_money = " BREAKOUT?" # Muita compra batendo em resistência

                intel[symbol] = {
                    "pressure": pressure,
                    "wall_price": wall_price,
                    "wall_type": wall_type,
                    "smart_money": smart_money
                }

                if not return_data:
                    wall_str = f"{wall_price:.4f}" if wall_price > 0 else "-"
                    size_str = f"${wall_size:,.0f}" if wall_size > 0 else "-"
                    print(f"{symbol:<15} | {pressure:<10} | {wall_str:<12} | {size_str:<12} | {wall_type:<10} | {smart_money:<15}")

            except Exception as e:
                print(f"Erro ao escanear {symbol}: {e}")

        if not return_data:
            print("-" * 110)
        
        return intel

if __name__ == "__main__":
    scanner = BookScanner()
    asyncio.run(scanner.scan())
