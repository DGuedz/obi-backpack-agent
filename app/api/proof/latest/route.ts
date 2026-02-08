import { NextResponse } from 'next/server';
import path from 'path';
import { promises as fs } from 'node:fs';
import crypto from 'crypto';

export const dynamic = 'force-dynamic';

interface ProofData {
  timestamp: string;
  source: string;
  metrics: Record<string, string>;
  topAssets: Array<{ asset: string; volume: string; trades: string }>;
  auditTrail: Array<{ time: string; symbol: string; side: string; price: string; quantity: string; fee: string }>;
  hash: string;
  signature: string;
  filename: string;
}

export async function GET() {
  try {
    const rootDir = process.cwd();
    const files = await fs.readdir(rootDir);
    const proofFiles = files.filter(f => f.startsWith('OBI_PROOF_') && f.endsWith('.md'));

    if (proofFiles.length === 0) {
      return NextResponse.json({ ok: false, error: 'No proof files found' }, { status: 404 });
    }

    // Sort by name descending (timestamp)
    proofFiles.sort((a, b) => b.localeCompare(a));
    const latestFile = proofFiles[0];
    const filePath = path.join(rootDir, latestFile);
    const content = await fs.readFile(filePath, 'utf-8');

    // Parse Markdown content
    const data = parseProofMarkdown(content, latestFile);

    return NextResponse.json({ ok: true, data });
  } catch (error) {
    console.error("Failed to fetch proof:", error);
    return NextResponse.json({ ok: false, error: 'Internal server error' }, { status: 500 });
  }
}

function parseProofMarkdown(content: string, filename: string): ProofData {
  const lines = content.split('\n');
  const metrics: Record<string, string> = {};
  const topAssets: Array<{ asset: string; volume: string; trades: string }> = [];
  const auditTrail: Array<{ time: string; symbol: string; side: string; price: string; quantity: string; fee: string }> = [];
  
  let currentSection = '';
  let timestamp = '';
  let source = '';

  for (const line of lines) {
    if (line.startsWith('**Generated at:**')) timestamp = line.split('**')[2].trim();
    if (line.startsWith('**Source:**')) source = line.split('**')[2].trim();
    
    if (line.includes('Performance Metrics')) { currentSection = 'metrics'; continue; }
    if (line.includes('Top Traded Assets')) { currentSection = 'assets'; continue; }
    if (line.includes('Audit Trail')) { currentSection = 'audit'; continue; }

    if (line.startsWith('|')) {
      const parts = line.split('|').map(p => p.trim()).filter(p => p);
      if (parts.length < 2 || parts[0].includes('---') || parts[0] === 'Metric' || parts[0] === 'Asset' || parts[0] === 'Time') continue;

      if (currentSection === 'metrics') {
        // | **Total Volume Generated** | **$5,385.85 USD** |
        const key = parts[0].replace(/\*\*/g, '').trim();
        const value = parts[1].replace(/\*\*/g, '').trim();
        metrics[key] = value;
      } else if (currentSection === 'assets') {
        // | BTC_USDC_PERP | $3,644.64 | 39 |
        topAssets.push({
          asset: parts[0],
          volume: parts[1],
          trades: parts[2]
        });
      } else if (currentSection === 'audit') {
        // | 2026-02-06T20:35:43.674 | BNB_USDC | ASK | $663.9000 | 0.017 | $0.00902904 |
        if (parts.length >= 6) {
          auditTrail.push({
            time: parts[0],
            symbol: parts[1],
            side: parts[2],
            price: parts[3],
            quantity: parts[4],
            fee: parts[5]
          });
        }
      }
    }
  }

  // Calculate Hash (simulate what the script does)
  // Note: The script hashes the *entire* report string. 
  // Since we read the file exactly as written, we can hash the content.
  const hash = crypto.createHash('sha256').update(content, 'utf8').digest('hex');

  // Hardcoded signature for demo purposes (from Colosseum Alignment doc)
  // In a real scenario, this would be read from a sidecar file or DB.
  const signature = "87rowg9VPHBuZLqOix1TuLTunBtC5AcBL+upiQ33GXCJlUDqjBmL7DNjhl5RhEoZMLgL/i/l3yLfKYdHnF4lBA==";

  return {
    timestamp,
    source,
    metrics,
    topAssets,
    auditTrail,
    hash,
    signature,
    filename
  };
}
