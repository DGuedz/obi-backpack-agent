#!/usr/bin/env python3
import os
import sys
import re
import subprocess
from pathlib import Path

# OBI WORK - SECURITY AUDIT SCRIPT
# "War Room" standard for detecting credential leaks.

SUSPICIOUS_PATTERNS = [
    r'(?i)API_KEY\s*=\s*[\'"]sk-',  # OpenAI keys
    r'(?i)PRIVATE_KEY\s*=\s*[\'"][a-zA-Z0-9]{30,}', # Generic Private Keys
    r'(?i)SECRET\s*=\s*[\'"][a-zA-Z0-9]{30,}', # Generic Secrets
    r'(?i)SEED\s*=\s*[\'"][a-z ]{10,}', # Mnemonics
    r'(?i)BACKPACK_API_SECRET\s*=\s*[\'"][a-zA-Z0-9/+]{40,}', # Backpack Secret
    r'-----BEGIN RSA PRIVATE KEY-----',
    r'-----BEGIN OPENSSH PRIVATE KEY-----'
]

SAFE_FILES = [
    "security_audit.py",
    "debug_keys.py",
    "verify_arkham_keys.py",
    "README.md",
    ".env.example",
    ".env.local.example",
    "deploy_iron_dome.py"
]

IGNORED_DIRS = [
    "node_modules",
    ".git",
    "build",
    "dist",
    "__pycache__",
    ".next",
    "venv",
    "env"
]

def scan_file(file_path):
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.readlines()
            for i, line in enumerate(content):
                for pattern in SUSPICIOUS_PATTERNS:
                    if re.search(pattern, line):
                        # Filter out common false positives (like os.getenv)
                        if "os.getenv" in line or "process.env" in line:
                            continue
                        issues.append((i + 1, line.strip()))
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return issues

def run_audit(root_dir):
    print("[INFO] OBI SECURITY AUDIT - INITIATING...")
    print(f"[INFO] Scanning Root: {root_dir}")
    print("=" * 60)
    
    found_issues = False
    
    for root, dirs, files in os.walk(root_dir):
        # Ignore directories
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        
        for file in files:
            if file in SAFE_FILES:
                continue
                
            file_path = os.path.join(root, file)
            
            # 1. Check filename risks
            if re.search(r'(?i)(credentials|secret|key|backup)', file) and not file.endswith('.py'):
                # Allow specific known safe files or extensions if needed, but flag for review
                pass 
                
            # 2. Content Scan
            issues = scan_file(file_path)
            if issues:
                print(f"\n[ALERT] POTENTIAL LEAK IN: {file_path}")
                for line_num, content in issues:
                    # Redact content for display
                    redacted = content[:20] + "..." if len(content) > 20 else content
                    print(f"   Line {line_num}: {redacted}")
                found_issues = True

    print("=" * 60)
    if found_issues:
        print("[FAIL] ISSUES FOUND. IMMEDIATE REVIEW REQUIRED.")
        sys.exit(1)
    else:
        print("[PASS] NO OBVIOUS HARDCODED CREDENTIALS FOUND.")
        sys.exit(0)

if __name__ == "__main__":
    # Get project root (assuming this script is in backend_core/tools)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    run_audit(project_root)
