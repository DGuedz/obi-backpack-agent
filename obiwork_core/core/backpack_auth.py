import time
import base64
from cryptography.hazmat.primitives.asymmetric import ed25519

class BackpackAuth:
    def __init__(self, api_key_base64, private_key_base64):
        self.api_key = api_key_base64
        self.private_key_bytes = base64.b64decode(private_key_base64)
        self.private_key = ed25519.Ed25519PrivateKey.from_private_bytes(self.private_key_bytes)

    def get_headers(self, instruction=None, params=None):
        if params is None:
            params = {}
        
        timestamp = int(time.time() * 1000)
        window = 5000
        
        # 1. Ordenar parâmetros alfabeticamente pela chave
        sorted_keys = sorted(params.keys())
        query_string_parts = []
        for key in sorted_keys:
            value = params[key]
            # Assumindo que os valores devem ser strings simples
            # Para listas ou objetos aninhados, a lógica seria mais complexa.
            
            # CRITICAL FIX: Booleans must be lowercase for signature matching JSON output
            if isinstance(value, bool):
                value = str(value).lower()
                
            query_string_parts.append(f"{key}={value}")
            
        param_string = "&".join(query_string_parts)
        
        # 2. Construir a string de assinatura
        # "The correct instruction type should be prefixed to the signing string."
        if instruction:
            if param_string:
                signature_payload = f"instruction={instruction}&{param_string}"
            else:
                signature_payload = f"instruction={instruction}"
        else:
            signature_payload = param_string
            
        # 3. Adicionar timestamp e window
        if signature_payload:
            signature_payload += f"&timestamp={timestamp}&window={window}"
        else:
            signature_payload = f"timestamp={timestamp}&window={window}"
            
        # 4. Assinar
        signature_bytes = self.private_key.sign(signature_payload.encode('utf-8'))
        signature_base64 = base64.b64encode(signature_bytes).decode('utf-8')
        
        headers = {
            "X-Timestamp": str(timestamp),
            "X-Window": str(window),
            "X-API-Key": self.api_key,
            "X-Signature": signature_base64,
            "Content-Type": "application/json; charset=utf-8"
        }
        
        return headers
