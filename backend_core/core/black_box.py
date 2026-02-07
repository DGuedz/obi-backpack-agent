import json
import time
import os
from datetime import datetime

class BlackBox:
    """
     BLACK BOX RECORDER (Memória Contextual)
    Grava o "DNA" do mercado no momento da entrada para aprendizado futuro.
    """
    def __init__(self, filename="trade_memory.json"):
        self.filename = filename
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.filename):
            with open(self.filename, 'w') as f:
                json.dump([], f)

    def record_entry_context(self, trade_id, symbol, side, context_data):
        """
        Grava o snapshot do mercado no momento da entrada.
        context_data: dict com RSI, OBI, Spread, Funding, Volatilidade.
        """
        entry_record = {
            "id": trade_id,
            "timestamp": int(time.time()),
            "human_time": datetime.now().isoformat(),
            "symbol": symbol,
            "side": side,
            "status": "OPEN",
            "context": context_data,
            "result": None
        }
        
        self._append_to_log(entry_record)
        print(f"    [BLACK BOX] Contexto Gravado para {trade_id}")

    def update_result(self, trade_id, pnl_percent, exit_reason, exit_price):
        """
        Atualiza o trade com o resultado final.
        """
        try:
            with open(self.filename, 'r') as f:
                history = json.load(f)
            
            updated = False
            for trade in history:
                if trade['id'] == trade_id:
                    trade['status'] = "CLOSED"
                    trade['result'] = {
                        "pnl_percent": pnl_percent,
                        "exit_reason": exit_reason,
                        "exit_price": exit_price,
                        "exit_time": datetime.now().isoformat()
                    }
                    updated = True
                    break
            
            if updated:
                with open(self.filename, 'w') as f:
                    json.dump(history, f, indent=4)
                print(f"    [BLACK BOX] Resultado Atualizado para {trade_id}: {pnl_percent}% ({exit_reason})")
            else:
                print(f"   ️ [BLACK BOX] Trade ID {trade_id} não encontrado para atualização.")
                
        except Exception as e:
            print(f"   ️ Erro ao atualizar Black Box: {e}")

    def _append_to_log(self, data):
        try:
            with open(self.filename, 'r') as f:
                history = json.load(f)
            
            history.append(data)
            
            # Manter histórico limpo (últimos 1000 trades)
            if len(history) > 1000:
                history = history[-1000:]
                
            with open(self.filename, 'w') as f:
                json.dump(history, f, indent=4)
        except Exception as e:
            print(f"   ️ Erro ao gravar na Black Box: {e}")
