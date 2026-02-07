#!/usr/bin/env python3
"""
 ORCHESTRATOR BRAIN
Sistema Central de Coordenação para o Time de Agentes Autônomos.
Responsável por gerenciar o fluxo de dados entre Backpack (CEX) e CoinMarketCap (Oracle/DEX),
aplicando Rate Limiting adaptativo e Caching inteligente para maximizar a eficiência.
"""

import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from threading import Lock

# Importação dos módulos existentes
try:
    from cmc_oracle import CMCOracle
    from cmc_dex_scanner import CMCDexScanner
    from backpack_data import BackpackData
    from feedback_department import FeedbackDepartment
except ImportError:
    # Fallback para desenvolvimento isolado ou testes
    print("️ Aviso: Módulos de dependência não encontrados. O Orchestrator pode não funcionar completamente.")

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [ORCHESTRATOR] - %(levelname)s - %(message)s'
)

@dataclass
class CacheItem:
    data: Any
    expiry: float

class CacheManager:
    """Gerenciador de Memória de Curto Prazo (Cache)"""
    def __init__(self):
        self._cache: Dict[str, CacheItem] = {}
        self._lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            item = self._cache.get(key)
            if item and item.expiry > time.time():
                return item.data
            elif item:
                del self._cache[key] # Expurgar item vencido
            return None

    def set(self, key: str, data: Any, ttl: int):
        with self._lock:
            self._cache[key] = CacheItem(data=data, expiry=time.time() + ttl)
            
    def clear(self):
        with self._lock:
            self._cache.clear()

class AdaptiveRateLimiter:
    """Controlador de Fluxo para evitar banimento de API (429)"""
    def __init__(self, limit: int, window: int, name: str = "API"):
        self.limit = limit
        self.window = window
        self.name = name
        self.calls = []
        self._lock = Lock()

    def wait_if_needed(self):
        with self._lock:
            now = time.time()
            # Remover chamadas antigas fora da janela
            self.calls = [t for t in self.calls if t > now - self.window]
            
            if len(self.calls) >= self.limit:
                sleep_time = self.calls[0] + self.window - now + 0.1 # Buffer de segurança
                if sleep_time > 0:
                    logging.warning(f"⏳ Rate Limit ({self.name}) atingido. Pausando por {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
            
            self.calls.append(time.time())

class OrchestratorBrain:
    """
    O 'Cérebro' que coordena os agentes e APIs.
    """
    def __init__(self, backpack_data: Any, cmc_oracle: Any, cmc_scanner: Any):
        self.bp_data = backpack_data
        self.cmc_oracle = cmc_oracle
        self.cmc_scanner = cmc_scanner
        
        self.cache = CacheManager()
        self.feedback = FeedbackDepartment() # Departamento de Feedback Integrado
        
        # Limites (Ajustados para segurança)
        # CMC: Cuidado com créditos. 30 requests/minuto é seguro para Hobbyist em bursts curtos.
        self.cmc_limiter = AdaptiveRateLimiter(limit=20, window=60, name="CoinMarketCap")
        
        # Backpack: Alta performance, mas evitamos spam.
        self.bp_limiter = AdaptiveRateLimiter(limit=50, window=10, name="Backpack")

    def get_macro_metrics(self, use_cache=True) -> Optional[Dict]:
        """
        Consulta o Oráculo CMC para obter métricas globais completas.
        Cache TTL: 5 minutos.
        """
        # 0. Consultar Feedback Department (Intel)
        intel = self.feedback.consult_intelligence("CoinMarketCap")
        if intel["risk_level"] == "HIGH":
            logging.warning(" CMC com risco ALTO. Usando Cache ou Fallback.")
            return self.cache.get("macro_metrics")

        cache_key = "macro_metrics"
        if use_cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        self.cmc_limiter.wait_if_needed()
        try:
            metrics = self.cmc_oracle.get_global_metrics()
            if metrics:
                self.cache.set(cache_key, metrics, ttl=300) # 5 min cache
                return metrics
            else:
                self.feedback.report_incident("CoinMarketCap", "EmptyMetrics", "Retorno vazio do Oracle", "WARNING")
        except Exception as e:
            logging.error(f"Erro ao buscar Macro Metrics: {e}")
            self.feedback.report_incident("CoinMarketCap", "Exception", str(e), "CRITICAL")
        
        return None

    def get_macro_sentiment(self, use_cache=True) -> str:
        """Wrapper para manter compatibilidade, mas usa get_macro_metrics"""
        metrics = self.get_macro_metrics(use_cache)
        if metrics:
            return metrics.get('sentiment', 'NEUTRAL')
        return "NEUTRAL"

    def get_consolidated_price(self, symbol: str, token_address: str = None) -> Dict[str, float]:
        """
        Busca preço na CEX (Backpack) e compara com DEX (On-Chain).
        Retorna ambos para arbitragem ou validação.
        """
        # 1. Preço CEX (Rápido, prioridade)
        cex_price = 0.0
        
        # Check Feedback Backpack
        intel_bp = self.feedback.consult_intelligence("Backpack")
        if intel_bp["risk_level"] != "HIGH":
            self.bp_limiter.wait_if_needed()
            try:
                ticker = self.bp_data.get_ticker(symbol)
                cex_price = float(ticker.get('lastPrice', 0))
            except Exception as e:
                logging.error(f"Erro CEX Price: {e}")
                self.feedback.report_incident("Backpack", "PriceFetchError", str(e), "WARNING")
        else:
            logging.warning(" Backpack com risco ALTO. Pulando CEX Price.")

        # 2. Preço DEX (Se endereço fornecido, via CMC Dex Scan)
        dex_price = 0.0
        if token_address:
            # Check Feedback CMC
            intel_cmc = self.feedback.consult_intelligence("CoinMarketCap")
            if intel_cmc["risk_level"] == "HIGH":
                 logging.warning(" CMC com risco ALTO. Pulando DEX Price.")
            else:
                cache_key = f"dex_price_{token_address}"
                cached = self.cache.get(cache_key)
                if cached:
                    dex_price = cached
                else:
                    self.cmc_limiter.wait_if_needed()
                    try:
                        dex_data = self.cmc_scanner.get_dex_pair_latest(token_address=token_address)
                        
                        # Validar se dex_data contém erro reportado pela API
                        if isinstance(dex_data, dict) and "error" in dex_data:
                            self.feedback.report_incident("CoinMarketCap", "APIError", str(dex_data), "CRITICAL")
                        
                        # Parsing dependente da resposta da v4 API (ajustar conforme retorno real)
                        # Assumindo estrutura data -> [0] -> quote -> price
                        elif dex_data and 'data' in dex_data and len(dex_data['data']) > 0:
                            dex_price = float(dex_data['data'][0].get('quote', {}).get('USD', {}).get('price', 0))
                            self.cache.set(cache_key, dex_price, ttl=60) # 1 min cache para on-chain
                    except Exception as e:
                        logging.error(f"Erro DEX Price: {e}")
                        self.feedback.report_incident("CoinMarketCap", "Exception", str(e), "WARNING")

        return {
            "symbol": symbol,
            "cex_price": cex_price,
            "dex_price": dex_price,
            "spread_pct": ((cex_price - dex_price) / dex_price * 100) if dex_price > 0 else 0
        }

    def get_battle_readiness(self) -> Dict[str, Any]:
        """
        Retorna o status de prontidão para batalha (Trading).
        Analisa Macro + Feedback para decidir a postura dos bots.
        """
        readiness = {
            "status": "HOLD",
            "mode": "DEFENSIVE",
            "risk_level": "UNKNOWN",
            "reason": "Initializing"
        }
        
        # 1. Verificar Saúde dos Sistemas (Feedback)
        cmc_health = self.feedback.consult_intelligence("CoinMarketCap")
        bp_health = self.feedback.consult_intelligence("Backpack")
        
        if bp_health["risk_level"] == "HIGH":
            readiness["status"] = "HALT"
            readiness["mode"] = "BUNKER"
            readiness["risk_level"] = "CRITICAL"
            readiness["reason"] = "Backpack API Unstable"
            return readiness
            
        # 2. Verificar Macro (Oracle)
        macro_sentiment = self.get_macro_sentiment()
        
        if cmc_health["risk_level"] == "HIGH":
            # Se CMC está cego, operamos apenas com dados internos (Price Action)
            # Modo Guerrilha: Stops curtos, alvos curtos, sem confirmação macro
            readiness["status"] = "CAUTION"
            readiness["mode"] = "GUERRILLA"
            readiness["risk_level"] = "HIGH"
            readiness["reason"] = "Oracle Blind (CMC Error)"
        else:
            # Sistema Full Operational
            if macro_sentiment == "BULLISH":
                readiness["status"] = "GO"
                readiness["mode"] = "FULL_ASSAULT"
                readiness["risk_level"] = "LOW"
            elif macro_sentiment == "BEARISH":
                readiness["status"] = "GO"
                readiness["mode"] = "SNIPER_SHORT" # Foco em Short
                readiness["risk_level"] = "MEDIUM"
            else:
                readiness["status"] = "GO"
                readiness["mode"] = "SCALP_ONLY" # Mercado lateral
                readiness["risk_level"] = "LOW"
                
        return readiness

    def execute_smart_scan(self, symbols: List[str]):
        """
        Varredura inteligente:
        1. Verifica Macro (Risk On/Off)
        2. Itera sobre símbolos
        3. Valida liquidez
        """
        sentiment = self.get_macro_sentiment()
        logging.info(f"️ Modo de Operação: {sentiment}")
        
        results = []
        for sym in symbols:
            # Exemplo simples de coleta
            self.bp_limiter.wait_if_needed()
            ticker = self.bp_data.get_ticker(sym)
            if ticker:
                results.append({
                    "symbol": sym,
                    "price": ticker.get('lastPrice'),
                    "vol_24h": ticker.get('quoteVolume')
                })
        
        return results

if __name__ == "__main__":
    # Teste de Integração (Mock ou Real se chaves existirem)
    print(" Iniciando Orchestrator Brain...")
    
    # Mock classes for standalone testing if needed, or real ones
    try:
        from backpack_auth import BackpackAuth
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        bp_data = BackpackData(auth)
        cmc_oracle = CMCOracle()
        cmc_scanner = CMCDexScanner()
        
        brain = OrchestratorBrain(bp_data, cmc_oracle, cmc_scanner)
        
        print("\n--- Teste 1: Macro Sentiment ---")
        sent = brain.get_macro_sentiment()
        print(f"Sentimento Atual: {sent}")
        
        print("\n--- Teste 2: Cache Hit ---")
        start = time.time()
        sent_cached = brain.get_macro_sentiment()
        print(f"Sentimento (Cache): {sent_cached} (Tempo: {(time.time() - start)*1000:.2f}ms)")
        
        print("\n--- Teste 3: Consolidated Price (SOL) ---")
        # Token Address SOL (Wrapped SOL on Solana): So11111111111111111111111111111111111111112
        price_data = brain.get_consolidated_price("SOL_USDC", "So11111111111111111111111111111111111111112")
        print(f"Dados Consolidados: {price_data}")
        
    except Exception as e:
        print(f" Erro no Teste: {e}")
