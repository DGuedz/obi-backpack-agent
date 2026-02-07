#  Backpack Commander: Manual de Operações

Bem-vindo ao sistema de trading quantitativo **Backpack Commander**. Este terminal foi desenhado para maximizar Yield (Basis Trade) e Volume (Airdrop) na Backpack Exchange, com segurança institucional.

##  Inicialização Rápida (T-Minus 10s)

1. **Configuração de Chaves**
   Crie um arquivo `.env` na raiz e insira suas chaves (API Key + Secret) geradas na Backpack.
   ```bash
   cp .env.example .env
   # Edite com suas chaves reais
   ```

2. **Lançar o Dashboard (Centro de Comando)**
   Abra o terminal e execute:
   ```bash
   ./venv/bin/streamlit run dashboard.py
   ```
   Isso abrirá a interface visual no seu navegador.

---

##  Modos de Operação

### 1. Radar de Assimetria (Dashboard)
Use a tabela visual para identificar oportunidades:
- ** Yield:** Ativos pagando juros altos (Funding + Lending). Ideal para **Basis Trade**.
- ** Liquidez:** Barras verdes cheias indicam alto volume. Ideal para **Airdrop Farming**.
- **️ Utilização:** Barras vermelhas indicam pool cheio (risco de liquidez).

### 2. AI Advisor (Piloto Automático)
No chat do Dashboard, pergunte:
> *"Qual o melhor farm agora?"*
O Advisor analisará os dados e fornecerá o comando exato de execução.

### 3. Execução (Terminal)
Copie o comando gerado pelo Advisor e cole em um novo terminal para iniciar o bot:
```bash
# Exemplo de Comando Gerado
python main.py --symbol SOL_USDC --risk 0.015
```

---

## ️ Protocolos de Segurança

- **Stop Loss Dinâmico:** O bot encerra posições automaticamente se a estrutura de mercado reverter.
- **Reject Taker:** Evita execução contra si mesmo (Wash Trading) para economizar taxas.
- **Gestão de Risco:** O parâmetro `--risk 0.015` limita a perda máxima por operação a 1.5% do saldo.

**Status:** `OPERATIONAL` | **Versão:** `2.0 (Stealth)`
