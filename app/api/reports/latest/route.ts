import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET() {
  try {
    const reportsDir = path.join(process.cwd(), 'backend_core', 'reports');
    const latestPath = path.join(reportsDir, 'strategic_report_latest.md');
    const metaPath = path.join(reportsDir, 'strategic_report_latest.json');
    const legacyPath = path.join(process.cwd(), '..', 'STRATEGIC_REPORT.md');
    const legacyAltPath = path.join(process.cwd(), 'STRATEGIC_REPORT.md');

    let content = '';
    let meta: Record<string, unknown> | null = null;

    if (fs.existsSync(latestPath)) {
      content = fs.readFileSync(latestPath, 'utf-8');
      if (fs.existsSync(metaPath)) {
        try {
          meta = JSON.parse(fs.readFileSync(metaPath, 'utf-8'));
        } catch {
          meta = null;
        }
      }
    } else if (fs.existsSync(legacyPath)) {
      content = fs.readFileSync(legacyPath, 'utf-8');
    } else if (fs.existsSync(legacyAltPath)) {
      content = fs.readFileSync(legacyAltPath, 'utf-8');
    } else {
      return NextResponse.json(
        { error: 'Report file not found', content: '# Strategic Report\n\nNo report generated yet.' },
        { status: 404 }
      );
    }

    await appendAudit({
      event: 'report_latest',
      status: 'ok',
      meta: meta ?? undefined
    });

    return NextResponse.json({ content, meta });
  } catch (error) {
    await appendAudit({
      event: 'report_latest',
      status: 'error',
      meta: { message: error instanceof Error ? error.message : 'unknown_error' }
    });
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    );
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
    fs.mkdirSync(logDir, { recursive: true });
    fs.appendFileSync(logPath, `${JSON.stringify(payload)}\n`, 'utf-8');
  } catch {
    return;
  }
}
