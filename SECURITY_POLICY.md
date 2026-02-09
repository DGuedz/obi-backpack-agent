# OBI WORK - SECURITY POLICY (PROTOCOL ZERO)

## 🎯 ZERO TRUST MANDATE
This repository adheres to a strict Zero Trust security model. All contributors must verify compliance before committing.

### 🔴 PROHIBITED (Hard Fail)
- **Hardcoded Secrets**: Never commit API Keys, Private Keys, Mnemonics, or Seeds.
- **Real Examples**: Do not use real keys in `.env.example` or documentation.
- **Environment Files**: Never commit `.env` or `.env.local`.
- **Debug Prints**: Do not print full credentials to console logs (use `***REDACTED***`).

### ✅ ALLOWED (Safe Patterns)
- **Environment Variables**: Use `os.getenv('KEY')` or `process.env.KEY`.
- **Redacted Logs**: Log only the first 4 characters (e.g., `req_...`).
- **Fake Keys**: Use explicitly fake strings (e.g., `your_api_key_here`).

### 🛠️ TOOLS & AUDIT
Run the local security audit before pushing:
```bash
python3 backend_core/tools/security_audit.py
```

### 🚨 INCIDENT RESPONSE
If a key is committed:
1.  **REVOKE** the key immediately at the provider (Backpack, AWS, etc.).
2.  **ROTATE** all dependent services.
3.  **WIPE** the git history (if necessary) or delete the repo and re-clone.
4.  **REPORT** the incident to the core team.

---
*Signed: OBI Security Sentinel*
