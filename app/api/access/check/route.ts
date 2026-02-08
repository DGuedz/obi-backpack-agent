import { NextResponse } from "next/server";
import path from "node:path";
import { promisify } from "node:util";
import { execFile } from "node:child_process";
import { promises as fs } from "node:fs";
import crypto from "crypto";
import { getDb } from "@/app/lib/db";

const execFileAsync = promisify(execFile);

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function POST(request: Request) {
  const requestId = crypto.randomUUID();
  let payload: Record<string, unknown> | null = null;
  try {
    payload = await request.json();
  } catch {
    payload = null;
  }

  const walletAddress = typeof payload?.walletAddress === "string" ? payload.walletAddress.trim() : "";
  if (!walletAddress) {
    await appendAudit({ event: "access_check", status: "error", error: "wallet_required", requestId });
    return NextResponse.json({ ok: false, error: "wallet_required" }, { status: 400 });
  }

  const scriptPath = path.join(process.cwd(), "backend_core/obi_solana_core/gatekeeper/solana_gatekeeper.py");
  try {
    const { stdout } = await execFileAsync("python3", [scriptPath, walletAddress], {
      timeout: 10000,
      maxBuffer: 1024 * 1024
    });
    const gatekeeper = JSON.parse(stdout.trim());
    const hasLicense = await hasActiveLicense(walletAddress);
    const allowed = Boolean(gatekeeper?.allowed) || hasLicense;
    const response = NextResponse.json({ ok: true, gatekeeper: { ...gatekeeper, allowed } });
    if (allowed) {
      response.cookies.set("obi_access_allowed", "true", {
        httpOnly: true,
        sameSite: "lax",
        secure: process.env.NODE_ENV === "production",
        maxAge: 60 * 60 * 24,
        path: "/"
      });
      response.cookies.set("obi_access_wallet", walletAddress, {
        httpOnly: true,
        sameSite: "lax",
        secure: process.env.NODE_ENV === "production",
        maxAge: 60 * 60 * 24,
        path: "/"
      });
    }
    await appendAudit({
      event: "access_check",
      status: "ok",
      walletAddress,
      gatekeeper: {
        allowed: gatekeeper?.allowed ?? null,
        mode: gatekeeper?.mode ?? null
      },
      license: hasLicense,
      requestId
    });
    return response;
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "gatekeeper_error";
    await appendAudit({
      event: "access_check",
      status: "error",
      walletAddress,
      meta: { message },
      requestId
    });
    return NextResponse.json({ ok: false, error: message }, { status: 500 });
  }
}

async function hasActiveLicense(walletAddress: string) {
  try {
    const db = await getDb();
    const row = db
      .prepare("SELECT status FROM licenses WHERE wallet_address = ? ORDER BY issued_at DESC LIMIT 1")
      .get(walletAddress) as { status?: string } | undefined;
    return row?.status === "active";
  } catch {
    return false;
  }
}

async function appendAudit(entry: Record<string, unknown>) {
  const logDir = path.join(process.cwd(), "backend_core", "logs");
  const logPath = path.join(logDir, "audit.jsonl");
  const payload = {
    ts: new Date().toISOString(),
    service: "access",
    ...entry
  };
  try {
    await fs.mkdir(logDir, { recursive: true });
    await fs.appendFile(logPath, `${JSON.stringify(payload)}\n`, "utf8");
  } catch {
    return;
  }
}
