import os
import glob
import re

def system_integrity_scan():
    print("\n️‍️ [SYSTEM INTEGRITY SCAN] DEEP CODEBASE AUDIT")
    print("==================================================")
    
    # 1. Scan for Suspicious Symbols (Missing _PERP)
    print("    1. Scanning for SPOT Symbols in Configs...")
    
    py_files = glob.glob("*.py")
    
    spot_pattern = re.compile(r'SYMBOL\s*=\s*["\']([A-Z]+)_USDC["\']') # Matches BTC_USDC but not BTC_USDC_PERP
    perp_pattern = re.compile(r'SYMBOL\s*=\s*["\']([A-Z]+)_USDC_PERP["\']')
    
    found_issues = 0
    
    for file in py_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Check for Spot Symbols
                matches = spot_pattern.findall(content)
                for m in matches:
                    print(f"      ️  [RISK] Found SPOT Symbol '{m}_USDC' in {file}")
                    found_issues += 1
                    
                # Check for Hardcoded "Market" orders without Reduce Only
                if "order_type=\"Market\"" in content and "reduce_only=True" not in content:
                    # Ignore hedge/panic scripts which are intentional
                    if "panic" not in file and "hedge" not in file and "emergency" not in file:
                         print(f"      ️  [RISK] Found Unsafe MARKET Order in {file}")
                         found_issues += 1

        except Exception as e:
            print(f"    Error reading {file}: {e}")
            
    if found_issues == 0:
        print("    Symbol Integrity Check Passed. No obvious Spot configs found.")
    else:
        print(f"    Found {found_issues} Potential Integrity Issues.")

    # 2. Check Data Feed Logic
    print("\n    2. Verifying Data Feeds (Klines)...")
    # We want to ensure get_klines is called with PERP symbols
    
    for file in py_files:
        with open(file, 'r') as f:
            content = f.read()
            if "get_klines" in content:
                if "_USDC\"" in content and "_PERP" not in content:
                     print(f"      ️  [DATA RISK] {file} might be fetching SPOT Klines for indicators!")

    # 3. Verify Safety Lock Implementation
    print("\n    3. Verifying Safety Lock in Trade Module...")
    try:
        with open("backpack_trade.py", "r") as f:
            if "SAFETY LOCK" in f.read():
                print("    BackpackTrade Safety Lock is INSTALLED.")
            else:
                print("    BackpackTrade Safety Lock is MISSING!")
    except:
        print("    Could not check backpack_trade.py")

if __name__ == "__main__":
    system_integrity_scan()
