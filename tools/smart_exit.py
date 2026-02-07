import asyncio
import os
import sys
import logging
from dotenv import load_dotenv

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from core.backpack_transport import BackpackTransport
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from core.technical_oracle import TechnicalOracle

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("SmartExit")

async def main():
    print(" INICIANDO SMART EXIT (OBI REVERSAL & PROFIT PROTECTION)...")
    load_dotenv()
    
    transport = BackpackTransport()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data_client = BackpackData(auth)
    oracle = TechnicalOracle(data_client)
    
    try:
        while True:
            positions = transport.get_positions()
            if not positions:
                print(" Nenhuma posição aberta. Dormindo 10s...")
                await asyncio.sleep(10)
                continue
                
            print(f"\n Analisando {len(positions)} posições para Saída Inteligente...")
            
            for pos in positions:
                symbol = pos.get('symbol')
                side = pos.get('side')
                qty = float(pos.get('netQuantity', pos.get('quantity', 0)))
                entry_price = float(pos.get('entryPrice'))
                
                if qty == 0: continue
                if not side: side = "Long" if qty > 0 else "Short"
                
                # Get Market Data
                ticker = transport.get_ticker(symbol)
                current_price = float(ticker.get('lastPrice'))
                
                # Calculate PnL
                if side == "Long":
                    roi = (current_price - entry_price) / entry_price
                else:
                    roi = (entry_price - current_price) / entry_price
                
                roi_pct = roi * 100
                print(f"    {symbol} ({side}): ROI {roi_pct:.2f}% | Entry: {entry_price} | Curr: {current_price}")
                
                # 1. OBI REVERSAL CHECK (Saída Técnica)
                # Se o fluxo virar CONTRA a posição fortemente, sair mesmo com pouco lucro ou pequeno prejuízo.
                depth = data_client.get_orderbook_depth(symbol)
                obi = oracle.calculate_obi(depth)
                
                reversal_detected = False
                
                if side == "Long" and obi < -0.2: # Fluxo Vendedor Forte
                    print(f"      ️ ALERTA DE REVERSÃO: OBI {obi:.2f} (Vendedor) em Long!")
                    reversal_detected = True
                elif side == "Short" and obi > 0.2: # Fluxo Comprador Forte
                    print(f"      ️ ALERTA DE REVERSÃO: OBI {obi:.2f} (Comprador) em Short!")
                    reversal_detected = True
                    
                # 2. DECISION MATRIX (SCALP MACHINE GUN EDITION) - PROFIT SNIPER
                # Meta: Lucro Rápido > 0.5% (Cobrir taxas e girar)
                
                # DEFINIÇÃO DE ROIS MÍNIMOS (CENTAVO A CENTAVO - NO LOSS)
                # Majors (BTC, ETH, SOL): 0.23% (Cobre 0.12% Fees + Spread)
                # Alts: 0.30% (Cobre 0.12% Fees + Maior Spread)
                
                is_major = symbol in ["BTC_USDC_PERP", "ETH_USDC_PERP", "SOL_USDC_PERP"]
                min_roi_target = 0.0023 if is_major else 0.0030
                
                # A. MOON BAG / BIG WIN (> 2%)
                if roi > 0.02: 
                     print(f"       PROFIT TARGET HIT (+{roi_pct:.2f}%): {symbol} atingiu meta de 2%. Fechando para garantir prova social.")
                     transport.execute_order(symbol, "Market", "Sell" if side == "Long" else "Buy", abs(qty))
                     continue

                # B. SCALP TARGET (> 0.6%) WITH WEAK FLOW
                # Se já temos lucro decente e o fluxo não é explosivo a favor, realiza.
                if roi > 0.006: 
                    is_pumping = (side == "Long" and obi > 0.5) or (side == "Short" and obi < -0.5)
                    if not is_pumping:
                        print(f"       SCALP SECURED (+{roi_pct:.2f}%): Fluxo normal. Garantindo lucro rápido em {symbol}.")
                        transport.execute_order(symbol, "Market", "Sell" if side == "Long" else "Buy", abs(qty))
                        continue
                
                # C. CENTAVO A CENTAVO (MICRO-PROFIT / BREAKEVEN)
                # Se o ROI cobriu taxas + spread e o mercado não está explodindo a favor -> REALIZAR
                # "Melhor um pássaro na mão (lucro real) do que dois voando (risco de reversão)"
                if roi > min_roi_target:
                    # Só sai se houver sinal de fraqueza ou estagnação (OBI < 0.2 a favor)
                    is_strong_flow = (side == "Long" and obi > 0.2) or (side == "Short" and obi < -0.2)
                    
                    if not is_strong_flow or reversal_detected:
                        print(f"       CENTAVO A CENTAVO (+{roi_pct:.2f}%): Lucro real garantido (Taxas pagas). Fechando {symbol}.")
                        transport.execute_order(symbol, "Market", "Sell" if side == "Long" else "Buy", abs(qty))
                        continue

                if reversal_detected:
                    # STRICT PROFIT RULE: Only exit if PnL covers fees
                    if roi > min_roi_target: # Garante que não sai no prejuízo real
                        print(f"       SAÍDA TÉCNICA (REVERSÃO) (+{roi_pct:.2f}%): Fechando {symbol} com lucro mínimo garantido.")
                        transport.execute_order(symbol, "Market", "Sell" if side == "Long" else "Buy", abs(qty))
                    
                    # DISABLE NEGATIVE EXIT ON REVERSAL
                    # elif roi < -0.01: 
                    #    print(f"       STOP TÉCNICO (-{roi_pct:.2f}%): OBI confirmou reversão. Abortando missão.")
                    #    transport.execute_order(symbol, "Market", "Sell" if side == "Long" else "Buy", abs(qty))
                    
                    else:
                        print(f"      ️ HOLDING THE LINE: Reversão detectada, mas PnL {roi_pct:.2f}% insuficiente (Min: {min_roi_target*100:.2f}%). Aguardando BreakEven.")
                
                await asyncio.sleep(0.5)
            
            print("⏳ Ciclo concluído. Aguardando 5s...")
            await asyncio.sleep(5)

    except KeyboardInterrupt:
        print("\n Smart Exit Encerrado.")

if __name__ == "__main__":
    asyncio.run(main())
