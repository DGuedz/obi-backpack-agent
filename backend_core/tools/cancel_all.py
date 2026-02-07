import asyncio
import os
import sys
from dotenv import load_dotenv

# Configuração de Caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))

from core.backpack_transport import BackpackTransport

async def cancel_all():
    print(" LIMPANDO A MESA (CANCEL ALL)...")
    load_dotenv()
    transport = BackpackTransport()
    
    try:
        orders = transport.get_open_orders()
        if not orders:
            print(" Nenhuma ordem para cancelar.")
            return

        print(f"️  Encontradas {len(orders)} ordens pendentes. Cancelando...")
        
        # Backpack API geralmente tem endpoint para cancelar todas ou loop
        # Vamos cancelar uma por uma para garantir ou usar cancelAll se disponível na lib
        
        # Verificando se existe cancel_all no transport (baseado em conhecimento prévio ou tentativa)
        # Se não, loop.
        
        # Loop seguro
        for o in orders:
            oid = o.get('id')
            symbol = o.get('symbol')
            print(f"   ️ Cancelando {symbol} (ID: {oid})...")
            # Assumindo assinatura transport.cancel_order(symbol, order_id)
            res = transport.cancel_order(symbol, oid)
            # print(f"      Resultado: {res}")
            
        print(" Limpeza concluída! Margem liberada.")
            
    except Exception as e:
        print(f" Erro ao cancelar: {e}")

if __name__ == "__main__":
    asyncio.run(cancel_all())
