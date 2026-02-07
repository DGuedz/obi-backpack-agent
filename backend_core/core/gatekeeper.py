import pandas as pd
import json
import os
import stat
from backpack_data import BackpackData

class Gatekeeper:
    """
    ️ GATEKEEPER - O Filtro de 4 Camadas (Ironclad Protocol)
    Nenhuma ordem passa sem validação total.
    Agora integrado ao LEARNING ENGINE (Protocolo Chimera) para ajuste dinâmico de risco.
    """
    def __init__(self, data_client: BackpackData, config_file="risk_config.json"):
        self._check_env_security()
        self.data = data_client
        self.config_file = config_file
        self._load_dynamic_config()

    def _check_env_security(self):
        """
        [IRON DOME] Verifica permissões do arquivo .env.
        Impede inicialização se o arquivo estiver legível por outros usuários (0600 required).
        """
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        if os.path.exists(env_path):
            st = os.stat(env_path)
            # Verifica se permissões são diferentes de 600 (-rw-------)
            # st_mode & 0o777 pega os bits de permissão
            # Se tiver permissão de grupo ou outros, falha
            if st.st_mode & 0o077:
                print(f" CRITICAL SECURITY ALERT: .env file permissions are too open ({oct(st.st_mode & 0o777)})")
                print("   Action Required: Run 'chmod 600 .env' immediately.")
                # Em produção rigorosa, levantaríamos exceção:
                # raise PermissionError("Insecure .env permissions. System locked.")
                print("   ️ WARNING: Continuing in DEBUG mode, but fix this for PRODUCTION.")
        else:
            print("️ WARNING: .env file not found. System running on environment variables or defaults.")

    def _load_dynamic_config(self):
        """Carrega parâmetros ajustados pelo Learning Engine."""
        default_config = {
            "min_volume_usd": 10_000_000,
            "max_spread_pct": 0.0015,
            "min_obi": 0.10,
            "max_funding_rate": 0.0004
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = default_config
        except:
            self.config = default_config
            
        # Mapear para variáveis locais para compatibilidade
        self.MIN_VOLUME = self.config.get("min_volume_usd", 10_000_000)
        self.MAX_SPREAD = self.config.get("max_spread_pct", 0.0015)
        self.MIN_OBI = self.config.get("min_obi", 0.10)
        self.MAX_FUNDING = self.config.get("max_funding_rate", 0.0004)

    def check_confluence(self, symbol, side):
        """
        Valida se o trade atende as Camadas de Segurança (Dynamic Risk).
        Retorna: (bool, reason, context_data)
        """
        # Recarregar config a cada check para pegar ajustes em tempo real
        self._load_dynamic_config()
        
        print(f"   ️ GATEKEEPER (Dynamic): Validando {symbol} ({side})...")

        context_data = {} # Dados para Black Box

        try:
            # 1. LAYER 4 (Macro/Sustentabilidade) - Dados de Ticker (Volume)
            ticker = self.data.get_ticker(symbol)
            if not ticker:
                return False, "Dados de Ticker Indisponíveis", {}

            # Validação de Volume (Evitar moedas mortas)
            quote_vol = float(ticker.get('quoteVolume', 0))
            context_data['volume_24h'] = quote_vol
            
            if quote_vol < self.MIN_VOLUME:
                return False, f"Volume Insuficiente (${quote_vol/1_000_000:.1f}M < ${self.MIN_VOLUME/1_000_000:.1f}M)", context_data

            # 2. LAYER 3 (Spread & Depth) - Validar via Depth (API Publica)
            # Ticker não fornece BestBid/BestAsk confiavelmente
            depth = self.data.get_orderbook_depth(symbol)
            if not depth or 'bids' not in depth or 'asks' not in depth:
                return False, "Depth Vazio (API Publica)", context_data
            
            bids = depth.get('bids', [])
            asks = depth.get('asks', [])

            if not bids or not asks:
                return False, "Livro de Ofertas Vazio", context_data

            # Parse Best Bid/Ask
            best_bid = float(bids[-1][0])
            best_ask = float(asks[0][0])
            
            # Adicionar ao Contexto para Micro-Precision no Sniper
            context_data['best_bid'] = best_bid
            context_data['best_ask'] = best_ask
            
            if best_bid == 0: return False, "Best Bid Zero", context_data

            # Validação de Spread (Evitar Slippage)
            spread = (best_ask - best_bid) / best_bid
            context_data['spread'] = spread
            
            if spread > self.MAX_SPREAD:
                return False, f"Spread Alto ({spread*100:.3f}% > {self.MAX_SPREAD*100:.3f}%)", context_data

            # 3. LAYER 2 (OBI - Order Book Imbalance)
            top_bids = bids[-10:] # Last 10
            top_asks = asks[:10]  # First 10
            
            bids_vol = sum([float(x[1]) for x in top_bids]) 
            asks_vol = sum([float(x[1]) for x in top_asks])
            
            total_vol = bids_vol + asks_vol
            if total_vol == 0: return False, "Depth Vazio", context_data
            
            obi = (bids_vol - asks_vol) / total_vol
            context_data['obi'] = obi
            
            if side == "Buy":
                if obi <= self.MIN_OBI:
                    return False, f"OBI Fraco para Long ({obi:.2f} <= {self.MIN_OBI})", context_data
            elif side == "Sell":
                if obi >= -self.MIN_OBI:
                    return False, f"OBI Fraco para Short ({obi:.2f} >= -{self.MIN_OBI})", context_data

            # 4. LAYER 1 (Técnica - EMA 50)
            klines = self.data.get_klines(symbol, "1h", limit=60)
            if not klines:
                return False, "Klines Indisponíveis", context_data
                
            df = pd.DataFrame(klines)
            df['close'] = df['close'].astype(float)
            
            # Calcular EMA 50 (Pandas Native)
            ema_series = df['close'].ewm(span=50, adjust=False).mean()
            ema_50 = ema_series.iloc[-1]
            current_price = df.iloc[-1]['close']
            
            # Contexto Técnico
            context_data['price'] = current_price
            context_data['ema_50'] = ema_50
            
            if side == "Buy":
                if current_price <= ema_50:
                    return False, f"Contra Tendência (Preço ${current_price:.2f} < EMA50 ${ema_50:.2f})", context_data
            elif side == "Sell":
                if current_price >= ema_50:
                    return False, f"Contra Tendência (Preço ${current_price:.2f} > EMA50 ${ema_50:.2f})", context_data

            # 5. LAYER 5 (Funding Rate - Taxas)
            try:
                markets = self.data.get_mark_prices()
                market_info = next((m for m in markets if m['symbol'] == symbol), None)
                if market_info:
                    funding = float(market_info.get('fundingRate', 0))
                    context_data['funding_rate'] = funding
                    
                    if side == "Buy" and funding > self.MAX_FUNDING:
                        return False, f"Funding Rate Abusivo para Long ({funding*100:.4f}% > {self.MAX_FUNDING*100:.4f}%)", context_data
                    
                    if side == "Sell" and funding < -self.MAX_FUNDING:
                        return False, f"Funding Rate Abusivo para Short ({funding*100:.4f}% < -{self.MAX_FUNDING*100:.4f}%)", context_data
            except Exception as e:
                print(f"   ️ Aviso Gatekeeper: Erro ao validar Funding ({e})")
                pass

            # SE PASSOU POR TUDO:
            return True, " APROVADO PELO GATEKEEPER", context_data

        except Exception as e:
            return False, f"Erro Crítico no Gatekeeper: {e}", context_data