# Colosseum Hackathon — Prova da Verdade OBI

Este documento consolida a narrativa oficial, a auditoria ultrafina e as evidências de campo do OBI Agent no Hackathon.

## Status Operacional (Atual)

### 1. Registro e Infra
*   **Agente:** `obi-backpack-agent`
*   **Status:** Active
*   **Heartbeat:** Sincronizado (`tools/colosseum_heartbeat.py`)
*   **Wallet:** AgentWallet configurado (`~/.agentwallet/config.json`)
*   **Assinatura WAPI:** Ajustada para validação correta de assinatura

### 2. Prova da Verdade (Skin in the Game)
*   **Prova on-chain:** Publicada via AgentWallet
*   **Hash do relatório:** `37b2ff414d5eceaaac6d408f1e32faac89fe446df4fa3ee07565e8464d43afc0`
*   **Assinatura:** `87rowg9VPHBuZLqOix1TuLTunBtC5AcBL+upiQ33GXCJlUDqjBmL7DNjhl5RhEoZMLgL/i/l3yLfKYdHnF4lBA==`
*   **Mensagem assinada:** `OBI_VALIDATION:VOL=5385.85:HASH=...`

## Antes do OBI → Depois do OBI (Reta Final S4)

### Antes do OBI (Base de Operação)
*   Execução intensa em mercado hostil, com spread alto e taxas elevadas.
*   Períodos de dump pesado no BTC pressionando o custo operacional.
*   Objetivo de volume agressivo com disciplina de risco.

### Depois do OBI (Validação e Resiliência)
*   Prova pública com hash e assinatura on-chain, selando a veracidade dos resultados.
*   Continuidade sob estresse, mantendo performance mesmo com o mercado contra.
*   Consolidação do OBI como camada de transparência auditável.

## Evidências Reais do Campo (Season 4)

### Reputação e Volume Total
*   **Season 4 Points:** 2.628 (Gold)
*   **Total Volume (Reputation):** 2,272,666.11
*   **Nível Atual:** Level 14
*   **Meta Platina:** Level 15 em 3,200,000.00

### Reputação por Ativo (Snapshots)
*   SOL-PERP: Level 14 (320,000 → 640,000)
*   BTC-PERP: Level 14 (320,000 → 640,000)
*   ETH-PERP: Level 13 (160,000 → 320,000)
*   LIT-PERP: Level 13 (160,000 → 320,000)
*   HYPE-PERP: Level 12 (80,000 → 160,000)
*   PAXG-PERP: Level 11 (40,000 → 80,000)
*   IP-PERP: Level 11 (40,000 → 80,000)
*   BNB-PERP: Level 11 (40,000 → 80,000)
*   SKR-PERP: Level 11 (40,000 → 80,000)
*   SUI-PERP: Level 11 (40,000 → 80,000)
*   APT-PERP: Level 11 (40,000 → 80,000)
*   XRP-PERP: Level 10 (20,000 → 40,000)
*   OG-PERP: Level 10 (20,000 → 40,000)
*   FOGO-PERP: Level 10 (20,000 → 40,000)
*   AVNT-PERP: Level 10 (20,000 → 40,000)
*   DOGE-PERP: Level 9 (10,000 → 20,000)
*   JTO-PERP: Level 9 (10,000 → 20,000)
*   PUMP-PERP: Level 9 (10,000 → 20,000)
*   FLOCK-PERP: Level 9 (10,000 → 20,000)
*   AVAX-PERP: Level 9 (10,000 → 20,000)
*   MON-PERP: Level 9 (10,000 → 20,000)
*   KBONK-PERP: Level 9 (10,000 → 20,000)
*   SEI-PERP: Level 8 (5,000 → 10,000)
*   MNT-PERP: Level 8 (5,000 → 10,000)
*   PENGU-PERP: Level 8 (5,000 → 10,000)
*   JUP-PERP: Level 8 (5,000 → 10,000)
*   W-PERP: Level 8 (5,000 → 10,000)
*   LINEA-PERP: Level 8 (5,000 → 10,000)
*   STABLE-PERP: Level 8 (5,000 → 10,000)
*   CRV-PERP: Level 8 (5,000 → 10,000)
*   WLFI-PERP: Level 8 (5,000 → 10,000)
*   LINK-PERP: Level 8 (5,000 → 10,000)
*   AAVE-PERP: Level 8 (5,000 → 10,000)
*   TAO-PERP: Level 8 (5,000 → 10,000)
*   ZORA-PERP: Level 8 (5,000 → 10,000)

## Auditoria Ultrafina (Tese de Resiliência)
*   Estratégia sob fogo real: dump forte, spreads agressivos e custo de execução elevado.
*   Persistência comprovada com volume real, não simulado, e trilha de auditoria on-chain.
*   “Skin in the game” explícito: custo operacional real para validar o OBI.

## Tokenomics (VSC Prompt Zero)
O modelo econômico do OBI foi desenhado em VSC (Value-Separated Content) para garantir sustentabilidade sem hype.
Arquivo fonte: `tools/obi_tokenomics.vsc`

**Destaques:**
*   **Utilidade Real:** Pagamento por validação e acesso ao VSC Brain.
*   **Anti-Dump:** Vesting de 24 meses para o time.
*   **Burn:** Mecanismo de queima trimestral de taxas.

## Bloqueio Atual: Submissão do Projeto

A API do Hackathon exige **repositório GitHub público válido**.

**Ação necessária:**
1.  Criar um repositório público.
2.  Enviar este código.
3.  Atualizar `tools/project_metadata.json` com o `repoLink`.
4.  Submeter o projeto.

## Submissão (Quando o Repo estiver pronto)

```bash
curl -X POST https://agents.colosseum.com/api/my-project \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d @tools/project_metadata.json
```

## Validação On-Chain (Resumo Técnico)
O script `proof_of_volume.py`:
1.  Busca o histórico de fills da Backpack.
2.  Calcula volume e taxas.
3.  Gera um SHA256 do relatório.
4.  Assina e publica a mensagem na Solana via AgentWallet.
