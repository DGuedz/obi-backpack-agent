import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET() {
  try {
    // Try to locate the STRATEGIC_REPORT.md file
    // Assuming the app runs in obiwork_web, the file is in the parent directory
    const filePath = path.join(process.cwd(), '..', 'STRATEGIC_REPORT.md');
    
    // Fallback if running from root
    const filePathAlt = path.join(process.cwd(), 'STRATEGIC_REPORT.md');

    let content = '';
    
    if (fs.existsSync(filePath)) {
      content = fs.readFileSync(filePath, 'utf-8');
    } else if (fs.existsSync(filePathAlt)) {
      content = fs.readFileSync(filePathAlt, 'utf-8');
    } else {
        // If file doesn't exist, return a placeholder or error
        return NextResponse.json(
            { error: 'Report file not found', content: '# Strategic Report\n\nNo report generated yet.' },
            { status: 404 }
        );
    }

    return NextResponse.json({ content });
  } catch (error) {
    console.error('Error reading strategic report:', error);
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}
