
import os
import sys
import json
import time
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv

# Adiciona diretórios ao path
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_transport import BackpackTransport

# Carrega variáveis de ambiente
load_dotenv()

class TradeAuditor:
    def __init__(self):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.transport = BackpackTransport()
        self.base_url = "https://api.backpack.exchange"

    def get_order_history(self, limit=1000, offset=0):
        """
        Busca histórico de ordens.
        Endpoint: GET /wapi/v1/history/orders
        Instrução: orderHistoryQueryAll
        """
        endpoint = "/wapi/v1/history/orders"
        url = f"{self.base_url}{endpoint}"
        instruction = "orderHistoryQueryAll"
        
        params = {'limit': str(limit), 'offset': str(offset)}
        headers = self.auth.get_headers(instruction=instruction, params=params)
        
        try:
            response = self.transport._send_request("GET", endpoint, instruction, payload=None)
            # O transport já lida com requests, mas _send_request espera endpoint sem base_url se usar transport
            # O transport do core usa endpoint relativo.
            # Vamos usar requests direto com auth para ter controle total ou adaptar para transport.
            # O transport._send_request usa self.base_url + endpoint.
            # O endpoint deve ser relativo.
            return response if response else []
        except Exception as e:
            print(f"Erro ao buscar histórico de ordens: {e}")
            return []

    def run_audit(self, hours=1):
        print(f"\n️‍️ INICIANDO AUDITORIA COMPLETA (ÚLTIMAS {hours} HORAS)")
        print(f"======================================================")
        
        # 1. Definir Janela de Tempo
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        print(f" Janela: {start_time.strftime('%H:%M:%S')} até {end_time.strftime('%H:%M:%S')}")
        
        # 2. Buscar Histórico de Fills (Execuções)
        print("\n Buscando Execuções (Fills)...")
        fills = self.data.get_fill_history(limit=1000)
        recent_fills = []
        
        for fill in fills:
            # Timestamp vem em milissegundos ou ISO? Backpack costuma ser ISO ou ms.
            # Verificando formato no código existente: investigate_drop.py trata ambos.
            ts_val = fill.get('timestamp')
            try:
                if isinstance(ts_val, str):
                    ts = datetime.fromisoformat(ts_val.replace('Z', '+00:00')).replace(tzinfo=None)
                else:
                    ts = datetime.fromtimestamp(int(ts_val) / 1000.0)
            except:
                continue
                
            if ts >= start_time:
                recent_fills.append({**fill, 'parsed_time': ts})
        
        print(f"    {len(recent_fills)} execuções encontradas.")
        
        # 3. Buscar Histórico de Ordens (Orders)
        print("\n Buscando Histórico de Ordens...")
        # Nota: O endpoint de history order pode precisar de paginação se houver muitas.
        # Transport method need adaptation? _send_request implementation:
        # requests.get(url, headers=headers) -> headers from auth.get_headers(instruction, payload)
        # GET payload is params? BackpackAuth uses params for GET signature?
        # BackpackAuth.get_headers(instruction, params)
        # BackpackTransport._send_request does NOT pass params to get_headers for GET, only payload for POST?
        # Let's check BackpackTransport._send_request implementation.
        # It calls: headers = self.auth.get_headers(instruction, payload)
        # If method is GET, payload is usually None. But for history endpoints, params are needed for signature.
        # BackpackTransport might be limited. Let's use requests directly here for safety.
        
        import requests
        endpoint = "/wapi/v1/history/orders"
        url = f"{self.base_url}{endpoint}"
        instruction = "orderHistoryQueryAll"
        params = {'limit': '1000', 'offset': '0'}
        headers = self.auth.get_headers(instruction=instruction, params=params)
        
        recent_orders = []
        try:
            resp = requests.get(url, headers=headers, params=params)
            if resp.status_code == 200:
                orders = resp.json()
                for order in orders:
                    ts_val = order.get('timestamp') or order.get('createdAt') # Check field name
                    try:
                        if isinstance(ts_val, str):
                            ts = datetime.fromisoformat(ts_val.replace('Z', '+00:00')).replace(tzinfo=None)
                        else:
                            ts = datetime.fromtimestamp(int(ts_val) / 1000.0)
                    except:
                        continue
                        
                    if ts >= start_time:
                        recent_orders.append({**order, 'parsed_time': ts})
            else:
                print(f"    Erro API Ordens: {resp.status_code} {resp.text}")
        except Exception as e:
            print(f"    Erro Request Ordens: {e}")

        print(f"    {len(recent_orders)} ordens encontradas.")
        
        # 4. Processar e Gerar Relatório
        if not recent_orders and not recent_fills:
            print("\n️ Nenhuma atividade registrada no período.")
            return

        print("\n RELATÓRIO DE EXECUÇÃO")
        print("----------------------------------------------------------------")
        print(f"{'HORA':<10} | {'SYMBOL':<15} | {'SIDE':<5} | {'TYPE':<8} | {'PRICE':<10} | {'QTY':<8} | {'STATUS':<10} | {'ROLE':<5}")
        print("----------------------------------------------------------------")
        
        # Mesclar e ordenar por tempo
        # Fills dão a execução real (preço, taxa, role)
        # Ordens dão a intenção (limit price, stop loss params)
        
        # Vamos listar Ordens primeiro para ver o fluxo
        recent_orders.sort(key=lambda x: x['parsed_time'])
        
        for order in recent_orders:
            t_str = order['parsed_time'].strftime('%H:%M:%S')
            symbol = order.get('symbol', '-')
            side = order.get('side', '-')
            otype = order.get('orderType', '-')
            
            price_val = order.get('price')
            if price_val is None:
                price = 0.0
            else:
                price = float(price_val)
                
            qty_val = order.get('quantity')
            if qty_val is None:
                qty = 0.0
            else:
                qty = float(qty_val)
            status = order.get('status', '-')
            
            # Tentar encontrar fill correspondente para ver se foi Maker ou Taker
            fill_info = next((f for f in recent_fills if f.get('orderId') == order.get('id')), None)
            role = "NONE"
            if fill_info:
                role = "MAKER" if fill_info.get('isMaker') else "TAKER"
                exec_price = float(fill_info.get('price', 0))
                # Slippage Check
                if otype == "Limit" and price > 0:
                    slip = (exec_price - price) / price
                    if abs(slip) > 0.0001: # 0.01%
                        status += f" (Slip {slip*100:.3f}%)"
            
            print(f"{t_str:<10} | {symbol:<15} | {side:<5} | {otype:<8} | {price:<10.2f} | {qty:<8.2f} | {status:<10} | {role:<5}")
            
            # Detalhes de Stop Loss / Take Profit se disponíveis na ordem
            if 'stopLossTriggerPrice' in order or 'takeProfitTriggerPrice' in order:
                sl = order.get('stopLossTriggerPrice', 'N/A')
                tp = order.get('takeProfitTriggerPrice', 'N/A')
                print(f"           ↳ Atomic Protection: SL={sl} | TP={tp}")

        print("----------------------------------------------------------------")
        
        # 5. Análise de Custos e Resultado
        total_fees = 0.0
        total_volume = 0.0
        maker_fills = 0
        taker_fills = 0
        
        for fill in recent_fills:
            fee = float(fill.get('fee', 0))
            qty = float(fill.get('quantity', 0))
            price = float(fill.get('price', 0))
            vol = qty * price
            
            total_fees += fee
            total_volume += vol
            
            if fill.get('isMaker'):
                maker_fills += 1
            else:
                taker_fills += 1
                
        print(f"\n RESUMO FINANCEIRO (Estimado)")
        print(f"   Volume Total:    ${total_volume:.2f}")
        print(f"   Taxas Pagas:     ${total_fees:.4f}")
        print(f"   Trades Maker:    {maker_fills}")
        print(f"   Trades Taker:    {taker_fills}")
        
        if taker_fills > 0:
            print(f"   ️ ALERTA: {taker_fills} execuções TAKER detectadas! (Custo maior)")
        else:
            print(f"    PARABÉNS: 100% MAKER (Eficiência Máxima)")

if __name__ == "__main__":
    auditor = TradeAuditor()
    auditor.run_audit(hours=1)
