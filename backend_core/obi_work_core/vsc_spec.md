# VSC STANDARD SPECIFICATION (v1.0)
# Value-Separated Content - The Nuclear Language of OBI WORK

## 1. PREMISE
VSC is a deterministic, line-based data format designed for autonomous agents.
It eliminates ambiguity by enforcing a strict key-value structure with no nesting complexity.
If a value cannot be resolved to a primitive or a clear list, it is INVALID.

## 2. SYNTAX RULES
1. **Line-Based**: Each line is a single instruction or data point.
2. **Separator**: The colon (`:`) is the primary separator. `key: value`.
3. **Comments**: Lines starting with `#` are ignored.
4. **Booleans**: MUST be `true` or `false` (lowercase). No `0/1` or `yes/no`.
5. **Undefined**: If a value is missing, it is `undefined`.
   - RULE: If a critical field is `undefined`, the Agent MUST BLOCK execution.

## 3. STRUCTURE
```vsc
# Header
version: 1.0
type: execution_context

# Identity
agent_id: obi_v4_core
risk_profile: defensive

# Execution Parameters
max_loss_usd: 10.0
allow_short: true
assets: [SOL, ETH, BTC]

# Integrity
audit_enabled: true
zk_level: high
```

## 4. PARSING LOGIC
- Trim whitespace from both ends.
- Split by first `:`.
- If no `:`, ignore line (unless part of a multiline block, which is discouraged in Core VSC).
- Cast numericals automatically.
- Parse `[a, b, c]` as lists.

## 5. ERROR HANDLING
- **Unknown Key**: Log warning, continue.
- **Invalid Value Type**: Critical Error -> BLOCK.
- **Missing Required Key**: Critical Error -> BLOCK.

## 6. IMMUTABILITY
Once loaded, a VSC Context is immutable during the Execution Loop.
Changes require a full restart of the Context Loader.
