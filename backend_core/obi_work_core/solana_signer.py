import os
import json
import base64
import hashlib
from solders.keypair import Keypair # type: ignore
from solders.pubkey import Pubkey # type: ignore
from solders.transaction import Transaction # type: ignore
from solders.system_program import TransferParams, transfer # type: ignore
from solders.instruction import Instruction, AccountMeta # type: ignore
from solana.rpc.api import Client
from solders.transaction import Transaction

class SolanaSigner:
    """
    OBI WORK CORE - Solana Agent Wallet
    Signs Audit Receipts and publishes them on-chain (Memo or OBI Pass).
    """
    
    def __init__(self, rpc_url: str = "https://api.devnet.solana.com"):
        self.rpc_client = Client(rpc_url)
        self.keypair = self._load_keypair()
        self.wallet_address = str(self.keypair.pubkey())
        print(f"Solana Agent Wallet Loaded: {self.wallet_address}")
        
    def _load_keypair(self) -> Keypair:
        """Loads Keypair from env (Base58 string or Byte Array)."""
        secret = os.getenv("SOLANA_AGENT_PRIVATE_KEY")
        if not secret:
            print("WARNING: SOLANA_AGENT_PRIVATE_KEY not found. Using Ephemeral Keypair (Data will be lost).")
            return Keypair()
            
        try:
            # Try parsing as JSON byte array
            if secret.startswith("[") and secret.endswith("]"):
                import json
                raw = json.loads(secret)
                return Keypair.from_bytes(raw)
            # Try Base64 (Ends with =)
            elif secret.endswith("="):
                import base64
                decoded = base64.b64decode(secret)
                if len(decoded) == 32:
                    return Keypair.from_seed(decoded)
                return Keypair.from_bytes(decoded)
            else:
                # Assume Base58
                return Keypair.from_base58_string(secret)
        except Exception as e:
            print(f"ERROR Loading Keypair: {e}. Generating new one.")
            return Keypair()

    def sign_audit_receipt(self, receipt: dict) -> str:
        """
        Signs the receipt hash locally (Off-Chain Proof).
        Returns the signature as base58 string.
        """
        # 1. Serialize Receipt Deterministically
        serialized = json.dumps(receipt, sort_keys=True).encode()
        
        # 2. Sign
        signature = self.keypair.sign_message(serialized)
        return str(signature)

    def publish_onchain(self, receipt: dict) -> str:
        """
        Publishes the Audit Hash to Solana via Memo Program.
        Returns the Transaction Signature (Explorer Link).
        """
        # 1. Create Receipt Hash
        receipt_str = json.dumps(receipt, sort_keys=True)
        receipt_hash = hashlib.sha256(receipt_str.encode()).hexdigest()
        
        # Memo: "OBI:AUDIT:<HASH>"
        memo_content = f"OBI:AUDIT:{receipt_hash}"
        
        print(f"Publishing Audit Hash: {memo_content}")
        
        try:
            # 2. Build Memo Instruction
            # Memo Program ID: MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcQb
            memo_program_id = Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcQb")
            
            ix = Instruction(
                program_id=memo_program_id,
                accounts=[
                    AccountMeta(pubkey=self.keypair.pubkey(), is_signer=True, is_writable=True)
                ],
                data=memo_content.encode("utf-8")
            )
            
            # 3. Build Transaction
            recent_blockhash = self.rpc_client.get_latest_blockhash().value.blockhash
            
            # Use solders Transaction (new way)
            txn = Transaction.new_signed_with_payer(
                [ix],
                self.keypair.pubkey(),
                [self.keypair],
                recent_blockhash
            )
            
            # 4. Send
            result = self.rpc_client.send_transaction(txn)
            tx_sig = str(result.value)
            print(f" Audit Published! TX: https://explorer.solana.com/tx/{tx_sig}?cluster=devnet")
            return tx_sig
            
        except Exception as e:
            print(f" Failed to publish on-chain: {e}")
            return "failed_tx"

if __name__ == "__main__":
    # Test
    signer = SolanaSigner()
    mock_receipt = {"session": "test", "value": 100}
    sig = signer.sign_audit_receipt(mock_receipt)
    print(f"Off-Chain Signature: {sig}")
    # tx = signer.publish_onchain(mock_receipt) # Uncomment to test with real funds
