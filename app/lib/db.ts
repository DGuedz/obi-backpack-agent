import path from 'path';
import Database from 'better-sqlite3';
import { promises as fs } from 'node:fs';

const dbPath = process.env.OBI_APPLICATION_DB_PATH
  ? path.resolve(process.env.OBI_APPLICATION_DB_PATH)
  : path.join(process.cwd(), 'backend_core', 'db', 'obi_applications.sqlite');

let dbInstance: Database.Database | null = null;

export async function getDb(): Promise<Database.Database> {
  if (dbInstance) return dbInstance;

  const dbDir = path.dirname(dbPath);
  await fs.mkdir(dbDir, { recursive: true });
  
  const db = new Database(dbPath);
  
  // Applications Tables
  db.exec(
    "CREATE TABLE IF NOT EXISTS applications (id TEXT PRIMARY KEY, received_at TEXT, wallet_address TEXT, user_agent TEXT, forwarded_for TEXT, answers_json TEXT, gatekeeper_allowed INTEGER, gatekeeper_mode TEXT, status TEXT)"
  );
  db.exec(
    "CREATE TABLE IF NOT EXISTS triage (application_id TEXT PRIMARY KEY, received_at TEXT, wallet_address TEXT, score INTEGER, tier TEXT, tags_json TEXT, status TEXT, gatekeeper_allowed INTEGER, gatekeeper_mode TEXT)"
  );
  db.exec(
    "CREATE TABLE IF NOT EXISTS triage_status (id INTEGER PRIMARY KEY AUTOINCREMENT, application_id TEXT, status TEXT, reviewer TEXT, updated_at TEXT)"
  );

  // Payments & Licenses Tables
  db.exec(
    "CREATE TABLE IF NOT EXISTS payments (id TEXT PRIMARY KEY, created_at TEXT, wallet_address TEXT, tier_id TEXT, amount REAL, status TEXT, provider TEXT, provider_payment_id TEXT, order_id TEXT, email TEXT)"
  );
  db.exec(
    "CREATE TABLE IF NOT EXISTS licenses (id TEXT PRIMARY KEY, wallet_address TEXT, tier_id TEXT, status TEXT, issued_at TEXT, payment_id TEXT)"
  );

  // Indexes
  db.exec("CREATE INDEX IF NOT EXISTS idx_applications_wallet ON applications(wallet_address)");
  db.exec("CREATE INDEX IF NOT EXISTS idx_triage_status_app ON triage_status(application_id)");
  db.exec("CREATE INDEX IF NOT EXISTS idx_payments_wallet ON payments(wallet_address)");
  db.exec("CREATE INDEX IF NOT EXISTS idx_licenses_wallet ON licenses(wallet_address)");

  // Migrations / Schema Updates
  ensureColumn(db, "payments", "order_id", "TEXT");
  ensureColumn(db, "payments", "email", "TEXT");

  dbInstance = db;
  return dbInstance;
}

function ensureColumn(db: Database.Database, table: string, column: string, type: string) {
  try {
    const columns = db.pragma(`table_info(${table})`) as Array<{ name: string }>;
    if (!columns.some(col => col.name === column)) {
       db.exec(`ALTER TABLE ${table} ADD COLUMN ${column} ${type}`);
    }
  } catch {
    // Ignore if table doesn't exist or other error, will be handled by main create statements or next retry
  }
}
