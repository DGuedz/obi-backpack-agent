import logging
import os
import json
import sys
import time
from datetime import datetime
from typing import Optional, Dict
from urllib import request, error

# Placeholder for solana-py imports
# from solana.rpc.api import Client
# from solders.pubkey import Pubkey

class SolanaGatekeeper:
    """
    ️ SOLANA GATEKEEPER
    
    O "Nervo" da arquitetura híbrida. 
    Responsável por verificar on-chain se uma wallet possui o OBI PASS (Token 2022).
    
    Conecta a Inteligência Off-Chain (Python) com a Liquidez On-Chain (Solana).
    """
    
    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        self.rpc_url = os.getenv("OBI_SOLANA_RPC_URL", rpc_url)
        self.logger = logging.getLogger("SolanaGatekeeper")
        
        # Endereço do Token OBI PASS (Será preenchido após deploy do Anchor Program)
        self.OBI_PASS_MINT = os.getenv("OBI_PASS_MINT", "DeployPending...")
        
        self.cache_url = os.getenv("OBI_GATEKEEPER_CACHE_URL", "").strip()
        self.cache_ttl_seconds = int(os.getenv("OBI_GATEKEEPER_CACHE_TTL_SECONDS", "120") or "120")
        self.access_cache: Dict[str, Dict[str, Optional[object]]] = {}
        
    def check_access(self, wallet_address: str) -> bool:
        """
        Verifica se a wallet tem permissão de acesso aos Agentes.
        Regra: Deve possuir pelo menos 1 OBI PASS (Token) ou estar na Whitelist.
        """
        cached = self._get_cached_access(wallet_address)
        if cached is not None:
            return cached
            
        # 2. Check Whitelist (Hardcoded VIPs)
        if self._is_whitelisted(wallet_address):
            self.logger.info(f" Acesso Permitido (Whitelist): {wallet_address}")
            self._set_cached_access(wallet_address, True)
            return True
            
        # 3. Check On-Chain Balance (OBI PASS)
        has_pass = self._verify_onchain_balance(wallet_address)
        
        if has_pass:
            self.logger.info(f" Acesso Permitido (OBI Pass Holder): {wallet_address}")
            self._set_cached_access(wallet_address, True)
            return True
        else:
            self.logger.warning(f" Acesso Negado (Sem OBI Pass): {wallet_address}")
            self._set_cached_access(wallet_address, False)
            return False

    def _is_whitelisted(self, wallet_address: str) -> bool:
        env_list = os.getenv("OBI_GATEKEEPER_WHITELIST", "")
        whitelisted = [item.strip() for item in env_list.split(",") if item.strip()]
        return wallet_address in whitelisted

    def _verify_onchain_balance(self, wallet_address: str) -> bool:
        """
        Consulta RPC Solana para ver saldo do Token 2022.
        """
        if self.OBI_PASS_MINT == "DeployPending..." or not self.OBI_PASS_MINT:
            dev_allow = os.getenv("OBI_GATEKEEPER_DEV_ALLOW", "").lower() in ["1", "true", "yes"]
            if dev_allow:
                self.logger.debug("️ OBI PASS Mint não configurado. Modo Dev: Acesso Liberado.")
                return True
            self.logger.warning("OBI PASS Mint não configurado. Acesso negado.")
            return False
            
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTokenAccountsByOwner",
                "params": [
                    wallet_address,
                    {"mint": self.OBI_PASS_MINT},
                    {"encoding": "jsonParsed"}
                ]
            }
            data = json.dumps(payload).encode("utf-8")
            req = request.Request(self.rpc_url, data=data, headers={"Content-Type": "application/json"})
            with request.urlopen(req, timeout=6) as resp:
                body = resp.read().decode("utf-8")
            response = json.loads(body)
            accounts = response.get("result", {}).get("value", [])
            for account in accounts:
                parsed = (
                    account.get("account", {})
                    .get("data", {})
                    .get("parsed", {})
                    .get("info", {})
                )
                token_amount = parsed.get("tokenAmount", {})
                ui_amount = token_amount.get("uiAmount", 0)
                if ui_amount and ui_amount > 0:
                    return True
            return False
        except error.HTTPError as e:
            if e.code == 429:
                self.logger.error("RPC Solana: 429 Too Many Requests")
                return False
            self.logger.error(f"Erro RPC Solana: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Erro RPC Solana: {e}")
            return False

    def _get_cached_access(self, wallet_address: str) -> Optional[bool]:
        if wallet_address in self.access_cache:
            entry = self.access_cache[wallet_address]
            allowed = entry.get("allowed")
            updated_at = entry.get("updated_at")
            if self._cache_valid(updated_at):
                return bool(allowed)
        external = self._fetch_external_cache(wallet_address)
        if external is None:
            return None
        self.access_cache[wallet_address] = {"allowed": external, "updated_at": datetime.utcnow().isoformat()}
        return external

    def _set_cached_access(self, wallet_address: str, allowed: bool) -> None:
        updated_at = datetime.utcnow().isoformat()
        self.access_cache[wallet_address] = {"allowed": allowed, "updated_at": updated_at}
        self._push_external_cache(wallet_address, allowed, updated_at)

    def _cache_valid(self, updated_at: Optional[object]) -> bool:
        if self.cache_ttl_seconds <= 0:
            return True
        if not updated_at or not isinstance(updated_at, str):
            return False
        try:
            normalized = updated_at.replace("Z", "+00:00")
            ts = datetime.fromisoformat(normalized).timestamp()
            return (time.time() - ts) <= self.cache_ttl_seconds
        except Exception:
            return False

    def _fetch_external_cache(self, wallet_address: str) -> Optional[bool]:
        if not self.cache_url:
            return None
        try:
            url = f"{self.cache_url}?wallet={wallet_address}"
            req = request.Request(url, headers={"Accept": "application/json"})
            with request.urlopen(req, timeout=3) as resp:
                body = resp.read().decode("utf-8")
            data = json.loads(body)
            allowed = data.get("allowed")
            updated_at = data.get("updatedAt") or data.get("updated_at")
            if allowed is None:
                return None
            if updated_at and not self._cache_valid(updated_at):
                return None
            return bool(allowed)
        except Exception:
            return None

    def _push_external_cache(self, wallet_address: str, allowed: bool, updated_at: str) -> None:
        if not self.cache_url:
            return
        try:
            payload = json.dumps({
                "wallet": wallet_address,
                "allowed": allowed,
                "updatedAt": updated_at
            }).encode("utf-8")
            req = request.Request(
                self.cache_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with request.urlopen(req, timeout=3):
                return
        except Exception:
            return

    def get_license_details(self, wallet_address: str) -> dict:
        """
        Retorna metadados da licença (Tier, Validade, etc.)
        Útil para o Agente saber qual nível de agressividade liberar.
        """
        return {
            "tier": "GOLD", # Placeholder
            "features": ["Sniper", "VolumeFarmer", "AlphaHunter"],
            "expiry": "Lifetime"
        }

if __name__ == "__main__":
    wallet = sys.argv[1] if len(sys.argv) > 1 else ""
    gatekeeper = SolanaGatekeeper()
    if not wallet:
        print(json.dumps({"ok": False, "error": "wallet_required"}))
        sys.exit(1)
    allowed = gatekeeper.check_access(wallet)
    details = gatekeeper.get_license_details(wallet) if allowed else None
    dev_allow = os.getenv("OBI_GATEKEEPER_DEV_ALLOW", "").lower() in ["1", "true", "yes"]
    mode = "dev" if (gatekeeper.OBI_PASS_MINT == "DeployPending..." or not gatekeeper.OBI_PASS_MINT) and dev_allow else "onchain"
    print(json.dumps({
        "ok": True,
        "wallet": wallet,
        "allowed": allowed,
        "mode": mode,
        "license": details
    }))
