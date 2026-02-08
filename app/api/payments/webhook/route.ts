import { NextResponse } from 'next/server';
import path from 'path';
import crypto from 'crypto';
import Database from 'better-sqlite3';
import { promises as fs } from 'node:fs';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

const dbPath = process.env.OBI_APPLICATION_DB_PATH
  ? path.resolve(process.env.OBI_APPLICATION_DB_PATH)
  : path.join(process.cwd(), 'backend_core', 'db', 'obi_applications.sqlite');
let dbInstance: ReturnType<typeof Database> | null = null;

export async function POST(req: Request) {
  const requestId = crypto.randomUUID();
  try {
    const payload = await req.json();
    const { PaymentId, ChangePaymentStatus, PaymentStatus } = payload;
    
    // Cielo webhook payload simplified
    // See: https://developercielo.github.io/manual/cielo-ecommerce#notificacao-de-mudanca-de-status
    
    if (!PaymentId || !ChangePaymentStatus) {
       await appendAudit({ event: 'webhook_received', status: 'ignored', meta: { reason: 'invalid_payload', payload }, requestId });
       return NextResponse.json({ ok: true, ignored: true });
    }

    const newStatus = Number(PaymentStatus || ChangePaymentStatus.Status);
    const db = await getDb();
    
    // Find payment by provider_payment_id
    const payment = db.prepare("SELECT * FROM payments WHERE provider_payment_id = ?").get(PaymentId) as Record<string, unknown> | undefined;

    if (!payment) {
        await appendAudit({ event: 'webhook_received', status: 'ignored', meta: { reason: 'payment_not_found', PaymentId }, requestId });
        return NextResponse.json({ ok: true, ignored: true });
    }

    // Update payment status
    db.prepare("UPDATE payments SET status = ? WHERE provider_payment_id = ?").run(String(newStatus), PaymentId);

    // Reconcile License
    // Status 2 = Authorized/Paid
    if (newStatus === 2) {
        const license = db.prepare("SELECT * FROM licenses WHERE payment_id = ?").get(payment.id) as Record<string, unknown> | undefined;
        if (license && license.status !== 'active') {
             db.prepare("UPDATE licenses SET status = 'active' WHERE id = ?").run(license.id);
             await appendAudit({ event: 'license_reconciled', status: 'activated', licenseId: license.id, requestId });
        } else if (!license) {
             // Create license if missing (edge case)
             const licenseId = crypto.randomUUID();
             const createdAt = new Date().toISOString();
             db.prepare(
                "INSERT INTO licenses (id, wallet_address, tier_id, status, issued_at, payment_id) VALUES (?, ?, ?, ?, ?, ?)"
              ).run(licenseId, payment.wallet_address, payment.tier_id, 'active', createdAt, payment.id);
             await appendAudit({ event: 'license_reconciled', status: 'created', licenseId, requestId });
        }
    } else if (newStatus === 10 || newStatus === 13) { // Canceled/Aborted
         db.prepare("UPDATE licenses SET status = 'revoked' WHERE payment_id = ?").run(payment.id);
         await appendAudit({ event: 'license_reconciled', status: 'revoked', paymentId: payment.id, requestId });
    }

    await appendAudit({ event: 'webhook_processed', status: 'ok', PaymentId, newStatus, requestId });
    return NextResponse.json({ ok: true });

  } catch (error) {
    const message = error instanceof Error ? error.message : 'Internal Server Error';
    await appendAudit({ event: 'webhook_error', status: 'error', meta: { message }, requestId });
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

async function getDb() {
  if (dbInstance) return dbInstance;
  const dbDir = path.dirname(dbPath);
  await fs.mkdir(dbDir, { recursive: true });
  const db = new Database(dbPath);
  // Ensure tables exist (shared with payments route)
  db.exec(
    "CREATE TABLE IF NOT EXISTS payments (id TEXT PRIMARY KEY, created_at TEXT, wallet_address TEXT, tier_id TEXT, amount REAL, status TEXT, provider TEXT, provider_payment_id TEXT, order_id TEXT, email TEXT)"
  );
  db.exec(
    "CREATE TABLE IF NOT EXISTS licenses (id TEXT PRIMARY KEY, wallet_address TEXT, tier_id TEXT, status TEXT, issued_at TEXT, payment_id TEXT)"
  );
  dbInstance = db;
  return dbInstance;
}

async function appendAudit(entry: Record<string, unknown>) {
  const logDir = path.join(process.cwd(), 'backend_core', 'logs');
  const logPath = path.join(logDir, 'audit.jsonl');
  const payload = {
    ts: new Date().toISOString(),
    service: 'payments_webhook',
    ...entry
  };
  try {
    await fs.mkdir(logDir, { recursive: true });
    await fs.appendFile(logPath, `${JSON.stringify(payload)}\n`, 'utf-8');
  } catch {
    return;
  }
}
