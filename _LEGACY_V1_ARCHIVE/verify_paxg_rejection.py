from pre_flight_checklist import UltimateChecklist

def verify_paxg():
    symbol = "PAXG_USDC_PERP"
    print(f" POST-MORTEM FORENSE EM {symbol}...")
    
    # Simular Short (que era a ideia original)
    checklist = UltimateChecklist(symbol)
    
    # Testar Short com 20x ( conservador para Gold)
    print("\n--- TESTANDO SHORT (20x) ---")
    approved, result = checklist.run_full_scan("Sell", 20)
    
    if not approved:
        print(f"\n RESULTADO: BLOQUEADO\nMOTIVO: {result}")
    else:
        print(f"\n RESULTADO: APROVADO\n{result}")

    # Testar Long com 20x (só para ver)
    print("\n--- TESTANDO LONG (20x) ---")
    approved, result = checklist.run_full_scan("Buy", 20)
    
    if not approved:
        print(f"\n RESULTADO: BLOQUEADO\nMOTIVO: {result}")
    else:
        print(f"\n RESULTADO: APROVADO\n{result}")

if __name__ == "__main__":
    verify_paxg()
