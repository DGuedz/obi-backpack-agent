import os
import sys
from colorama import Fore, Style, init

init(autoreset=True)

def macro_analysis():
    print(f"\n{Style.BRIGHT} OBIWORK STRATEGIC MACRO ANALYSIS (2026) {Style.RESET_ALL}")
    print("=" * 80)
    
    # 1. Geopolítica (Rússia/Ucrânia/EUA) -> Impacto: Risk Off / Flight to Safety
    print(f"\n{Fore.RED} GEOPOLÍTICA (RISCO MÁXIMO):{Style.RESET_ALL}")
    print("   - Conflito Rússia x Ucrânia sem fim à vista e com escalada de ataques.")
    print("   - Trump pressionando OTAN e aliados (incerteza institucional).")
    print("   - Disputa pela Groenlândia (recursos estratégicos).")
    print(f"    {Style.BRIGHT}IMPACTO CRYPTO:{Style.RESET_ALL} Incerteza gera aversão a risco. Baleias movem liquidez para Dólar (USDC/USDT) e Ouro (PAXG).")
    print(f"    {Style.BRIGHT}AÇÃO:{Style.RESET_ALL} BTC sofre pressão vendedora no curto prazo. PAXG pode ser hedge.")

    # 2. Tech (TikTok/EUA) -> Impacto: Soberania de Dados
    print(f"\n{Fore.CYAN} TECH & REGULAÇÃO (TIKTOK):{Style.RESET_ALL}")
    print("   - ByteDance cede controle nos EUA (venda forçada).")
    print(f"    {Style.BRIGHT}IMPACTO CRYPTO:{Style.RESET_ALL} Precedente perigoso para protocolos descentralizados. Reforça narrativa de 'Soberania Bitcoin'.")

    # 3. Brasil (Bolsa Recorde / Dólar R$ 5.28) -> Impacto: Fluxo Emergente
    print(f"\n{Fore.GREEN} BRASIL (FLUXO EMERGENTE):{Style.RESET_ALL}")
    print("   - Ibovespa batendo recordes (+11% em 2026).")
    print("   - Dólar 'baixo' (R$ 5.28) atrai capital estrangeiro buscando yield real.")
    print(f"    {Style.BRIGHT}IMPACTO CRYPTO:{Style.RESET_ALL} Capital gringo entrando no Brasil pode transbordar para cripto via ETFs e corretoras locais.")

    print("\n" + "=" * 80)
    print(f"{Style.BRIGHT} VEREDITO TÁTICO OBIWORK:{Style.RESET_ALL}")
    print("1. O mercado global está em modo **'Risk Off'** devido à guerra.")
    print("2. O **Dólar** está se fortalecendo como refúgio global.")
    print("3. Nossa posição em **ETH** (Long) é contrária ao macro (arriscada), mas técnica (oversold).")
    print("4. **Monitorar PAXG (Ouro Tokenizado)**: Se o medo aumentar, ele vai subir.")
    print("=" * 80)

if __name__ == "__main__":
    macro_analysis()
