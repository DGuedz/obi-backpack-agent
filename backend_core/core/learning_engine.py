import json
import os
import pandas as pd
import time

class LearningEngine:
    """
     LEARNING ENGINE (Protocolo Chimera)
    Analisa erros passados e ajusta os pesos de risco dinamicamente.
    """
    def __init__(self, memory_file="trade_memory.json", config_file="risk_config.json"):
        self.memory_file = memory_file
        self.config_file = config_file
        
        # Configuração Padrão (Base)
        self.default_config = {
            "min_volume_usd": 10_000_000,
            "max_spread_pct": 0.0015,    # 0.15%
            "min_obi": 0.10,             # 10% Imbalance
            "max_funding_rate": 0.0004,  # 0.04%
            "ema_tolerance_pct": 0.001   # 0.1% tolerância contra tendência (se aplicável)
        }
        
        self._ensure_config_exists()

    def _ensure_config_exists(self):
        if not os.path.exists(self.config_file):
            with open(self.config_file, 'w') as f:
                json.dump(self.default_config, f, indent=4)

    def evolve(self):
        """
        Executa o ciclo de aprendizado (Reinforcement Learning Simplificado).
        """
        if not os.path.exists(self.memory_file):
            return

        try:
            with open(self.memory_file, 'r') as f:
                history = json.load(f)
            
            if not history: return
            
            df = pd.json_normalize(history)
            
            # Verificar se temos trades fechados com resultado
            if 'result.pnl_percent' not in df.columns:
                return

            # Filtrar PERDAS (PnL < 0)
            losses = df[df['result.pnl_percent'] < 0]
            
            if losses.empty:
                print("    [LEARNING] Sem perdas recentes para analisar. Mantendo parâmetros.")
                return
            
            print(f"    [LEARNING] Analisando {len(losses)} perdas para calibração...")
            
            current_config = self._load_config()
            new_config = current_config.copy()
            
            # --- ANÁLISE DE CAUSALIDADE (CORRELAÇÃO DE FALHAS) ---
            
            # 1. Hipótese: Spread Alto causou a perda?
            # Se média do spread nas perdas > spread atual configurado * 0.8 (perto do limite)
            if 'context.spread' in losses.columns:
                avg_loss_spread = losses['context.spread'].mean()
                if avg_loss_spread > current_config['max_spread_pct'] * 0.8:
                    print(f"    Padrão Detectado: Spread médio nas perdas ({avg_loss_spread*100:.3f}%) está alto.")
                    # Ação: Apertar o cinto (Reduzir spread máximo permitido)
                    new_config['max_spread_pct'] = max(0.0005, current_config['max_spread_pct'] * 0.9)
                    print(f"    Ajuste: Max Spread reduzido para {new_config['max_spread_pct']*100:.3f}%")

            # 2. Hipótese: OBI Fraco?
            if 'context.obi' in losses.columns:
                # OBI nas perdas (absoluto)
                avg_loss_obi = losses['context.obi'].abs().mean()
                if avg_loss_obi < current_config['min_obi'] * 1.2: # Se perdemos mesmo com OBI "bom", talvez precise ser MELHOR
                    print(f"    Padrão Detectado: OBI nas perdas ({avg_loss_obi:.2f}) pode ser insuficiente.")
                    new_config['min_obi'] = min(0.3, current_config['min_obi'] * 1.1)
                    print(f"    Ajuste: Min OBI aumentado para {new_config['min_obi']:.2f}")

            # 3. Hipótese: Funding Rate (Taxas comeram o lucro ou contra-fluxo)
            if 'context.funding_rate' in losses.columns:
                # Se Long e Funding Positivo -> Pagou taxa
                # Se Short e Funding Negativo -> Pagou taxa
                # Simplificação: Verificar magnitude do funding nas perdas
                avg_loss_funding = losses['context.funding_rate'].abs().mean()
                if avg_loss_funding > current_config['max_funding_rate'] * 0.8:
                    print(f"    Padrão Detectado: Funding Rate alto nas perdas.")
                    new_config['max_funding_rate'] = max(0.0001, current_config['max_funding_rate'] * 0.9)
                    print(f"    Ajuste: Max Funding reduzido para {new_config['max_funding_rate']*100:.4f}%")

            # Salvar nova configuração se houve mudança
            if new_config != current_config:
                with open(self.config_file, 'w') as f:
                    json.dump(new_config, f, indent=4)
                print("    [EVOLUTION] Parâmetros de Risco Recalibrados com Sucesso.")
            else:
                print("    [LEARNING] Nenhuma correlação óbvia encontrada. Parâmetros mantidos.")

        except Exception as e:
            print(f"   ️ Erro no Learning Engine: {e}")

    def _load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except:
            return self.default_config

if __name__ == "__main__":
    # Teste Manual
    engine = LearningEngine()
    engine.evolve()
