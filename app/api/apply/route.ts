import { NextResponse } from "next/server";
import path from "node:path";
import { promisify } from "node:util";
import { execFile } from "node:child_process";
import crypto from "node:crypto";
import { promises as fs } from "node:fs";
import Database from "better-sqlite3";

const execFileAsync = promisify(execFile);

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const dbPath = process.env.OBI_APPLICATION_DB_PATH
  ? path.resolve(process.env.OBI_APPLICATION_DB_PATH)
  : path.join(process.cwd(), "backend_core", "db", "obi_applications.sqlite");
let dbInstance: ReturnType<typeof Database> | null = null;

export async function POST(request: Request) {
  let payload: Record<string, unknown> | null = null;
  try {
    payload = await request.json();
  } catch {
    payload = null;
  }

  const walletAddress = typeof payload?.walletAddress === "string" ? payload.walletAddress.trim() : "";
  if (!walletAddress) {
    return NextResponse.json({ ok: false, error: "wallet_required" }, { status: 400 });
  }

  const answers = typeof payload?.answers === "object" && payload.answers !== null ? payload.answers : null;
  const rawAnswers = answers ? (answers as Record<string, unknown>) : {};
  const triage = buildTriage(rawAnswers);
  const applicationRecord = {
    id: crypto.randomUUID(),
    receivedAt: new Date().toISOString(),
    walletAddress,
    userAgent: request.headers.get("user-agent") || "",
    forwardedFor: request.headers.get("x-forwarded-for") || "",
    answers: answers ? sanitizeAnswers(answers as Record<string, unknown>) : {}
  };

  const scriptPath = path.join(process.cwd(), "backend_core/obi_solana_core/gatekeeper/solana_gatekeeper.py");
  try {
    const { stdout } = await execFileAsync("python3", [scriptPath, walletAddress], {
      timeout: 10000,
      maxBuffer: 1024 * 1024
    });
    const gatekeeper = JSON.parse(stdout.trim());
    const persisted = await persistApplication(applicationRecord, gatekeeper);
    const persistedDb = await persistApplicationDb(applicationRecord, gatekeeper);
    const queued = await persistTriage({
      applicationId: applicationRecord.id,
      receivedAt: applicationRecord.receivedAt,
      walletAddress,
      triage,
      status: "pending",
      gatekeeper: {
        allowed: gatekeeper?.allowed ?? null,
        mode: gatekeeper?.mode ?? null
      }
    });
    const queuedDb = await persistTriageDb({
      applicationId: applicationRecord.id,
      receivedAt: applicationRecord.receivedAt,
      walletAddress,
      triage,
      status: "pending",
      gatekeeper: {
        allowed: gatekeeper?.allowed ?? null,
        mode: gatekeeper?.mode ?? null
      }
    });
    const webhookSent = await sendTriageWebhook({
      applicationId: applicationRecord.id,
      walletAddress,
      triage,
      gatekeeper: {
        allowed: gatekeeper?.allowed ?? null,
        mode: gatekeeper?.mode ?? null
      }
    });
    const notificationLogged = await persistInternalNotification({
      applicationId: applicationRecord.id,
      receivedAt: applicationRecord.receivedAt,
      walletAddress,
      triage,
      gatekeeper: {
        allowed: gatekeeper?.allowed ?? null,
        mode: gatekeeper?.mode ?? null
      }
    });
    const notificationSent = await sendInternalWebhook({
      applicationId: applicationRecord.id,
      walletAddress,
      triage,
      gatekeeper: {
        allowed: gatekeeper?.allowed ?? null,
        mode: gatekeeper?.mode ?? null
      }
    });
    await appendAudit({
      event: "apply_submit",
      status: "ok",
      walletAddress,
      applicationId: applicationRecord.id,
      gatekeeper: {
        allowed: gatekeeper?.allowed ?? null,
        mode: gatekeeper?.mode ?? null
      }
    });
    return NextResponse.json({
      ok: true,
      gatekeeper,
      application: {
        received: true,
        persisted,
        persistedDb,
        queued,
        queuedDb,
        webhookSent,
        notificationLogged,
        notificationSent
      }
    });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "gatekeeper_error";
    await appendAudit({
      event: "apply_submit",
      status: "error",
      walletAddress,
      meta: { message }
    });
    return NextResponse.json({ ok: false, error: message }, { status: 500 });
  }
}

function sanitizeAnswers(answers: Record<string, unknown>) {
  const rawName = typeof answers.q1 === "string" ? answers.q1 : "";
  const rawCpf = typeof answers.q2 === "string" ? answers.q2 : "";
  const rawEmail = typeof answers.q4 === "string" ? answers.q4 : "";
  const rawHandle = typeof answers.q5 === "string" ? answers.q5 : "";
  const rawReferral = typeof answers.q9 === "string" ? answers.q9 : "";
  return {
    name: maskValue(rawName),
    cpfHash: hashValue(rawCpf),
    cpfLast4: lastDigits(rawCpf, 4),
    emailHash: hashValue(rawEmail),
    emailDomain: emailDomain(rawEmail),
    handle: maskValue(rawHandle),
    referral: rawReferral.trim()
  };
}

function maskValue(value: string) {
  const cleaned = value.trim();
  if (cleaned.length <= 4) return cleaned;
  return `${cleaned.slice(0, 2)}***${cleaned.slice(-2)}`;
}

function lastDigits(value: string, digits: number) {
  const numeric = value.replace(/\D/g, "");
  if (numeric.length <= digits) return numeric;
  return numeric.slice(-digits);
}

function emailDomain(value: string) {
  const trimmed = value.trim();
  const atIndex = trimmed.indexOf("@");
  if (atIndex === -1) return "";
  return trimmed.slice(atIndex + 1).toLowerCase();
}

function hashValue(value: string) {
  const trimmed = value.trim();
  if (!trimmed) return "";
  return crypto.createHash("sha256").update(trimmed).digest("hex");
}

function buildTriage(answers: Record<string, unknown>) {
  const years = toNumber(answers.q6);
  const capital = toNumber(answers.q7);
  const profile = typeof answers.q8 === "string" ? answers.q8.toLowerCase() : "";
  const referral = typeof answers.q9 === "string" ? answers.q9.trim() : "";
  let score = 0;
  const tags: string[] = [];

  if (years >= 5) {
    score += 20;
    tags.push("senior");
  } else if (years >= 2) {
    score += 12;
    tags.push("mid");
  } else if (years > 0) {
    score += 6;
    tags.push("junior");
  }

  if (capital >= 10000) {
    score += 20;
    tags.push("capital_high");
  } else if (capital >= 5000) {
    score += 15;
    tags.push("capital_mid");
  } else if (capital >= 1000) {
    score += 10;
    tags.push("capital_low");
  }

  if (profile.includes("dev") && profile.includes("trad")) {
    score += 12;
    tags.push("hybrid");
  } else if (profile.includes("dev")) {
    score += 8;
    tags.push("dev");
  } else if (profile.includes("trad")) {
    score += 6;
    tags.push("trader");
  }

  if (referral) {
    score += 4;
    tags.push("referral");
  }

  const tier = score >= 35 ? "priority" : score >= 20 ? "review" : "standard";
  return { score, tier, tags };
}

function toNumber(value: unknown) {
  const numeric = typeof value === "number" ? value : Number.parseFloat(String(value ?? ""));
  return Number.isFinite(numeric) ? numeric : 0;
}

async function persistApplication(applicationRecord: Record<string, unknown>, gatekeeper: Record<string, unknown>) {
  const logDir = path.join(process.cwd(), "backend_core", "logs");
  const logPath = path.join(logDir, "applications.jsonl");
  try {
    await fs.mkdir(logDir, { recursive: true });
    const line = JSON.stringify({
      ...applicationRecord,
      gatekeeper: {
        allowed: gatekeeper?.allowed ?? null,
        mode: gatekeeper?.mode ?? null
      }
    });
    await fs.appendFile(logPath, `${line}\n`, "utf8");
    return true;
  } catch {
    return false;
  }
}

async function persistTriage(record: Record<string, unknown>) {
  const logDir = path.join(process.cwd(), "backend_core", "logs");
  const logPath = path.join(logDir, "triage_queue.jsonl");
  try {
    await fs.mkdir(logDir, { recursive: true });
    await fs.appendFile(logPath, `${JSON.stringify(record)}\n`, "utf8");
    return true;
  } catch {
    return false;
  }
}

async function appendAudit(entry: Record<string, unknown>) {
  const logDir = path.join(process.cwd(), "backend_core", "logs");
  const logPath = path.join(logDir, "audit.jsonl");
  const payload = {
    ts: new Date().toISOString(),
    service: "apply",
    ...entry
  };
  try {
    await fs.mkdir(logDir, { recursive: true });
    await fs.appendFile(logPath, `${JSON.stringify(payload)}\n`, "utf8");
  } catch {
    return;
  }
}

async function persistInternalNotification(record: Record<string, unknown>) {
  const logDir = path.join(process.cwd(), "backend_core", "logs");
  const logPath = path.join(logDir, "internal_notifications.jsonl");
  try {
    await fs.mkdir(logDir, { recursive: true });
    await fs.appendFile(logPath, `${JSON.stringify(record)}\n`, "utf8");
    return true;
  } catch {
    return false;
  }
}

async function sendTriageWebhook(payload: Record<string, unknown>) {
  const webhookUrl = process.env.OBI_TRIAGE_WEBHOOK_URL;
  if (!webhookUrl) return false;
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 3000);
    const res = await fetch(webhookUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal
    });
    clearTimeout(timeout);
    return res.ok;
  } catch {
    return false;
  }
}

async function sendInternalWebhook(payload: Record<string, unknown>) {
  const webhookUrl = process.env.OBI_INTERNAL_WEBHOOK_URL;
  if (!webhookUrl) return false;
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 3000);
    const res = await fetch(webhookUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal
    });
    clearTimeout(timeout);
    return res.ok;
  } catch {
    return false;
  }
}

async function getDb() {
  if (dbInstance) return dbInstance;
  const dbDir = path.dirname(dbPath);
  await fs.mkdir(dbDir, { recursive: true });
  const db = new Database(dbPath);
  db.exec(
    "CREATE TABLE IF NOT EXISTS applications (id TEXT PRIMARY KEY, received_at TEXT, wallet_address TEXT, user_agent TEXT, forwarded_for TEXT, answers_json TEXT, gatekeeper_allowed INTEGER, gatekeeper_mode TEXT, status TEXT)"
  );
  db.exec(
    "CREATE TABLE IF NOT EXISTS triage (application_id TEXT PRIMARY KEY, received_at TEXT, wallet_address TEXT, score INTEGER, tier TEXT, tags_json TEXT, status TEXT, gatekeeper_allowed INTEGER, gatekeeper_mode TEXT)"
  );
  db.exec(
    "CREATE TABLE IF NOT EXISTS triage_status (id INTEGER PRIMARY KEY AUTOINCREMENT, application_id TEXT, status TEXT, reviewer TEXT, updated_at TEXT)"
  );
  db.exec("CREATE INDEX IF NOT EXISTS idx_applications_wallet ON applications(wallet_address)");
  db.exec("CREATE INDEX IF NOT EXISTS idx_triage_status_app ON triage_status(application_id)");
  dbInstance = db;
  return dbInstance;
}

async function persistApplicationDb(applicationRecord: Record<string, unknown>, gatekeeper: Record<string, unknown>) {
  try {
    const db = await getDb();
    const stmt = db.prepare(
      "INSERT OR REPLACE INTO applications (id, received_at, wallet_address, user_agent, forwarded_for, answers_json, gatekeeper_allowed, gatekeeper_mode, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
    );
    stmt.run(
      applicationRecord.id,
      applicationRecord.receivedAt,
      applicationRecord.walletAddress,
      applicationRecord.userAgent,
      applicationRecord.forwardedFor,
      JSON.stringify(applicationRecord.answers ?? {}),
      gatekeeper?.allowed ? 1 : 0,
      gatekeeper?.mode ?? "",
      "pending"
    );
    return true;
  } catch {
    return false;
  }
}

async function persistTriageDb(record: Record<string, unknown>) {
  try {
    const db = await getDb();
    const triage = record.triage as { score?: number; tier?: string; tags?: string[] } | undefined;
    const gatekeeper = record.gatekeeper as { allowed?: boolean; mode?: string } | undefined;
    const stmt = db.prepare(
      "INSERT OR REPLACE INTO triage (application_id, received_at, wallet_address, score, tier, tags_json, status, gatekeeper_allowed, gatekeeper_mode) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
    );
    stmt.run(
      record.applicationId,
      record.receivedAt,
      record.walletAddress,
      triage?.score ?? 0,
      triage?.tier ?? "standard",
      JSON.stringify(triage?.tags ?? []),
      record.status ?? "pending",
      gatekeeper?.allowed ? 1 : 0,
      gatekeeper?.mode ?? ""
    );
    const statusStmt = db.prepare(
      "INSERT INTO triage_status (application_id, status, reviewer, updated_at) VALUES (?, ?, ?, ?)"
    );
    statusStmt.run(record.applicationId, record.status ?? "pending", "apply", new Date().toISOString());
    return true;
  } catch {
    return false;
  }
}
