import os
from typing import Dict, Any, List, Union

class VSCParser:
    """
    Parses VSC (Value-Separated Content) files into a dictionary.
    Strict enforcement of rules defined in vsc_spec.md.
    """
    
    @staticmethod
    def parse_file(file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"VSC file not found: {file_path}")
            
        context = {}
        with open(file_path, 'r') as f:
            lines = f.readlines()
            
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
                
            # Split by first colon OR comma (VSC Standard)
            if ':' in line:
                separator = ':'
            elif ',' in line:
                separator = ','
            else:
                # Log warning in a real system, strict mode ignores or errors
                continue
                
            key, value_raw = line.split(separator, 1)
            key = key.strip()
            value_raw = value_raw.strip()
            
            # Parse Value
            value = VSCParser._parse_value(value_raw)
            
            context[key] = value
            
        return context
    
    @staticmethod
    def _parse_value(value: str) -> Union[str, int, float, bool, List[Any], None]:
        # Handle Boolean
        if value.lower() == 'true':
            return True
        if value.lower() == 'false':
            return False
            
        # Handle Lists [a, b, c]
        if value.startswith('[') and value.endswith(']'):
            content = value[1:-1]
            if not content.strip():
                return []
            items = [VSCParser._parse_value(item.strip()) for item in content.split(',')]
            return items
            
        # Handle Numbers
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
            
        # Handle Undefined/Null
        if value.lower() in ['undefined', 'null', 'none']:
            return None
            
        # Default string
        return value

class ExecutionContextLoader:
    """
    OBI WORK CORE - Execution Context Loader
    Loads human intent via VSC and validates schema.
    """
    
    REQUIRED_KEYS = ['risk_profile', 'assets', 'max_loss_usd']
    
    def __init__(self, vsc_path: str):
        self.vsc_path = vsc_path
        self.context = {}
        self.is_valid = False
        
    def load(self) -> Dict[str, Any]:
        """Loads and validates the context. Raises error if invalid."""
        print(f"Loading Context from: {self.vsc_path}")
        self.context = VSCParser.parse_file(self.vsc_path)
        self._validate_schema()
        self.is_valid = True
        return self.context
        
    def _validate_schema(self):
        """Enforces critical schema rules."""
        missing = [k for k in self.REQUIRED_KEYS if k not in self.context]
        if missing:
            raise ValueError(f"CRITICAL: Missing required VSC keys: {missing}. Execution BLOCKED.")
            
        # Check for undefined critical values
        for k in self.REQUIRED_KEYS:
            if self.context[k] is None:
                 raise ValueError(f"CRITICAL: Key '{k}' is undefined. Execution BLOCKED.")

if __name__ == "__main__":
    # Test stub
    # Create a dummy file for test
    with open("test_context.vsc", "w") as f:
        f.write("# Test Context\nrisk_profile: defensive\nassets: [SOL, BTC]\nmax_loss_usd: 50.0\nallow_short: true")
        
    loader = ExecutionContextLoader("test_context.vsc")
    try:
        ctx = loader.load()
        print("Context Loaded Successfully:")
        print(ctx)
    except Exception as e:
        print(f"Context Load Failed: {e}")
        
    os.remove("test_context.vsc")
