
import os
import sys
import json
from dotenv import load_dotenv

# Configura path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Carrega env vars
load_dotenv()

from core.backpack_transport import BackpackTransport

def execute_prediction():
    transport = BackpackTransport()
    
    print(" OBI PREDICTION EXECUTION TERMINAL")
    print("   Fetching active markets...")
    
    markets = transport.get_prediction_markets()
    if not markets:
        print("    No active markets found.")
        return

    # Flatten the markets to list all tradeable outcomes
    tradeable_assets = []
    index = 1
    
    print("\n AVAILABLE PREDICTION MARKETS:")
    for m in markets:
        title = m.get('title', 'Unknown')
        for pm in m.get('predictionMarkets', []):
            symbol = pm.get('marketSymbol')
            question = pm.get('question')
            price = pm.get('activePrice')
            
            print(f"   [{index}] {symbol}")
            print(f"       Question: {question}")
            print(f"       Last Price: {price}")
            
            tradeable_assets.append({
                "symbol": symbol,
                "question": question,
                "price": price
            })
            index += 1
            
    print("\n EXECUTION INSTRUCTIONS:")
    print("   To trade, enter the NUMBER of the market you want to trade.")
    
    try:
        choice = input("   Select Market ID (or 'q' to quit): ")
        if choice.lower() == 'q': return
        
        selected_idx = int(choice) - 1
        if selected_idx < 0 or selected_idx >= len(tradeable_assets):
            print("    Invalid selection.")
            return
            
        target = tradeable_assets[selected_idx]
        symbol = target['symbol']
        print(f"\n    SELECTED: {symbol}")
        print(f"      Question: {target['question']}")
        print(f"      Current Price: {target['price']}")
        
        # Determine Side (Bid=Buy YES usually, but in prediction markets:)
        # Backpack Predictions are usually Binary Tokens (YES Token).
        # Buying YES = Bid on the Market.
        # Selling YES (or Buying NO) might be different.
        # Assumption: "Bid" buys the outcome displayed.
        
        side = input("   Side (Bid/Ask): ").capitalize()
        if side not in ["Bid", "Ask"]:
            print("    Invalid side. Use Bid (Buy) or Ask (Sell).")
            return
            
        quantity = input("   Quantity (Tokens): ")
        price_limit = input("   Limit Price (e.g. 0.55): ")
        
        confirm = input(f"   ️ CONFIRM ORDER: {side} {quantity}x {symbol} @ {price_limit}? (y/n): ")
        if confirm.lower() != 'y':
            print("    Cancelled.")
            return
            
        print("\n SENDING ORDER...")
        # Execute using standard order endpoint with prediction symbol
        # orderType="Limit" is standard
        res = transport.execute_order(
            symbol=symbol,
            order_type="Limit",
            side=side,
            quantity=quantity,
            price=price_limit,
            time_in_force="GTC"
        )
        
        if res:
            print(f"    ORDER EXECUTED! Response: {res}")
        else:
            print("    ORDER FAILED. Check logs/balance.")
            
    except Exception as e:
        print(f"    Execution Error: {e}")

if __name__ == "__main__":
    execute_prediction()
