import os
import sys
import asyncio
import argparse
from dotenv import load_dotenv

# Adicionar caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), 'strategies'))
sys.path.append(os.path.join(os.getcwd(), 'safety'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from backpack_transport import BackpackTransport
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from risk_manager import RiskManager
from sniper_executor import SniperExecutor

async def manual_entry(symbol, side, leverage=5, order_type="Limit", farm_mode=False):
    load_dotenv()
    
    print(f"\n MANUAL SNIPER ENTRY: {symbol} [{side}]")
    if farm_mode:
        print(f" FARM MODE ATIVADO: Volume & Speed Focus")
    print(f"️  Alavancagem: {leverage}x | Tipo: {order_type} | Margem: 70% (Risk Manager)")
    print("Inicializando componentes...")
    
    transport = BackpackTransport()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data_client = BackpackData(auth)
    risk_manager = RiskManager(transport)
    sniper = SniperExecutor(transport, data_client, risk_manager)
    
    try:
        # 1. Dados de Mercado para Preço e SL
        depth = data_client.get_orderbook_depth(symbol)
        oracle = sniper.oracle # Reuso
        
        # Smart Price
        if order_type == "Limit":
            smart_price, reason = oracle.get_smart_entry_price(symbol, side)
            if smart_price <= 0:
                print(" Erro ao calcular preço inteligente.")
                return
    
            # Ajuste para PostOnly: Se Sell, preço deve ser > Best Bid.
            # O Smart Entry tenta Match Best Ask.
            # Se o mercado mover rápido, Best Ask pode virar Best Bid (spread cruzado ou volatilidade).
            depth = data_client.get_orderbook_depth(symbol)
            if side == "Sell":
                best_bid = float(depth['bids'][-1][0])
                if smart_price <= best_bid:
                    smart_price = best_bid + 0.05 # Força maior que Best Bid (Maker)
                    print(f"️ Ajuste Maker: Preço ({smart_price}) forçado acima do Best Bid ({best_bid})")
            else:
                best_ask = float(depth['asks'][0][0])
                if smart_price >= best_ask:
                    smart_price = best_ask - 0.05 # Força menor que Best Ask (Maker)
                    print(f"️ Ajuste Maker: Preço ({smart_price}) forçado abaixo do Best Ask ({best_ask})")
    
            # Round price to avoid API Error
            if "BTC" in symbol: smart_price = round(smart_price, 1)
            elif "ETH" in symbol: smart_price = round(smart_price, 2)
            else: smart_price = round(smart_price, 4)
    
            print(f" Preço Alvo: {smart_price} ({reason})")
        else:
            # Market Order - Preço é apenas referência para cálculo de SL/TP
            ticker = data_client.get_ticker(symbol)
            smart_price = float(ticker['lastPrice'])
            print(f" Preço Referência (Market): {smart_price}")
        
        # SL Calculation (ATR)
        context = {}
        atr = oracle.get_atr(symbol)
        ticker = data_client.get_ticker(symbol)
        current_price = float(ticker['lastPrice'])
        atr_pct = (atr / current_price) if current_price > 0 else 0.01
        
        if farm_mode:
             # Farm Mode: SL Ultra Apertado (0.5% a 1.0%) para giro rápido
             sl_dist_pct = max(0.005, min(atr_pct, 0.01))
             print(f" FARM SL: Ajustado para max 1% (Atual: {sl_dist_pct*100:.2f}%)")
        else:
             # Normal Mode: SL 1.5x ATR (Conservador, max 1.5%)
             sl_dist_pct = max(0.005, min(atr_pct * 1.5, 0.015))
        
        # Target ROE
        target_roe = 0.05

        if farm_mode:
            target_roe = 0.02
            print(" FARM MODE: ROE ajustado para 2% (Scalp Rápido)")
            # Ajuste de Alavancagem para Farm se OBI for forte
            if leverage < 10:
                print(f" FARM BOOST: Aumentando alavancagem de {leverage}x para 10x (Eficiência de Capital)")
                leverage = 10
        
        if side == "Buy":
            sl_price = smart_price * (1 - sl_dist_pct)
            tp_price = smart_price * (1 + (target_roe / leverage))
        else:
            sl_price = smart_price * (1 + sl_dist_pct)
            tp_price = smart_price * (1 - (target_roe / leverage))
            
        print(f"️ Stop Loss: {sl_price:.4f} (-{sl_dist_pct*100:.2f}%)")
        print(f" Take Profit: {tp_price:.4f} (ROE 5%)")
        
        # 2. Size Calculation
        safe, usable_capital = risk_manager.check_capital_safety()
        if not safe:
            print(" Capital Insuficiente ou Reserva Atingida.")
            return
            
        # Usar todo o capital disponível permitido (70%) para a alavancagem
        quantity = risk_manager.calculate_leveraged_position_size(usable_capital, leverage, smart_price, depth=depth)
        
        # Adjust precision

        if "BTC" in symbol: quantity = round(quantity, 3)
        elif "ETH" in symbol: quantity = round(quantity, 2)
        elif "SOL" in symbol: quantity = round(quantity, 1)
        else: quantity = round(quantity, 0)
        
        print(f" Quantidade: {quantity} (Lev {leverage}x | Margin ${usable_capital:.2f})")
        
        # 3. Execution
        # confirm = input(f"️ CONFIRMAR EXECUÇÃO {side} {quantity} {symbol} @ {smart_price}? (y/n): ")
        # if confirm.lower() != 'y':
        #     print(" Operação Cancelada.")
        #     return
        print(f" Executando {side} em {symbol} imediatamente...")
            
        payload = {
            "symbol": symbol,
            "side": "Bid" if side == "Buy" else "Ask",
            "orderType": order_type,
            "quantity": str(quantity),
            "selfTradePrevention": "RejectTaker",
            "stopLossTriggerPrice": str(round(sl_price, 2))
        }
        
        if order_type == "Limit":
            payload["price"] = str(smart_price)
            payload["postOnly"] = True
        
        res = transport._send_request("POST", "/api/v1/order", "orderExecute", payload)
        
        if res and 'id' in res:
            print(f" ORDEM ENVIADA COM SUCESSO! ID: {res['id']}")
            print(f"️ NOTA: O Take Profit ({tp_price:.4f}) NÃO foi enviado atomicamente para economizar taxas.")
            print("   -> O 'stealth_monitor.py' ou 'PositionManager' deve colocar a ordem Limit Maker assim que preencher.")
        else:
            print(f" Erro no envio: {res}")
            
    except Exception as e:
        print(f" ERRO FATAL: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", required=True, help="Símbolo do ativo (ex: SOL_USDC_PERP)")
    parser.add_argument("--side", required=True, choices=["Buy", "Sell"], help="Direção (Buy/Sell)")
    parser.add_argument("--leverage", type=int, default=5, help="Alavancagem (Default: 5)")
    parser.add_argument("--type", default="Limit", choices=["Limit", "Market"], help="Tipo de Ordem (Limit/Market)")
    parser.add_argument("--farm", action="store_true", help="Ativar modo Farm (ROE 2 pct)")
    args = parser.parse_args()
    
    asyncio.run(manual_entry(args.symbol, args.side, args.leverage, args.type, args.farm))
