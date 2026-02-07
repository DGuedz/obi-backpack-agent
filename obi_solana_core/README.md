# ️ OBI SOLANA CORE

Este diretório contém os componentes **Solana-Native** do projeto OBI WORK, essenciais para a elegibilidade no Colosseum e integração com o ecossistema.

## Estrutura

*   **`gatekeeper/`**: (Python) Módulo "Nervo" que conecta a inteligência off-chain com a validação on-chain. Verifica se o usuário possui o **OBI Pass** antes de liberar os agentes.
*   **`programs/`**: (Rust/Anchor) Contratos inteligentes (Programs) que rodarão na Solana Mainnet.
    *   *ObiPass Program*: Gerencia a emissão e validação das licenças de acesso (Token 2022).
*   **`actions/`**: (Next.js/TS) Implementação de **Solana Blinks** para viralização no Twitter.
*   **`client/`**: Scripts utilitários para interagir com a blockchain.

## Status de Implementação

- [x] Estrutura de Diretórios
- [x] SolanaGatekeeper (Python Skeleton)
- [ ] ObiPass Anchor Program (Rust)
- [ ] Solana Blinks (Actions API)

## Como Usar (Gatekeeper)

```python
from obi_solana_core.gatekeeper.solana_gatekeeper import SolanaGatekeeper

gatekeeper = SolanaGatekeeper()
user_wallet = "SolanaWalletAddress..."

if gatekeeper.check_access(user_wallet):
    print(" Agente Liberado!")
else:
    print(" Compre seu OBI Pass para acessar.")
```
