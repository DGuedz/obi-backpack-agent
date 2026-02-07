# SHIELD PROTOCOL: THE IRON GATE ️

## 1. A Narrativa: "Proteção Primeiro, Comunidade Depois"
Na Web3, a "comunidade" é frequentemente um vetor de ataque (Sybil, Spammers, Scammers). Para proteger o núcleo (Nós/Core) e os membros legítimos, invertemos a lógica tradicional:
**"Ninguém entra até provar que não é uma ameaça."**

Este não é apenas um KYC. É um **Protocolo de Blindagem de Reputação**.
Utilizamos criptografia (Merkle Trees) para garantir que a privacidade dos usuários aprovados seja mantida on-chain, enquanto o processamento pesado de verificação ocorre off-chain em nossa "Sala de Guerra" (Gatekeeper).

## 2. Arquitetura do Sistema

### Camada 1: O Form de Inscrição (Frontend)
- **Input:** Usuário conecta carteira + Preenche dados mínimos.
- **Armazenamento:** Supabase (Criptografado). Nada sensível vai on-chain.

### Camada 2: O Gatekeeper (Python/Node Engine)
O motor de análise que roda em nosso servidor seguro.
1.  **Varredura de Criação:** Identifica todos os tokens/contratos que a carteira criou.
2.  **Auditoria Cruzada (RugCheck Integration):**
    - Para cada token criado pelo usuário, consultamos a API `api.rugcheck.xyz`.
    - Se o usuário criou tokens marcados como "Danger" ou "Rug", ele é banido automaticamente.
3.  **Cálculo de Score:** 0 a 100.
    - Score > 80: Whitelist.
    - Score < 40: Blacklist.

### Camada 3: O Contrato Blindado (On-Chain)
- **Tecnologia:** Merkle Tree (Árvore de Merkle).
- **Custo:** Zero de Gas por usuário. Pagamos apenas para atualizar a "Raiz" (Root) do contrato uma vez por dia.
- **Privacidade:** O contrato contém apenas um Hash (ex: `0x5d...`). Ninguém sabe quem está na lista olhando o contrato, apenas quem tem a "Prova" (o usuário aprovado).

## 3. Viabilidade Econômica (RugCheck API)
- **Status:** A API da RugCheck é focada em *Tokens*, mas é vital para verificar a *idoneidade* de um usuário (checando o que ele criou).
- **Custo:** Gratuito para uso moderado (Rate Limited).
- **Escalabilidade:** Para alta demanda, pode ser necessário IP Rotation ou parceria, mas para o início (Bootstrap), o custo é **ZERO**.

## 4. Stack Tecnológico
- **Linguagem:** Python (Script de Análise).
- **Bibliotecas:** `requests` (API), `solders` (Solana Keys), `merkletreejs` (Logic).
- **Banco de Dados:** Supabase.
