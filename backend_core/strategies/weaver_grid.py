import logging
import asyncio
import math
from core.technical_oracle import TechnicalOracle

class WeaverGrid:
    """
    ️ WEAVER GRID (The Volume Farmer)
    Estratégia Modular de Geração de Volume para S4 Airdrop.
    
    FILOSOFIA: "Entrada Assimétrica, Saída Cirúrgica."
    
    MODO DE ATAQUE:
    - 3-Bullet Entry: Divide o capital em 3 ordens escalonadas (Limit Maker).
      1. Scout (20%): Testa o nível.
      2. Soldier (30%): Confirma a zona.
      3. Tank (50%): Absorção final.
      
    EQUAÇÃO DE OURO:
    - Target Profit > (EntryFee + ExitFee + Slippage)
    - Foco em Maker Orders (Rebate/Zero Fee) para maximizar o Net PnL.
    """
    def __init__(self, transport, data_client, risk_manager):
        self.transport = transport
        self.data = data_client
        self.risk_manager = risk_manager
        self.oracle = TechnicalOracle(data_client)
        self.logger = logging.getLogger("WeaverGrid")
        
        # Configuração da Equação de Ouro
        self.MAKER_FEE = 0.0003 # 0.03% (Conservador, assumindo Tier baixo inicial)
        self.TAKER_FEE = 0.0008 # 0.08%
        self.MIN_PROFIT_BUFFER = 0.0005 # 0.05% de gordura para garantir lucro real
        
        # Grid Config
        self.GRID_SPREAD = 0.0015 # 0.15% entre as balas
        self.SCALP_TARGET = 0.003 # 0.3% (Alvo curto para girar volume rápido)

    async def execute_modular_attack(self, symbol, total_capital, side="Buy"):
        """
        Executa a estratégia de 3 Balas (Modular Entry).
        """
        try:
            self.logger.info(f"️ INICIANDO ATAQUE MODULAR (WEAVER) em {symbol} | Capital: ${total_capital:.2f}")
            
            # 1. Obter Preço Base (Smart Entry)
            depth = self.data.get_orderbook_depth(symbol)
            if not depth: return
            
            smart_price, reason = self.oracle.get_smart_entry_price(symbol, side)
            if smart_price <= 0:
                # Fallback
                if side == "Buy": smart_price = float(depth['bids'][0][0])
                else: smart_price = float(depth['asks'][0][0])
            
            # 2. Definir Níveis (Subdivisão em 3)
            # Bullet 1: No preço Smart (Aggressive Maker)
            # Bullet 2: 0.15% melhor
            # Bullet 3: 0.30% melhor
            
            if side == "Buy":
                p1 = smart_price
                p2 = smart_price * (1 - self.GRID_SPREAD)
                p3 = smart_price * (1 - (self.GRID_SPREAD * 2))
            else:
                p1 = smart_price
                p2 = smart_price * (1 + self.GRID_SPREAD)
                p3 = smart_price * (1 + (self.GRID_SPREAD * 2))
                
            # 3. Calcular Tamanhos (20/30/50)
            q1 = (total_capital * 0.20) / p1
            q2 = (total_capital * 0.30) / p2
            q3 = (total_capital * 0.50) / p3
            
            # 3.5 Definir STOP LOSS UNIFICADO (Aperto de Stop)
            # O Stop de todas as ordens deve ser abaixo do Tank.
            # Se o Tank falhar, a tese inteira falha.
            # Stop = Tank Price - 0.6% (Dando um respiro leve para volatildade)
            
            if side == "Buy":
                unified_sl_price = p3 * 0.994
            else:
                unified_sl_price = p3 * 1.006
                
            unified_sl_price = self._adjust_price_precision(symbol, unified_sl_price)
            self.logger.info(f"    STOP LOSS UNIFICADO (KILL SWITCH): {unified_sl_price} (Ancorado no Tank)")
            
            bullets = [
                {"price": p1, "qty": q1, "name": "SCOUT"},
                {"price": p2, "qty": q2, "name": "SOLDIER"},
                {"price": p3, "qty": q3, "name": "TANK"}
            ]
            
            # 4. Validar Equação de Ouro (Simulação)
            # Se entrarmos e sairmos, pagamos as taxas?
            # Custo Entrada (Maker) + Custo Saída (Taker - pior caso)
            total_cost_pct = self.MAKER_FEE + self.TAKER_FEE
            required_move = total_cost_pct + self.MIN_PROFIT_BUFFER
            
            self.logger.info(f"   ️ EQUAÇÃO DE OURO: Custo Est. {total_cost_pct*100:.2f}% | Alvo Mínimo {required_move*100:.2f}%")
            
            if self.SCALP_TARGET < required_move:
                self.logger.warning(f"   ️ ALERTA: Alvo ({self.SCALP_TARGET*100}%) muito curto para as taxas! Ajustando para {required_move*100:.2f}%")
                # Auto-Adjust Target
                target_roe = required_move
            else:
                target_roe = self.SCALP_TARGET

            # 5. Disparar Ordens (Maker Only - PostOnly)
            for b in bullets:
                qty = self._adjust_precision(symbol, b["qty"])
                price = self._adjust_price_precision(symbol, b["price"])
                
                if qty <= 0: continue
                
                # Payload com SL Unificado
                payload = {
                    "symbol": symbol,
                    "side": "Bid" if side == "Buy" else "Ask",
                    "orderType": "Limit",
                    "quantity": str(qty),
                    "price": str(price),
                    "postOnly": True, # OBRIGATÓRIO PARA VOLUME FARMING
                    "stopLossTriggerPrice": str(unified_sl_price)
                }
                
                self.logger.info(f"       {b['name']} ({qty} @ {price}): Enviando... [SL: {unified_sl_price}]")
                self.transport._send_request("POST", "/api/v1/order", "orderExecute", payload)
                # await asyncio.sleep(0.2) # Evitar rate limit
                
            self.logger.info("   ️ REDE DE VOLUME LANÇADA COM SUCESSO.")

        except Exception as e:
            self.logger.error(f"Erro no WeaverGrid: {e}")

    def _adjust_precision(self, symbol, qty):
        if "BTC" in symbol: return round(qty, 3)
        if "ETH" in symbol: return round(qty, 2)
        if "SOL" in symbol: return round(qty, 1) # SOL aceita 1 casa decimal na qty? Geralmente 2, mas defensivo.
        return round(qty, 1)

    def _adjust_price_precision(self, symbol, price):
        if "BTC" in symbol: return round(price, 1)
        if "ETH" in symbol: return round(price, 2)
        if "SOL" in symbol: return round(price, 2)
        if "HYPE" in symbol: return round(price, 3) # HYPE geralmente tem mais casas
        return round(price, 4)
