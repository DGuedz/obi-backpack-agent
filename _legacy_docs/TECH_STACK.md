# OBI WORK - ARQUITETURA CIBORGUE FINANCEIRO

Este documento define o *stack* tecnológico cirúrgico para execução do **Protocolo Omega**.
Foco: **Alta Frequência (HFT)**, **Segurança (Iron Dome)** e **Conectividade On-Chain**.

## 1. O Cérebro (Python Quant & HFT)
*Velocidade, precisão matemática e conectividade universal.*

| Biblioteca | Versão Alvo | Finalidade |
| :--- | :--- | :--- |
| **`ccxt`** | Latest | **Universal Adapter**. Conecta o OBI a 100+ exchanges (Binance, Bybit, Backpack) com código unificado. |
| **`pandas`** | Latest | Manipulação de séries temporais financeiras (OHLCV). |
| **`numpy`** | Latest | Cálculos matriciais de alta performance. |
| **`pandas_ta`** | Latest | Indicadores técnicos otimizados (ATR, RSI, Bollinger) em milissegundos. |
| **`vectorbt`** | Latest | Backtesting vetorial ultrarrápido para validação científica de estratégias. |
| **`websockets`** | Latest | Conexão HFT (Streaming) para reação a Flash Crashes. |
| **`asyncio`** | Built-in | Execução assíncrona para concorrência de tarefas. |

## 2. O Coração (Solana & Gatekeeping)
*Conexão blockchain, verificação de licença e ponte de ativos.*

| Biblioteca | Versão Alvo | Finalidade |
| :--- | :--- | :--- |
| **`solders`** | Latest | Primitivos core da Solana (Rust bindings). |
| **`solana`** | Latest | Interação com RPC da Solana (Python wrapper). |
| **Anchor** | Rust (Ext) | Desenvolvimento de contratos inteligentes (OBI Pass). |
| **Helius API** | SaaS | Inteligência On-Chain e Whale Watching. |

## 3. A Interface (Comando & Controle)
*Visualização e Interação.*

| Ferramenta | Tipo | Finalidade |
| :--- | :--- | :--- |
| **`streamlit`** | Python Lib | **Dashboard Tático**. Interface web visual (Dark Mode) rápida. |
| **Next.js** | Framework | **Solana Actions (Blinks)** para venda de licenças e Marketing. |

## 4. O Escudo (Segurança & Infraestrutura)
*Protocolo Iron Dome.*

| Ferramenta | Tipo | Finalidade |
| :--- | :--- | :--- |
| **`python-dotenv`** | Python Lib | Isolamento de chaves (API/Private Keys) em `.env`. |
| **VPS** | Infra | Ambiente de execução isolado (Ubuntu Linux). |

---

### Instalação

```bash
pip install -r requirements.txt
```
