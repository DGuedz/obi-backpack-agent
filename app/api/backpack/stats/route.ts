import { NextResponse } from 'next/server';
import { BackpackClient } from '@/app/lib/backpack';

export const dynamic = 'force-dynamic'; // Disable caching

export async function GET() {
  // Use BACKPACK_API_KEY from environment, NOT NEXT_PUBLIC
  // The .env.local file should have these variables.
  // Note: For Next.js App Router API Routes, we access process.env directly.
  const key = process.env.BACKPACK_API_KEY;
  const secret = process.env.BACKPACK_API_SECRET;

  if (!key || !secret) {
    // Return mock data if keys are missing (for dev preview without keys)
    // Or return error. User asked for "dados on chain via backpack api", so error is better to prompt config.
    // But to avoid breaking the UI completely, maybe a specific flag.
    console.error("Missing API Keys in Environment Variables (BACKPACK_API_KEY, BACKPACK_API_SECRET)");
    return NextResponse.json({ 
        connected: false, 
        error: 'API Keys not configured in .env' 
    }, { status: 200 }); 
  }

  try {
    const client = new BackpackClient(key, secret);
    
    const [balance, positions] = await Promise.all([
      client.getBalance(),
      client.getPositions()
    ]);

    const toNumber = (value: unknown, fallback = 0) => {
      const num = typeof value === 'number' ? value : Number.parseFloat(String(value));
      return Number.isFinite(num) ? num : fallback;
    };

    let totalBalance = 0;
    // Handle collateralQuery response (Unified)
    if (balance && typeof balance === 'object' && 'totalPortfolioValue' in balance && balance.totalPortfolioValue) {
        totalBalance = toNumber(balance.totalPortfolioValue);
    } else if (balance && typeof balance === 'object' && 'USDC' in balance && balance.USDC && typeof balance.USDC === 'object') {
        // Fallback for standard balanceQuery
        const usdc = balance.USDC as { available?: unknown; locked?: unknown };
        totalBalance = toNumber(usdc.available) + toNumber(usdc.locked);
    }
    
    let totalUnrealizedPnl = 0;
    let activePositions: Array<{
      asset: string;
      side: string;
      entry: string;
      mark: string;
      pnl: string;
      status: string;
    }> = [];

    if (Array.isArray(positions)) {
        activePositions = positions
          .map((pos) => {
            if (!pos || typeof pos !== 'object') return null;
            const data = pos as Record<string, unknown>;
            const pnl = toNumber(data.unrealizedPnl);
            totalUnrealizedPnl += pnl;
            
            let side = typeof data.side === 'string' ? data.side : '';
            if (!side && data.netQuantity !== undefined) {
                side = toNumber(data.netQuantity) > 0 ? "Long" : "Short";
            }

            return {
                asset: typeof data.symbol === 'string' ? data.symbol : 'UNKNOWN',
                side: side || "Unknown",
                entry: toNumber(data.entryPrice).toFixed(2),
                mark: toNumber(data.markPrice).toFixed(2),
                pnl: pnl.toFixed(2),
                status: "RUNNING"
            };
        })
        .filter((pos): pos is NonNullable<typeof pos> => Boolean(pos));
    }

    return NextResponse.json({
        totalBalance: totalBalance.toFixed(2),
        totalPnl: totalUnrealizedPnl.toFixed(2),
        activePositions,
        connected: true
    });

  } catch (error: unknown) {
    console.error("Backpack API Route Error:", error);
    const message = error instanceof Error ? error.message : 'Unexpected error';
    return NextResponse.json({ error: message, connected: false }, { status: 500 });
  }
}
