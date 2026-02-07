# OBI Work Contracts

## OBIWorkLicense.sol

Contrato inteligente para venda de licenças OBI Work (NFTs).

### Funcionalidades
- **Pagamento em USDC**: Preços fixos em USDC (6 decimais).
- **NFT Access**: O NFT serve como chave de acesso (Gatekeeper).
- **Tiers**: Suporte a múltiplos níveis (Clone #02, #05).
- **Soulbound (Opcional)**: Pode ser configurado para não permitir transferências.

### Deploy
1. Configure as variáveis de ambiente (chave privada, RPC).
2. Execute o script de deploy (usando Hardhat ou Foundry).
3. Argumento do Construtor: Endereço do contrato USDC na rede alvo.

```solidity
constructor(address _usdcTokenAddress)
```

### Verificação
Após deploy, verifique o contrato no Etherscan/Snowtrace para permitir interação via frontend.
