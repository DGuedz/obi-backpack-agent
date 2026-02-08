import { NextResponse } from 'next/server';
import { execFile } from 'child_process';
import util from 'util';
import path from 'path';
import fs from 'fs';

const execFilePromise = util.promisify(execFile);
const ALLOWED = new Set(['/scan', '/track', '/watchlist', '/whales', '/activity', '/market']);
const ipCounters = new Map<string, { count: number; resetAt: number }>();
const walletCounters = new Map<string, { count: number; resetAt: number }>();
const PER_IP = { limit: 10, windowMs: 60000 };
const PER_WALLET = { limit: 5, windowMs: 60000 };

export async function POST(req: Request) {
  try {
    const payload = await safeJson(req);
    const command = typeof payload?.message === "string" ? payload.message.trim() : "";
    if (!command || command.length > 200) {
      return NextResponse.json({ message: "Invalid command.", type: "alert" }, { status: 400 });
    }
    if (!command.startsWith('/')) {
      return NextResponse.json({ message: "Command not allowed.", type: "alert", code: "not_allowed" }, { status: 400 });
    }
    const base = command.split(' ')[0];
    if (!ALLOWED.has(base)) {
      await appendAudit({ event: "chat_not_allowed", status: "error", command: base });
      return NextResponse.json({ message: "Command not allowed.", type: "alert", code: "not_allowed" }, { status: 400 });
    }
    const ip = getIp(req);
    const ipCheck = checkRate(ipCounters, ip, PER_IP.limit, PER_IP.windowMs);
    if (!ipCheck.ok) {
      await appendAudit({ event: "chat_rate_limit", status: "error", ip, command: base });
      return NextResponse.json({ message: "Too Many Requests.", type: "alert", code: "rate_limited", retryAfter: ipCheck.retryAfter }, { status: 429 });
    }

    const getScriptPath = (scriptName: string) => {
        return path.resolve(process.cwd(), "..", "obiwork_core", "gatekeeper", scriptName);
    };

    // 1. SCAN COMMAND (Compliance Gate)
    if (command.startsWith("/scan")) {
      const parts = command.split(" ").filter(Boolean);
      if (parts.length < 2) {
        return NextResponse.json({ message: "Usage: /scan <wallet_address>" });
      }
      const wallet = parts[1];
      if (!isValidWallet(wallet)) {
        return NextResponse.json({ message: "Invalid wallet format.", type: "alert" }, { status: 400 });
      }
      const walletCheck = checkRate(walletCounters, wallet, PER_WALLET.limit, PER_WALLET.windowMs);
      if (!walletCheck.ok) {
        await appendAudit({ event: "chat_rate_limit_wallet", status: "error", wallet, command: "/scan" });
        return NextResponse.json({ message: "Too Many Requests.", type: "alert", code: "rate_limited", retryAfter: walletCheck.retryAfter }, { status: 429 });
      }
      const scriptPath = getScriptPath("compliance_gate.py");
      
      try {
        const { stdout } = await execFilePromise("python3", [scriptPath, "--scan", wallet, "--json"], {
          timeout: 8000,
          maxBuffer: 256 * 1024
        });
        const data = JSON.parse(stdout.trim());
        await appendAudit({ event: "chat_scan", status: "ok", wallet });
        return NextResponse.json({
          message: `Analysis complete for ${wallet}`,
          type: "analysis",
          data: data
        });
      } catch {
        await appendAudit({ event: "chat_scan", status: "error", wallet });
        return NextResponse.json({ message: "Scan failed.", type: "alert" });
      }
    }

    // 2. TRACK COMMAND (Wallet Tracker)
    if (command.startsWith("/track")) {
        const parts = command.split(" ").filter(Boolean);
        if (parts.length < 2) {
            return NextResponse.json({ message: "Usage: /track <wallet_address> [label]" });
        }
        const wallet = parts[1];
        if (!isValidWallet(wallet)) {
            return NextResponse.json({ message: "Invalid wallet format.", type: "alert" }, { status: 400 });
        }
        const walletCheck = checkRate(walletCounters, wallet, PER_WALLET.limit, PER_WALLET.windowMs);
        if (!walletCheck.ok) {
          await appendAudit({ event: "chat_rate_limit_wallet", status: "error", wallet, command: "/track" });
          return NextResponse.json({ message: "Too Many Requests.", type: "alert", code: "rate_limited", retryAfter: walletCheck.retryAfter }, { status: 429 });
        }
        const label = parts.slice(2).join(" ").slice(0, 40) || "Ally";
        const scriptPath = getScriptPath("wallet_tracker.py");

        try {
            const { stdout } = await execFilePromise("python3", [scriptPath, "--add", wallet, "--label", label, "--json"], {
              timeout: 8000,
              maxBuffer: 256 * 1024
            });
            const data = JSON.parse(stdout.trim());
            await appendAudit({ event: "chat_track", status: "ok", wallet, label });
            return NextResponse.json({
                message: ` Tracking enabled for ${wallet} (${label})`,
                type: "text",
                data: data
            });
        } catch {
            await appendAudit({ event: "chat_track", status: "error", wallet, label });
            return NextResponse.json({ message: "Failed to track wallet.", type: "alert" });
        }
    }

    // 3. WATCHLIST COMMAND (List tracked)
    if (command.startsWith("/watchlist")) {
        const scriptPath = getScriptPath("wallet_tracker.py");
        try {
            const { stdout } = await execFilePromise("python3", [scriptPath, "--list", "--json"], {
              timeout: 8000,
              maxBuffer: 256 * 1024
            });
            const wallets = JSON.parse(stdout.trim());
            
            if (wallets.length === 0) {
                return NextResponse.json({ message: "Watchlist is empty. Use /track <wallet> to add.", type: "text" });
            }

            let msg = " **WATCHLIST**:\n";
            wallets.forEach((w: { label: string; address: string }) => {
                msg += `- **${w.label}**: \`${w.address.slice(0,6)}...${w.address.slice(-4)}\`\n`;
            });
            
            await appendAudit({ event: "chat_watchlist", status: "ok", count: wallets.length });
            return NextResponse.json({ message: msg, type: "text" });
        } catch {
            await appendAudit({ event: "chat_watchlist", status: "error" });
            return NextResponse.json({ message: "Failed to fetch watchlist.", type: "alert" });
        }
    }

    // 4. WHALES / ACTIVITY COMMAND
    if (command.startsWith("/whales") || command.startsWith("/activity")) {
        const scriptPath = getScriptPath("wallet_tracker.py");
        try {
            const { stdout } = await execFilePromise("python3", [scriptPath, "--check", "--json"], {
              timeout: 8000,
              maxBuffer: 256 * 1024
            });
            const updates = JSON.parse(stdout.trim());
            
            if (updates.length === 0) {
                return NextResponse.json({ message: "No recent activity detected on tracked wallets.", type: "text" });
            }

            let msg = " **ON-CHAIN ACTIVITY**:\n";
            updates.forEach((u: { timestamp: string; label: string; action: string }) => {
                msg += `[${u.timestamp.split("T")[1].split(".")[0]}] **${u.label}**: ${u.action}\n`;
            });
            
            await appendAudit({ event: "chat_activity", status: "ok", count: updates.length });
            return NextResponse.json({ message: msg, type: "text" });
        } catch {
            await appendAudit({ event: "chat_activity", status: "error" });
            return NextResponse.json({ message: "Failed to check activity.", type: "alert" });
        }
    }

    // 5. MARKET COMMAND
    if (command.startsWith("/market")) {
        const reportPath = path.resolve(process.cwd(), "..", "STRATEGIC_REPORT.md");
        if (fs.existsSync(reportPath)) {
            const report = fs.readFileSync(reportPath, "utf-8");
            await appendAudit({ event: "chat_market", status: "ok" });
            return NextResponse.json({
                message: report.substring(0, 500) + "...\n(See full report in dashboard)",
                type: "text"
            });
        }
        await appendAudit({ event: "chat_market", status: "error" });
        return NextResponse.json({ message: "Market report not available." });
    }

    // DEFAULT
    return NextResponse.json({
      message: "Command not recognized. Try:\n- /scan <wallet>\n- /track <wallet> [label]\n- /watchlist\n- /whales\n- /market",
      type: "text"
    });

  } catch {
    await appendAudit({ event: "chat_error", status: "error" });
    return NextResponse.json(
      { error: "Internal Server Error" },
      { status: 500 }
    );
  }
}

async function safeJson(req: Request) {
  try {
    return await req.json();
  } catch {
    return null;
  }
}

function isValidWallet(value: string) {
  return /^[1-9A-HJ-NP-Za-km-z]{32,64}$/.test(value);
}

function getIp(req: Request) {
  const h = req.headers;
  const fwd = h.get('x-forwarded-for') || '';
  const real = h.get('x-real-ip') || '';
  const ip = fwd.split(',')[0].trim() || real.trim() || 'unknown';
  return ip;
}

function checkRate(map: Map<string, { count: number; resetAt: number }>, key: string, limit: number, windowMs: number) {
  const now = Date.now();
  const entry = map.get(key);
  if (!entry || now > entry.resetAt) {
    map.set(key, { count: 1, resetAt: now + windowMs });
    return { ok: true, retryAfter: 0 };
  }
  if (entry.count >= limit) {
    const retryAfter = Math.ceil((entry.resetAt - now) / 1000);
    return { ok: false, retryAfter };
  }
  entry.count += 1;
  map.set(key, entry);
  return { ok: true, retryAfter: 0 };
}

async function appendAudit(entry: Record<string, unknown>) {
  const logDir = path.join(process.cwd(), "backend_core", "logs");
  const logPath = path.join(logDir, "audit.jsonl");
  const payload = {
    ts: new Date().toISOString(),
    service: "chat",
    ...entry
  };
  try {
    fs.mkdirSync(logDir, { recursive: true });
    fs.appendFileSync(logPath, `${JSON.stringify(payload)}\n`, "utf-8");
  } catch {
    return;
  }
}
