#  OBI WORK: ESTRATÉGIA COLOSSEUM 2026
## "Agentic Liquidity Infrastructure on Solana"

###  O Veredito
Para vencer o Hackathon, precisamos migrar de "Trading Bot na CEX" para **"Infraestrutura de Agentes On-Chain"**. O código deve "falar" Solana nativamente.

### ️ O Plano de Ajuste (The Pivot)

#### 1. OBI Pass (Substituindo Solidity)
Abandonaremos o contrato EVM. O acesso ao sistema será controlado por um **Token 2022 (SPL Extension)** na Solana.
*   **Tecnologia:** SPL Token 2022 com **Transfer Hooks**.
*   **Por que?** Permite que o token de acesso tenha regras de compliance embutidas (ex: só pode ser transferido se a wallet tiver interagido com o protocolo, ou royalties forçados).
*   **Utilidade:** Quem tem o Token na wallet ganha acesso ao Dashboard e aos Agentes.

#### 2. OBI Blinks (A "Killer Feature")
Usaremos **Solana Actions (Blinks)** para tornar a interação viral.
*   **Funcionalidade:** Um link do Twitter (X) que renderiza um botão "Buy OBI Pass" ou "Copy Alpha Trade".
*   **Fluxo:** O usuário vê o sinal do Agente no Twitter -> Clica em "Executar" -> A carteira Phantom abre -> Transação assinada na Solana.
*   **Impacto:** Isso tira o projeto do "backend obscuro" e coloca na timeline de todo mundo.

#### 3. Arquitetura Híbrida (Agente + On-Chain)
*   **Cérebro (Off-Chain):** Python (Sniper/Scanner) continua rodando na AWS/VPS pela performance.
*   **Coração (On-Chain):** Programa Anchor que gerencia as Licenças e recebe pagamentos em USDC (SPL).
*   **Nervo (Integração):** Agente monitora a blockchain Solana. Se `Wallet A` comprou o passe on-chain -> Agente libera acesso ao Sniper off-chain.

---

###  Roadmap Técnico (7-14 Dias)

#### Fase 1: Solana Program (Anchor)
- [ ] Criar `ObiPass` program (Rust).
- [ ] Implementar mint de licença pagando USDC.
- [ ] Deploy na Devnet.

#### Fase 2: Integração Agente
- [ ] Criar `SolanaGatekeeper` em Python.
- [ ] Agente verifica saldo de token OBI Pass na wallet do usuário antes de rodar estratégias.

#### Fase 3: Blinks (O Diferencial)
- [ ] Criar API Route `/api/actions/buy-license`.
- [ ] Criar `actions.json` para unfurl no Twitter.

---

###  Estrutura de Diretórios Proposta
```
/obi_solana_core/
  ├── programs/          # Código Rust/Anchor
  │   └── obi_pass/
  ├── actions/           # Solana Blinks (Next.js Routes)
  └── client/            # Python Script para ler estado on-chain
```
