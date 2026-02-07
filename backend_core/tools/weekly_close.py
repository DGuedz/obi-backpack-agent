import os
import sys
import re
from datetime import datetime

def calculate_session_volume():
    log_files = {
        'BTC_USDC_PERP': {'file': 'farm_btc.log', 'size': 168},
        'SKR_USDC_PERP': {'file': 'farm_skr.log', 'size': 48},
        'FOGO_USDC_PERP': {'file': 'farm_fogo.log', 'size': 24}
    }
    
    total_volume = 0
    total_trades = 0
    
    print("\n" + "="*60)
    print("          OBI WORK - WEEKLY SESSION CLOSE ")
    print("="*60)
    print(f" DATA: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    for symbol, data in log_files.items():
        if not os.path.exists(data['file']):
            continue
            
        with open(data['file'], 'r') as f:
            content = f.read()
            
        # Count Fills (Entries)
        fills = len(re.findall(r"FILL EM", content))
        
        # Count Exits (TP + Emergency)
        tps = len(re.findall(r"TP Green Sell", content))
        emergencies = len(re.findall(r"FECHANDO (LONG|SHORT)", content))
        stops = len(re.findall(r"Stop Loss Executado", content)) # Hypothetical
        
        # Total Actions
        actions = fills + tps + emergencies + stops
        
        # Volume Calculation (Estimate)
        # Assuming each action moves the full size (conservative estimate)
        vol = actions * data['size']
        
        total_volume += vol
        total_trades += actions
        
        print(f" {symbol:<15} | Execuções: {actions:<4} | Vol. Est: ${vol:,.2f}")
        
    print("-" * 60)
    print(f" VOLUME TOTAL DA SESSÃO: ${total_volume:,.2f}")
    print(f" TOTAL DE EXECUÇÕES:    {total_trades}")
    print("=" * 60)
    print("Signed: obiwork")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    calculate_session_volume()
