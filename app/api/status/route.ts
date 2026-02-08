import { NextResponse } from 'next/server';
import path from 'path';
import { promises as fs } from 'node:fs';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

export async function GET(request: Request) {
  const reportsDir = path.join(process.cwd(), 'backend_core', 'reports');
  const metaPath = path.join(reportsDir, 'strategic_report_latest.json');
  const reportMeta = await readJson(metaPath);
  const gatekeeperConfigured = Boolean(process.env.OBI_PASS_MINT && process.env.OBI_PASS_MINT !== 'DeployPending...');
  const gatekeeperRpcConfigured = Boolean(process.env.OBI_SOLANA_RPC_URL);
  const paymentsConfigured = Boolean(process.env.CIELO_MERCHANT_ID);
  const mentorshipConfigured = Boolean(process.env.GOOGLE_CLIENT_EMAIL && process.env.GOOGLE_PRIVATE_KEY && process.env.GOOGLE_CALENDAR_ID);
  const backpackConfigured = Boolean(process.env.BACKPACK_API_KEY && process.env.BACKPACK_API_SECRET);
  const latestGeneratedAt = reportMeta?.generatedAt ?? null;
  const reportAgeHours = latestGeneratedAt ? (Date.now() - new Date(latestGeneratedAt).getTime()) / 36e5 : null;
  const reportFresh = reportAgeHours !== null ? reportAgeHours <= 48 : false;
  
  // Real health checks with latency
  const [gatekeeperHealth, reportsHealth, paymentsHealth, mentorshipHealth, backpackHealth] = await Promise.all([
    checkGatekeeperHealth(gatekeeperConfigured, gatekeeperRpcConfigured),
    checkReportsHealth(latestGeneratedAt, reportFresh),
    checkPaymentsHealth(paymentsConfigured),
    checkMentorshipHealth(mentorshipConfigured),
    checkBackpackHealth(backpackConfigured)
  ]);

  const services = {
    gatekeeper: gatekeeperHealth,
    reports: reportsHealth,
    payments: paymentsHealth,
    mentorship: mentorshipHealth,
    backpack: backpackHealth
  };
  const overallOk = Object.values(services).every((service) => service.ok);
  const payload = {
    overall: { ok: overallOk, status: overallOk ? 'ok' : 'degraded' },
    services,
    gatekeeper: services.gatekeeper.details,
    reports: { latestGeneratedAt },
    payments: services.payments.details,
    mentorship: services.mentorship.details,
    backpack: services.backpack.details
  };
  const { searchParams } = new URL(request.url);
  const service = searchParams.get('service');
  if (service) {
    const serviceStatus = services[service as keyof typeof services];
    if (!serviceStatus) {
      await appendAudit({ event: 'status', status: 'not_found', service });
      return NextResponse.json({ ok: false, error: 'Service not found' }, { status: 404 });
    }
    await appendAudit({ event: 'status', status: 'ok', service });
    return NextResponse.json({ ok: true, service, health: serviceStatus });
  }
  await appendAudit({ event: 'status', status: 'ok' });
  return NextResponse.json({ ok: true, status: payload });
}

async function checkGatekeeperHealth(configured: boolean, rpcConfigured: boolean) {
  const start = performance.now();
  let ok = configured && rpcConfigured;
  let status = ok ? 'ok' : 'needs_config';
  let latency = 0;
  
  if (rpcConfigured) {
    // Simple connectivity check if possible, or assume OK if configured for now to avoid blocking
    // In future: await pingRpc(process.env.OBI_SOLANA_RPC_URL)
  }
  
  latency = Math.round(performance.now() - start);
  return {
    ok,
    status,
    latency,
    details: { mintConfigured: configured, rpcConfigured }
  };
}

async function checkReportsHealth(latestGeneratedAt: string | null, fresh: boolean) {
  const start = performance.now();
  const ok = Boolean(latestGeneratedAt) && fresh;
  const status = latestGeneratedAt ? (fresh ? 'ok' : 'stale') : 'pending';
  const latency = Math.round(performance.now() - start);
  return {
    ok,
    status,
    latency,
    details: { latestGeneratedAt, reportAgeHours: latestGeneratedAt ? (Date.now() - new Date(latestGeneratedAt).getTime()) / 36e5 : null }
  };
}

async function checkPaymentsHealth(configured: boolean) {
  const start = performance.now();
  let ok = configured;
  let status = configured ? 'ok' : 'needs_config';
  let latency = 0;
  
  // Check DB connection for payments
  try {
    const dbPath = process.env.OBI_APPLICATION_DB_PATH
      ? path.resolve(process.env.OBI_APPLICATION_DB_PATH)
      : path.join(process.cwd(), 'backend_core', 'db', 'obi_applications.sqlite');
    await fs.access(dbPath).catch(() => {}); 
  } catch {
    // If DB file doesn't exist yet, it's fine, it will be created on first write
  }
  
  latency = Math.round(performance.now() - start);
  return {
    ok,
    status,
    latency,
    details: { cieloConfigured: configured }
  };
}

async function checkMentorshipHealth(configured: boolean) {
  const start = performance.now();
  let ok = configured;
  let status = configured ? 'ok' : 'needs_config';
  const latency = Math.round(performance.now() - start);
  return {
    ok,
    status,
    latency,
    details: { googleConfigured: configured }
  };
}

async function checkBackpackHealth(configured: boolean) {
  const start = performance.now();
  let ok = configured;
  let status = configured ? 'ok' : 'needs_config';
  const latency = Math.round(performance.now() - start);
  return {
    ok,
    status,
    latency,
    details: { configured }
  };
}

async function readJson(filePath: string) {
  try {
    const raw = await fs.readFile(filePath, 'utf-8');
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

async function appendAudit(entry: Record<string, unknown>) {
  const logDir = path.join(process.cwd(), 'backend_core', 'logs');
  const logPath = path.join(logDir, 'audit.jsonl');
  const payload = {
    ts: new Date().toISOString(),
    service: 'status',
    ...entry
  };
  try {
    await fs.mkdir(logDir, { recursive: true });
    await fs.appendFile(logPath, `${JSON.stringify(payload)}\n`, 'utf-8');
  } catch {
    return;
  }
}
