import { NextResponse } from "next/server";
import path from "node:path";
import { promises as fs } from "node:fs";
import Database from "better-sqlite3";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const dbPath = process.env.OBI_APPLICATION_DB_PATH
  ? path.resolve(process.env.OBI_APPLICATION_DB_PATH)
  : path.join(process.cwd(), "backend_core", "db", "obi_applications.sqlite");
let dbInstance: ReturnType<typeof Database> | null = null;

export async function GET() {
  try {
    const db = await getDb();
    const rows = db
      .prepare(
        "SELECT application_id as applicationId, received_at as receivedAt, wallet_address as walletAddress, score, tier, tags_json as tagsJson, status, gatekeeper_allowed as gatekeeperAllowed, gatekeeper_mode as gatekeeperMode FROM triage ORDER BY received_at DESC"
      )
      .all();
    const items = rows.map((row: Record<string, unknown>) => ({
      applicationId: row.applicationId,
      receivedAt: row.receivedAt,
      walletAddress: row.walletAddress,
      status: row.status,
      triage: {
        score: row.score ?? 0,
        tier: row.tier ?? "standard",
        tags: parseJsonArray(row.tagsJson)
      },
      gatekeeper: {
        allowed: Boolean(row.gatekeeperAllowed),
        mode: row.gatekeeperMode ?? ""
      }
    }));
    await appendAudit({ event: "triage_list", status: "ok", count: items.length });
    return NextResponse.json({ ok: true, items });
  } catch {
    try {
      const logDir = path.join(process.cwd(), "backend_core", "logs");
      const queuePath = path.join(logDir, "triage_queue.jsonl");
      const statusPath = path.join(logDir, "triage_status.jsonl");
      const [queueItems, statusItems] = await Promise.all([
        readJsonLines(queuePath),
        readJsonLines(statusPath)
      ]);
      const statusMap = new Map<string, { status: string; updatedAt: string; reviewer: string }>();
      for (const item of statusItems) {
        if (!item || typeof item !== "object") continue;
        const applicationId = typeof item.applicationId === "string" ? item.applicationId : "";
        const status = typeof item.status === "string" ? item.status : "";
        const updatedAt = typeof item.updatedAt === "string" ? item.updatedAt : "";
        const reviewer = typeof item.reviewer === "string" ? item.reviewer : "";
        if (!applicationId || !status) continue;
        const prev = statusMap.get(applicationId);
        if (!prev || updatedAt >= prev.updatedAt) {
          statusMap.set(applicationId, { status, updatedAt, reviewer });
        }
      }
      const items = queueItems.map((item) => {
        const applicationId = typeof item.applicationId === "string" ? item.applicationId : "";
        const status = statusMap.get(applicationId)?.status || "pending";
        return { ...item, status };
      });
      await appendAudit({ event: "triage_list", status: "ok", count: items.length, source: "fallback" });
      return NextResponse.json({ ok: true, items });
    } catch (fallbackError: unknown) {
      const message = fallbackError instanceof Error ? fallbackError.message : "triage_error";
      await appendAudit({ event: "triage_list", status: "error", meta: { message } });
      return NextResponse.json({ ok: false, error: message }, { status: 500 });
    }
  }
}

export async function POST(request: Request) {
  let payload: Record<string, unknown> | null = null;
  try {
    payload = await request.json();
  } catch {
    payload = null;
  }
  const applicationId = typeof payload?.applicationId === "string" ? payload.applicationId.trim() : "";
  const status = typeof payload?.status === "string" ? payload.status.trim().toLowerCase() : "";
  const reviewer = typeof payload?.reviewer === "string" ? payload.reviewer.trim() : "";
  const allowedStatuses = new Set(["pending", "review", "approved", "rejected"]);
  if (!applicationId || !allowedStatuses.has(status)) {
    return NextResponse.json({ ok: false, error: "invalid_payload" }, { status: 400 });
  }
  try {
    const db = await getDb();
    const updateTriage = db.prepare("UPDATE triage SET status = ? WHERE application_id = ?");
    updateTriage.run(status, applicationId);
    const updateApplication = db.prepare("UPDATE applications SET status = ? WHERE id = ?");
    updateApplication.run(status, applicationId);
    const insertStatus = db.prepare(
      "INSERT INTO triage_status (application_id, status, reviewer, updated_at) VALUES (?, ?, ?, ?)"
    );
    insertStatus.run(applicationId, status, reviewer, new Date().toISOString());
    const logDir = path.join(process.cwd(), "backend_core", "logs");
    const statusPath = path.join(logDir, "triage_status.jsonl");
    await fs.mkdir(logDir, { recursive: true });
    const entry = {
      applicationId,
      status,
      reviewer,
      updatedAt: new Date().toISOString()
    };
    await fs.appendFile(statusPath, `${JSON.stringify(entry)}\n`, "utf8");
    await appendAudit({
      event: "triage_update",
      status: "ok",
      applicationId,
      updateStatus: status,
      reviewer
    });
    return NextResponse.json({ ok: true, entry });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "triage_error";
    await appendAudit({
      event: "triage_update",
      status: "error",
      applicationId,
      updateStatus: status,
      reviewer,
      meta: { message }
    });
    return NextResponse.json({ ok: false, error: message }, { status: 500 });
  }
}

async function readJsonLines(filePath: string) {
  try {
    const content = await fs.readFile(filePath, "utf8");
    return content
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        try {
          return JSON.parse(line);
        } catch {
          return null;
        }
      })
      .filter(Boolean) as Array<Record<string, unknown>>;
  } catch {
    return [];
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

function parseJsonArray(value: unknown) {
  if (typeof value !== "string") return [];
  try {
    const parsed = JSON.parse(value);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

async function appendAudit(entry: Record<string, unknown>) {
  const logDir = path.join(process.cwd(), "backend_core", "logs");
  const logPath = path.join(logDir, "audit.jsonl");
  const payload = {
    ts: new Date().toISOString(),
    service: "triage",
    ...entry
  };
  try {
    await fs.mkdir(logDir, { recursive: true });
    await fs.appendFile(logPath, `${JSON.stringify(payload)}\n`, "utf8");
  } catch {
    return;
  }
}
