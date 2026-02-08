import hashlib
import time
import uuid

class AgentIdentity:
    """
    OBI WORK CORE - Agent Identity Module
    Defines the immutable identity of the executing agent.
    """
    
    VERSION = "4.0.0-core"
    BUILD_CODENAME = "PARTNER_ECOSYSTEM"
    
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.start_time = time.time()
        self.identity_hash = self._generate_identity_hash()
        
    def _generate_identity_hash(self) -> str:
        """Generates a deterministic hash for the agent session based on version and time."""
        raw_string = f"{self.VERSION}:{self.BUILD_CODENAME}:{self.start_time}:{self.session_id}"
        return hashlib.sha256(raw_string.encode()).hexdigest()
    
    def get_identity_receipt(self) -> dict:
        """Returns the audit receipt component for identity."""
        return {
            "agent_version": self.VERSION,
            "build_codename": self.BUILD_CODENAME,
            "session_id": self.session_id,
            "identity_hash": self.identity_hash,
            "timestamp": self.start_time
        }

    def validate_integrity(self) -> bool:
        """Checks if identity is intact (placeholder for deeper integrity checks)."""
        # In a real scenario, this could check code signatures.
        return True

if __name__ == "__main__":
    agent = AgentIdentity()
    print("OBI WORK AGENT IDENTITY")
    print("=======================")
    print(agent.get_identity_receipt())
