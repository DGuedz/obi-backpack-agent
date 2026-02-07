# PLANO DE IMPLEMENTAÇÃO TÉCNICA

## 1. Stack Tecnológica
- **Linguagem:** Python 3.10+
- **Bibliotecas:** `aiohttp` (API), `pandas` (Dados), `pandas-ta` (Indicadores), `rich` (Logs), `python-dotenv` (Segurança).

## 2. Estrutura de Arquivos
- `/core`:
    - `risk_manager.py`: Implementa as Leis da Preservação e Segregação (70/30).
    - `backpack_transport.py`: Wrapper da API com assinatura Ed25519 e rate limiting.
    - `technical_oracle.py`: Calcula OBI, Funding e ATR.
- `/strategies`:
    - `sniper_executor.py`: Lógica de entrada baseada em confluência.
    - `weaver_grid.py`: Lógica de Grid dinâmico (ATR-based).
- `/safety`:
    - `sentinel.py`: Processo de monitoramento e Kill-switch.

## 3. Fluxo de Dados (Data Flow)
1. `backpack_transport` recebe dados via WebSocket.
2. `technical_oracle` processa e emite um `MarketSignal`.
3. `risk_manager` valida o sinal contra o saldo e define o `size`.
4. `sniper_executor` monta o payload atômico (Entry + SL + TP).
5. `backpack_transport` envia a ordem assinada.
