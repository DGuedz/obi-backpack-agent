import argparse
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))

from core.backpack_transport import BackpackTransport

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--symbol', required=True)
    parser.add_argument('--side', required=True, choices=['Bid', 'Ask'])
    parser.add_argument('--price', required=True)
    parser.add_argument('--qty', required=True)
    args = parser.parse_args()
    
    load_dotenv()
    transport = BackpackTransport()
    
    print(f" EXECUTING DIRECT ORDER: {args.side} {args.qty}x {args.symbol} @ {args.price}")
    
    res = transport.execute_order(
        symbol=args.symbol,
        order_type="Limit",
        side=args.side,
        quantity=args.qty,
        price=args.price,
        time_in_force="GTC"
    )
    
    if res:
        print(f" SUCCESS: {res}")
    else:
        print(" FAILED.")

if __name__ == "__main__":
    main()
