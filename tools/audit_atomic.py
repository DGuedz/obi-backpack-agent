import os
import sys
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add paths
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))

from backpack_transport import BackpackTransport

def audit_account():
    print("️ INICIANDO AUDITORIA ATÔMICA DA CONTA...")
    load_dotenv()
    
    transport = BackpackTransport()
    
    # 1. PnL & Balance
    print("\n SALDO & MARGEM:")
    try:
        collateral = transport.get_account_collateral()
        if collateral:
            print(f"   Saldo USDC: ${collateral.get('availableToTrade', '0.00')}")
            print(f"   Equity:     ${collateral.get('equity', '0.00')}")
            print(f"   Margin:     ${collateral.get('initialMargin', '0.00')}")
        else:
            print("    Falha ao obter saldo.")
    except Exception as e:
        print(f"    Erro: {e}")

    # 2. Posições Abertas
    print("\n POSIÇÕES ABERTAS:")
    try:
        positions = transport.get_positions()
        if positions:
            for p in positions:
                symbol = p['symbol']
                side = "LONG" if float(p['netQuantity']) > 0 else "SHORT"
                entry = float(p['entryPrice'])
                mark = float(p['markPrice'])
                qty = float(p['netQuantity'])
                pnl = float(p.get('unrealizedPnl', 0))
                
                print(f"   {symbol:<15} | {side:<5} | Entry: {entry:<8.4f} | Mark: {mark:<8.4f} | PnL: ${pnl:.2f}")
        else:
            print("    Nenhuma posição aberta.")
    except Exception as e:
        print(f"    Erro ao buscar posições: {e}")

    # 3. Histórico de Fills (Últimas 100)
    print("\n HISTÓRICO DE TRADES (Últimos 100):")
    try:
        # Endpoint correto para fills history geralmente é /api/v1/history/fills ou wapi
        # Vamos tentar o instruction fillHistoryQueryAll
        # Se falhar sem symbol, tentamos com symbol para os ativos principais
        
        # Tentativa 1: Geral
        fills = transport._send_request("GET", "/api/v1/history/fills", "fillHistoryQueryAll", {"limit": 100})
        
        if not fills:
            # Fallback: Tentar por Símbolo (os do farmer)
            print("   ️ Consulta geral vazia/falha. Tentando por ativo...")
            top_symbols = ["BTC_USDC_PERP", "SOL_USDC_PERP", "ETH_USDC_PERP", "HYPE_USDC_PERP", "BNB_USDC_PERP", "XRP_USDC_PERP"]
            fills = []
            for sym in top_symbols:
                f = transport._send_request("GET", "/api/v1/history/fills", "fillHistoryQueryAll", {"symbol": sym, "limit": 20})
                if f: fills.extend(f)
        
        if fills:
            # Converter para DataFrame para analise
            df = pd.DataFrame(fills)
            df['price'] = df['price'].astype(float)
            df['quantity'] = df['quantity'].astype(float)
            df['fee'] = df['fee'].astype(float)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Ordenar
            df = df.sort_values('timestamp', ascending=False)
            
            total_vol = (df['price'] * df['quantity']).sum()
            total_fees = df['fee'].sum()
            
            print(f"   Volume Total (100 fills): ${total_vol:.2f}")
            print(f"   Taxas Pagas:              ${total_fees:.2f}")
            print(f"   Último Trade:             {df['timestamp'].iloc[0]}")
            
            print("\n   TOP 10 FILLS RECENTES:")
            print(df[['symbol', 'side', 'price', 'quantity', 'fee']].head(10).to_string(index=False))
            
            # Tentativa de PnL Realizado (Match fills) - Simplificado
            # Agrupar por symbol
            print("\n   RESUMO POR ATIVO:")
            grouped = df.groupby('symbol').agg({
                'quantity': 'sum',
                'fee': 'sum',
                'price': 'mean' # Preço médio
            })
            print(grouped)
            
        else:
            print("    Nenhum fill encontrado ou erro de permissão.")

    except Exception as e:
        print(f"    Erro Crítico na Auditoria: {e}")

if __name__ == "__main__":
    audit_account()
