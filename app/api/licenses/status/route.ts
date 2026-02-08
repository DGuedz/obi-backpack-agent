import { NextResponse } from 'next/server';
import path from 'path';
import Database from 'better-sqlite3';
import { promises as fs } from 'node:fs';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

const dbPath = process.env.OBI_APPLICATION_DB_PATH
  ? path.resolve(process.env.OBI_APPLICATION_DB_PATH)
  : path.join(process.cwd(), 'backend_core', 'db', 'obi_applications.sqlite');
let dbInstance: ReturnType<typeof Database> | null = null;

export async function POST(request: Request) {
  const payload = await safeJson(request);
  const walletAddress = typeof payload?.walletAddress === 'string' ? payload.walletAddress.trim() : '';
  if (!walletAddress) {
    return NextResponse.json({ ok: false, error: 'wallet_required' }, { status: 400 });
  }
  try {
    const db = await getDb();
    const row = db
      .prepare(
        'SELECT id, wallet_address as walletAddress, tier_id as tierId, status, issued_at as issuedAt, payment_id as paymentId FROM licenses WHERE wallet_address = ? ORDER BY issued_at DESC LIMIT 1'
      )
      .get(walletAddress) as Record<string, unknown> | undefined;
    await appendAudit({
      event: 'license_status',
      status: 'ok',
      walletAddress
    });
    return NextResponse.json({ ok: true, license: row ?? null });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : 'license_status_error';
    await appendAudit({
      event: 'license_status',
      status: 'error',
      walletAddress,
      meta: { message }
    });
    return NextResponse.json({ ok: false, error: message }, { status: 500 });
  }
}

async function safeJson(request: Request) {
  try {
    return await request.json();
  } catch {
    return null;
  }
}

async function getDb() {
  if (dbInstance) return dbInstance;
  const dbDir = path.dirname(dbPath);
  await fs.mkdir(dbDir, { recursive: true });
  const db = new Database(dbPath);
  db.exec(
    "CREATE TABLE IF NOT EXISTS licenses (id TEXT PRIMARY KEY, wallet_address TEXT, tier_id TEXT, status TEXT, issued_at TEXT, payment_id TEXT)"
  );
  db.exec("CREATE INDEX IF NOT EXISTS idx_licenses_wallet ON licenses(wallet_address)");
  dbInstance = db;
  return dbInstance;
}

async function appendAudit(entry: Record<string, unknown>) {
  const logDir = path.join(process.cwd(), 'backend_core', 'logs');
  const logPath = path.join(logDir, 'audit.jsonl');
  const payload = {
    ts: new Date().toISOString(),
    service: 'licenses',
    ...entry
  };
  try {
    await fs.mkdir(logDir, { recursive: true });
    await fs.appendFile(logPath, `${JSON.stringify(payload)}\n`, 'utf-8');
  } catch {
    return;
  }
}
