import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import util from 'util';
import path from 'path';
import fs from 'fs';

const execPromise = util.promisify(exec);

export async function POST(req: Request) {
  try {
    const { message } = await req.json();
    const command = message.trim();

    // Helper to get script path
    const getScriptPath = (scriptName: string) => {
        return path.resolve(process.cwd(), "..", "obiwork_core", "gatekeeper", scriptName);
    };

    // 1. SCAN COMMAND (Compliance Gate)
    if (command.startsWith("/scan")) {
      const parts = command.split(" ");
      if (parts.length < 2) {
        return NextResponse.json({ message: "Usage: /scan <wallet_address>" });
      }
      const wallet = parts[1];
      const scriptPath = getScriptPath("compliance_gate.py");
      
      try {
        const { stdout, stderr } = await execPromise(`python3 ${scriptPath} --scan ${wallet} --json`);
        if (stderr) console.error("Python Stderr:", stderr);
        
        const data = JSON.parse(stdout);
        return NextResponse.json({
          message: `Analysis complete for ${wallet}`,
          type: "analysis",
          data: data
        });
      } catch (error) {
        console.error("Execution error:", error);
        return NextResponse.json({ message: "Scan failed.", type: "alert" });
      }
    }

    // 2. TRACK COMMAND (Wallet Tracker)
    if (command.startsWith("/track")) {
        const parts = command.split(" ");
        if (parts.length < 2) {
            return NextResponse.json({ message: "Usage: /track <wallet_address> [label]" });
        }
        const wallet = parts[1];
        const label = parts.slice(2).join(" ") || "Ally";
        const scriptPath = getScriptPath("wallet_tracker.py");

        try {
            const { stdout, stderr } = await execPromise(`python3 ${scriptPath} --add ${wallet} --label "${label}" --json`);
            if (stderr) console.error("Python Stderr:", stderr);
            
            const data = JSON.parse(stdout);
            return NextResponse.json({
                message: ` Tracking enabled for ${wallet} (${label})`,
                type: "text",
                data: data
            });
        } catch (error) {
            return NextResponse.json({ message: "Failed to track wallet.", type: "alert" });
        }
    }

    // 3. WATCHLIST COMMAND (List tracked)
    if (command.startsWith("/watchlist")) {
        const scriptPath = getScriptPath("wallet_tracker.py");
        try {
            const { stdout } = await execPromise(`python3 ${scriptPath} --list --json`);
            const wallets = JSON.parse(stdout);
            
            if (wallets.length === 0) {
                return NextResponse.json({ message: "Watchlist is empty. Use /track <wallet> to add.", type: "text" });
            }

            let msg = " **WATCHLIST**:\n";
            wallets.forEach((w: any) => {
                msg += `- **${w.label}**: \`${w.address.slice(0,6)}...${w.address.slice(-4)}\`\n`;
            });
            
            return NextResponse.json({ message: msg, type: "text" });
        } catch (error) {
            return NextResponse.json({ message: "Failed to fetch watchlist.", type: "alert" });
        }
    }

    // 4. WHALES / ACTIVITY COMMAND
    if (command.startsWith("/whales") || command.startsWith("/activity")) {
        const scriptPath = getScriptPath("wallet_tracker.py");
        try {
            const { stdout } = await execPromise(`python3 ${scriptPath} --check --json`);
            const updates = JSON.parse(stdout);
            
            if (updates.length === 0) {
                return NextResponse.json({ message: "No recent activity detected on tracked wallets.", type: "text" });
            }

            let msg = " **ON-CHAIN ACTIVITY**:\n";
            updates.forEach((u: any) => {
                msg += `[${u.timestamp.split("T")[1].split(".")[0]}] **${u.label}**: ${u.action}\n`;
            });
            
            return NextResponse.json({ message: msg, type: "text" });
        } catch (error) {
            return NextResponse.json({ message: "Failed to check activity.", type: "alert" });
        }
    }

    // 5. MARKET COMMAND
    if (command.startsWith("/market")) {
        const reportPath = path.resolve(process.cwd(), "..", "STRATEGIC_REPORT.md");
        if (fs.existsSync(reportPath)) {
            const report = fs.readFileSync(reportPath, "utf-8");
            return NextResponse.json({
                message: report.substring(0, 500) + "...\n(See full report in dashboard)",
                type: "text"
            });
        }
        return NextResponse.json({ message: "Market report not available." });
    }

    // DEFAULT
    return NextResponse.json({
      message: "Command not recognized. Try:\n- /scan <wallet>\n- /track <wallet> [label]\n- /watchlist\n- /whales\n- /market",
      type: "text"
    });

  } catch (error) {
    console.error("API Error:", error);
    return NextResponse.json(
      { error: "Internal Server Error" },
      { status: 500 }
    );
  }
}
