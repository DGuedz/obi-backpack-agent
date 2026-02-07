import time
import base64
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

class BackpackAuth:
    def __init__(self, api_key_base64, private_key_base64):
        self.api_key = api_key_base64
        # Add padding if needed for base64 decoding
        padding = len(private_key_base64) % 4
        if padding > 0:
            private_key_base64 += "=" * (4 - padding)
            
        self.private_key_bytes = base64.b64decode(private_key_base64)
        self.private_key = ed25519.Ed25519PrivateKey.from_private_bytes(self.private_key_bytes)
        
        # Verify Key Pair
        public_key = self.private_key.public_key()
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        public_b64 = base64.b64encode(public_bytes).decode()
        
        # Mask keys for logging
        masked_api_key = self.api_key[:6] + "..." + self.api_key[-6:] if self.api_key else "None"
        masked_public = public_b64[:6] + "..." + public_b64[-6:] if public_b64 else "None"
        
        print(f"DEBUG: Configured API Key: {masked_api_key}")
        print(f"DEBUG: Derived Public Key: {masked_public}")
        
        if self.api_key != public_b64:
            print("️ WARNING: API Key does NOT match derived Public Key! Keys are mismatched or format is wrong.")


    def get_headers(self, instruction=None, params=None):
        if params is None:
            params = {}
        
        # Create a copy to not modify original
        params_to_sign = params.copy()
        
        timestamp = int(time.time() * 1000)
        window = 5000
        
        # Add timestamp and window to params for sorting
        params_to_sign['timestamp'] = str(timestamp)
        params_to_sign['window'] = str(window)
        
        # 1. Sort parameters alphabetically by key
        sorted_keys = sorted(params_to_sign.keys())
        query_string_parts = []
        for key in sorted_keys:
            value = params_to_sign[key]
            
            # CRITICAL FIX: Booleans must be lowercase
            if isinstance(value, bool):
                value = str(value).lower()
                
            query_string_parts.append(f"{key}={value}")
            
        param_string = "&".join(query_string_parts)
        
        # 2. Build signature string
        if instruction:
            if param_string:
                signature_payload = f"instruction={instruction}&{param_string}"
            else:
                signature_payload = f"instruction={instruction}"
        else:
            signature_payload = param_string or ""
            
        # 3. Sign
        # print(f"DEBUG SIGNATURE PAYLOAD: {signature_payload}")
        
        signature = self.private_key.sign(signature_payload.encode())
        signature_base64 = base64.b64encode(signature).decode()
        
        headers = {
            "X-API-Key": self.api_key,
            "X-Signature": signature_base64,
            "X-Timestamp": str(timestamp),
            "X-Window": str(window),
            "Content-Type": "application/json; charset=utf-8"
        }
        
        return headers
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
