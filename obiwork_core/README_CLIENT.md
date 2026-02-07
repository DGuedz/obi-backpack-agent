#  OBIWORK Core (Clone #01)

Bem-vindo ao **OBIWORK Core**, seu sistema de trading institucional automatizado para a Backpack Exchange.

##  Instalação Rápida

1. **Requisitos**: Python 3.8+ instalado.
2. **Instalar Dependências**:
   ```bash
   pip install -r requirements.txt
   # Ou se preferir usar o setup.py:
   pip install -e .
   ```

3. **Configuração (.env)**:
   Crie um arquivo `.env` na raiz (baseado no `.env.example` se houver) com suas chaves API:
   ```env
   BACKPACK_API_KEY=sua_chave_publica
   BACKPACK_API_SECRET=sua_chave_privada
   ```

##  Como Usar

O comando principal é o `volume_farmer.py` localizado em `tools/`.

### 1. Modo Seguro (Simulação)
Para testar sem usar dinheiro real (Dry Run):
```bash
python tools/volume_farmer.py --dry-run
```

### 2. Modo Surf (Recomendado)
Para surfar tendências com proteção OBI (Stop Loss curto, Take Profit longo):
```bash
python tools/volume_farmer.py --mode surf --direction auto
```

### 3. Modo Farm (Volume)
Para gerar volume com execução neutra (Delta Neutral tentado):
```bash
python tools/volume_farmer.py --mode straddle
```

## ️ Segurança

- **Stop Loss Atômico**: Todas as ordens são protegidas.
- **OBI Guard**: O sistema monitora o fluxo de ordens para evitar entrar contra "baleias".
- **Chaves API**: Suas chaves ficam apenas no seu computador (`.env`). Nunca compartilhe esse arquivo.

##  Estratégia

O bot utiliza o **Order Book Imbalance (OBI)** para identificar a pressão de compra/venda antes que o preço se mova.

- **OBI > 0.25**: Pressão de Compra (Bullish)
- **OBI < -0.25**: Pressão de Venda (Bearish)

---
*Desenvolvido por OBIWORK Labs.*
