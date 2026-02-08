import { NextResponse } from 'next/server';
import path from 'path';
import { promisify } from 'util';
import { execFile } from 'child_process';
import { promises as fs } from 'node:fs';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

const execFileAsync = promisify(execFile);

export async function POST(request: Request) {
  const payload = await safeJson(request);
  const days = Number.isFinite(payload?.days) ? Number(payload?.days) : 10;
  const boundedDays = Math.min(Math.max(days, 1), 30);
  const scriptPath = path.join(
    process.cwd(),
    'backend_core',
    'obiwork_core',
    'tools',
    'strategic_report.py'
  );
  const reportsDir = path.join(process.cwd(), 'backend_core', 'reports');
  const historyDir = path.join(reportsDir, 'history');
  const latestPath = path.join(reportsDir, 'strategic_report_latest.md');
  const metaPath = path.join(reportsDir, 'strategic_report_latest.json');

  try {
    await fs.mkdir(reportsDir, { recursive: true });
    await fs.mkdir(historyDir, { recursive: true });
    
    const { stdout, stderr } = await execFileAsync('python3', [scriptPath, String(boundedDays)], {
      timeout: 20000,
      maxBuffer: 1024 * 1024
    });
    const output = `${stdout ?? ''}\n${stderr ?? ''}`.trim();
    const legacyPath = path.join(process.cwd(), 'STRATEGIC_REPORT.md');
    const legacyAltPath = path.join(process.cwd(), '..', 'STRATEGIC_REPORT.md');
    let content = '';
    if (await fileExists(legacyPath)) {
      content = await fs.readFile(legacyPath, 'utf-8');
    } else if (await fileExists(legacyAltPath)) {
      content = await fs.readFile(legacyAltPath, 'utf-8');
    } else if (output) {
      content = output;
    } else {
      content = '# Strategic Report\n\nNo report generated yet.';
    }
    
    // Save as latest
    await fs.writeFile(latestPath, content, 'utf-8');
    
    // Save to history with date
    const dateStr = new Date().toISOString().split('T')[0];
    const historyPath = path.join(historyDir, `strategic_report_${dateStr}.md`);
    await fs.writeFile(historyPath, content, 'utf-8');

    const meta = {
      generatedAt: new Date().toISOString(),
      days: boundedDays
    };
    await fs.writeFile(metaPath, JSON.stringify(meta), 'utf-8');
    await appendAudit({
      event: 'report_generate',
      status: 'ok',
      meta
    });
    return NextResponse.json({ ok: true, meta });
  } catch (error: unknown) {
    await appendAudit({
      event: 'report_generate',
      status: 'error',
      meta: { message: error instanceof Error ? error.message : 'unknown_error' }
    });
    return NextResponse.json({ ok: false, error: 'report_generate_failed' }, { status: 500 });
  }
}

async function safeJson(request: Request) {
  try {
    return await request.json();
  } catch {
    return null;
  }
}

async function fileExists(filePath: string) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

async function appendAudit(entry: Record<string, unknown>) {
  const logDir = path.join(process.cwd(), 'backend_core', 'logs');
  const logPath = path.join(logDir, 'audit.jsonl');
  const payload = {
    ts: new Date().toISOString(),
    service: 'reports',
    ...entry
  };
  try {
    await fs.mkdir(logDir, { recursive: true });
    await fs.appendFile(logPath, `${JSON.stringify(payload)}\n`, 'utf-8');
  } catch {
    return;
  }
}
