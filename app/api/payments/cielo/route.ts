
import { NextResponse } from 'next/server';
import { CieloService } from '@/app/lib/cielo';
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
const TIER_PRICES: Record<string, number> = {
  scout: 29.99,
  commander: 49.9,
  architect: 99
};

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { cardData, amount, orderId, customerName, walletAddress, tierId, email } = body;

    if (!cardData || !amount || !walletAddress || !tierId) {
      await appendAudit({
        event: 'payment_create',
        status: 'error',
        meta: { message: 'missing_fields' }
      });
      return NextResponse.json({ error: 'Missing payment data' }, { status: 400 });
    }
    const tierPrice = TIER_PRICES[String(tierId)];
    if (!tierPrice) {
      await appendAudit({
        event: 'payment_create',
        status: 'error',
        walletAddress,
        tierId,
        meta: { message: 'invalid_tier' }
      });
      return NextResponse.json({ error: 'Invalid tier' }, { status: 400 });
    }
    const parsedAmount = Number(amount);
    if (!Number.isFinite(parsedAmount) || Math.abs(parsedAmount - tierPrice) > 0.01) {
      await appendAudit({
        event: 'payment_create',
        status: 'error',
        walletAddress,
        tierId,
        amount,
        meta: { message: 'amount_mismatch' }
      });
      return NextResponse.json({ error: 'Invalid amount' }, { status: 400 });
    }

    const existing = await findActiveLicense(walletAddress, String(tierId));
    if (existing) {
      const response = NextResponse.json({
        ok: true,
        license: existing.license,
        Payment: { Status: 1, PaymentId: existing.paymentId }
      });
      response.cookies.set('obi_access_allowed', 'true', {
        httpOnly: true,
        sameSite: 'lax',
        secure: process.env.NODE_ENV === 'production',
        maxAge: 60 * 60 * 24,
        path: '/'
      });
      response.cookies.set('obi_access_wallet', String(walletAddress), {
        httpOnly: true,
        sameSite: 'lax',
        secure: process.env.NODE_ENV === 'production',
        maxAge: 60 * 60 * 24,
        path: '/'
      });
      await appendAudit({
        event: 'payment_create',
        status: 'ok',
        walletAddress,
        tierId,
        meta: { message: 'already_licensed' }
      });
      return response;
    }

    if (!process.env.CIELO_MERCHANT_ID) {
        await new Promise(resolve => setTimeout(resolve, 2000));
        const paymentId = `mock-payment-id-${Date.now()}`;
        const resolvedOrderId = typeof orderId === 'string' && orderId.trim() ? orderId.trim() : `OBI-${tierId}-${Date.now()}`;
        await persistPaymentAndLicense({
          walletAddress,
          tierId,
          amount: parsedAmount,
          orderId: resolvedOrderId,
          email: typeof email === 'string' ? email.trim() : '',
          provider: 'cielo-mock',
          providerPaymentId: paymentId,
          status: 'authorized'
        });
        await appendAudit({
          event: 'payment_create',
          status: 'ok',
          walletAddress,
          tierId,
          amount: parsedAmount,
          provider: 'cielo-mock'
        });
        const response = NextResponse.json({
          Payment: {
            Status: 1,
            PaymentId: paymentId,
            ReturnMessage: 'Operation Successful (Mock)'
          }
        });
        response.cookies.set('obi_access_allowed', 'true', {
          httpOnly: true,
          sameSite: 'lax',
          secure: process.env.NODE_ENV === 'production',
          maxAge: 60 * 60 * 24,
          path: '/'
        });
        response.cookies.set('obi_access_wallet', String(walletAddress), {
          httpOnly: true,
          sameSite: 'lax',
          secure: process.env.NODE_ENV === 'production',
          maxAge: 60 * 60 * 24,
          path: '/'
        });
        return response;
    }

    const cielo = new CieloService();

    const resolvedOrderId = typeof orderId === 'string' && orderId.trim() ? orderId.trim() : `OBI-${tierId}-${Date.now()}`;
    const transaction = {
      MerchantOrderId: resolvedOrderId,
      Customer: {
        Name: customerName || 'Customer',
      },
      Payment: {
        Type: 'CreditCard' as const,
        Amount: parsedAmount * 100,
        Installments: 1,
        CreditCard: {
          CardNumber: cardData.number,
          Holder: cardData.holder,
          ExpirationDate: cardData.expiry,
          SecurityCode: cardData.cvc,
          Brand: cardData.brand || 'Visa', // Should be detected
        },
      },
    };

    const result = await cielo.createTransaction(transaction);
    const status = result?.Payment?.Status;
    const paymentId = result?.Payment?.PaymentId;
    if (status === 1 || status === 2) {
      await persistPaymentAndLicense({
        walletAddress,
        tierId,
        amount: parsedAmount,
        orderId: resolvedOrderId,
        email: typeof email === 'string' ? email.trim() : '',
        provider: 'cielo',
        providerPaymentId: paymentId,
        status: 'authorized'
      });
      await appendAudit({
        event: 'payment_create',
        status: 'ok',
        walletAddress,
        tierId,
        amount: parsedAmount,
        provider: 'cielo'
      });
      const response = NextResponse.json(result);
      response.cookies.set('obi_access_allowed', 'true', {
        httpOnly: true,
        sameSite: 'lax',
        secure: process.env.NODE_ENV === 'production',
        maxAge: 60 * 60 * 24,
        path: '/'
      });
      response.cookies.set('obi_access_wallet', String(walletAddress), {
        httpOnly: true,
        sameSite: 'lax',
        secure: process.env.NODE_ENV === 'production',
        maxAge: 60 * 60 * 24,
        path: '/'
      });
      return response;
    }
    await appendAudit({
      event: 'payment_create',
      status: 'error',
      walletAddress,
      tierId,
      amount: parsedAmount,
      provider: 'cielo',
      meta: { paymentStatus: status }
    });
    return NextResponse.json(result);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Internal Server Error';
    await appendAudit({
      event: 'payment_create',
      status: 'error',
      meta: { message }
    });
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

async function getDb() {
  if (dbInstance) return dbInstance;
  const dbDir = path.dirname(dbPath);
  await fs.mkdir(dbDir, { recursive: true });
  const db = new Database(dbPath);
  db.exec(
    "CREATE TABLE IF NOT EXISTS payments (id TEXT PRIMARY KEY, created_at TEXT, wallet_address TEXT, tier_id TEXT, amount REAL, status TEXT, provider TEXT, provider_payment_id TEXT, order_id TEXT, email TEXT)"
  );
  db.exec(
    "CREATE TABLE IF NOT EXISTS licenses (id TEXT PRIMARY KEY, wallet_address TEXT, tier_id TEXT, status TEXT, issued_at TEXT, payment_id TEXT)"
  );
  db.exec("CREATE INDEX IF NOT EXISTS idx_payments_wallet ON payments(wallet_address)");
  db.exec("CREATE INDEX IF NOT EXISTS idx_licenses_wallet ON licenses(wallet_address)");
  ensureColumn(db, "payments", "order_id", "TEXT");
  ensureColumn(db, "payments", "email", "TEXT");
  dbInstance = db;
  return dbInstance;
}

async function persistPaymentAndLicense(input: {
  walletAddress: string;
  tierId: string;
  amount: number;
  orderId: string;
  email: string;
  provider: string;
  providerPaymentId?: string;
  status: string;
}) {
  const db = await getDb();
  const paymentId = crypto.randomUUID();
  const createdAt = new Date().toISOString();
  db.prepare(
    "INSERT INTO payments (id, created_at, wallet_address, tier_id, amount, status, provider, provider_payment_id, order_id, email) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
  ).run(
    paymentId,
    createdAt,
    input.walletAddress,
    input.tierId,
    input.amount,
    input.status,
    input.provider,
    input.providerPaymentId ?? '',
    input.orderId,
    input.email
  );
  const licenseId = crypto.randomUUID();
  db.prepare(
    "INSERT INTO licenses (id, wallet_address, tier_id, status, issued_at, payment_id) VALUES (?, ?, ?, ?, ?, ?)"
  ).run(licenseId, input.walletAddress, input.tierId, 'active', createdAt, paymentId);
}

async function findActiveLicense(walletAddress: string, tierId: string) {
  try {
    const db = await getDb();
    const license = db
      .prepare(
        "SELECT id, wallet_address as walletAddress, tier_id as tierId, status, issued_at as issuedAt, payment_id as paymentId FROM licenses WHERE wallet_address = ? AND tier_id = ? AND status = 'active' ORDER BY issued_at DESC LIMIT 1"
      )
      .get(walletAddress, tierId) as Record<string, unknown> | undefined;
    if (!license) return null;
    const payment = db
      .prepare("SELECT provider_payment_id as providerPaymentId FROM payments WHERE id = ? LIMIT 1")
      .get(license.paymentId) as Record<string, unknown> | undefined;
    return {
      license,
      paymentId: payment?.providerPaymentId || license.paymentId
    };
  } catch {
    return null;
  }
}

function ensureColumn(db: Database.Database, table: string, column: string, type: string) {
  try {
    db.exec(`ALTER TABLE ${table} ADD COLUMN ${column} ${type}`);
  } catch {
    return;
  }
}

async function appendAudit(entry: Record<string, unknown>) {
  const logDir = path.join(process.cwd(), 'backend_core', 'logs');
  const logPath = path.join(logDir, 'audit.jsonl');
  const payload = {
    ts: new Date().toISOString(),
    service: 'payments',
    ...entry
  };
  try {
    await fs.mkdir(logDir, { recursive: true });
    await fs.appendFile(logPath, `${JSON.stringify(payload)}\n`, 'utf-8');
  } catch {
    return;
  }
}
