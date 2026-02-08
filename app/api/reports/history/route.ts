import { NextResponse } from 'next/server';
import path from 'path';
import { promises as fs } from 'node:fs';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const date = searchParams.get('date');
  const reportsDir = path.join(process.cwd(), 'backend_core', 'reports');
  const historyDir = path.join(reportsDir, 'history');
  
  // List history if no date provided
  if (!date) {
    try {
        await fs.mkdir(historyDir, { recursive: true });
        const files = await fs.readdir(historyDir);
        const history = files
            .filter(f => f.endsWith('.md'))
            .map(f => ({
                date: f.replace('strategic_report_', '').replace('.md', ''),
                filename: f
            }))
            .sort((a, b) => b.date.localeCompare(a.date));
        
        return NextResponse.json({ ok: true, history });
    } catch {
        return NextResponse.json({ ok: true, history: [] });
    }
  }

  // Fetch specific historical report
  const safeDate = date.replace(/[^0-9-]/g, ''); // basic sanitization
  const reportPath = path.join(historyDir, `strategic_report_${safeDate}.md`);
  
  try {
      const content = await fs.readFile(reportPath, 'utf-8');
      return NextResponse.json({ ok: true, date: safeDate, content });
  } catch {
      return NextResponse.json({ ok: false, error: 'report_not_found' }, { status: 404 });
  }
}
