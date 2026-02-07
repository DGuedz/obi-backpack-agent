"use client";

import { Activity, DollarSign, TrendingUp, BarChart2, Shield, RefreshCw } from "lucide-react";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import OnChainReports from "../components/OnChainReports";
import ObiChatInterface from "../components/ObiChatInterface";

interface ActivePosition {
  asset: string;
  side?: string;
  entry: string;
  mark: string;
  pnl: string;
  status: string;
}

interface DashboardStats {
  totalBalance: string;
  totalPnl: string;
  connected: boolean;
  activePositions: ActivePosition[];
}

export default function DashboardHome() {
  const [stats, setStats] = useState<DashboardStats>({
    totalBalance: "---",
    totalPnl: "---",
    connected: false,
    activePositions: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch('/api/backpack/stats');
        const data = await res.json();
        if (data.connected) {
            setStats(data);
        }
      } catch (e) {
        console.error("Failed to fetch dashboard stats", e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
    // Refresh every 5 seconds
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-8">
      
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold font-mono text-white">WORKROOM OVERVIEW</h1>
          <p className="text-zinc-400 text-sm font-mono">Real-time clone telemetry.</p>
        </div>
        <div className={`flex items-center gap-2 px-3 py-1 rounded-full border ${stats.connected ? "bg-emerald-950/30 border-emerald-900/50" : "bg-red-950/30 border-red-900/50"}`}>
          <span className="relative flex h-2 w-2">
            <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${stats.connected ? "bg-emerald-400" : "bg-red-400"}`}></span>
            <span className={`relative inline-flex rounded-full h-2 w-2 ${stats.connected ? "bg-emerald-500" : "bg-red-500"}`}></span>
          </span>
          <span className={`text-xs font-mono ${stats.connected ? "text-emerald-500" : "text-red-500"}`}>
            {stats.connected ? "SYSTEM ONLINE" : "API DISCONNECTED"}
          </span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: "TOTAL BALANCE", value: loading ? "..." : `$${stats.totalBalance}`, sub: "USDC Equity", icon: DollarSign, color: "text-emerald-400" },
          { label: "UNREALIZED PNL", value: loading ? "..." : (parseFloat(stats.totalPnl) > 0 ? `+$${stats.totalPnl}` : `$${stats.totalPnl}`), sub: "Open Positions", icon: BarChart2, color: parseFloat(stats.totalPnl) >= 0 ? "text-emerald-400" : "text-red-400" },
          { label: "WIN RATE", value: "68.5%", sub: "142 Trades", icon: TrendingUp, color: "text-yellow-400" },
          { label: "RISK EXPOSURE", value: "LOW", sub: "Leverage 5x", icon: Shield, color: "text-purple-400" },
        ].map((stat, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="p-6 bg-zinc-900 border border-zinc-800 rounded-xl"
          >
            <div className="flex justify-between items-start mb-4">
              <span className="text-xs text-zinc-500 font-mono tracking-wider">{stat.label}</span>
              <stat.icon className={`w-4 h-4 ${stat.color}`} />
            </div>
            <div className={`text-2xl font-bold font-mono text-white mb-1`}>{stat.value}</div>
            <div className="text-xs text-zinc-500 font-mono">{stat.sub}</div>
          </motion.div>
        ))}
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* On-Chain Reports & Intelligence */}
        <div className="lg:col-span-2 space-y-8">
            <OnChainReports />
        </div>

        {/* OBI Chat & Tools */}
        <div className="lg:col-span-1 space-y-8">
            <ObiChatInterface />
            
            {/* Quick Actions (Simulated) */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
                <h3 className="text-sm font-bold text-white font-mono mb-4 flex items-center gap-2">
                    <Activity className="w-4 h-4 text-purple-500" />
                    SYSTEM STATUS
                </h3>
                <div className="space-y-3">
                    <div className="flex justify-between text-xs font-mono">
                        <span className="text-zinc-500">GATEKEEPER</span>
                        <span className="text-emerald-500">ACTIVE</span>
                    </div>
                    <div className="flex justify-between text-xs font-mono">
                        <span className="text-zinc-500">RUGCHECK API</span>
                        <span className="text-emerald-500">CONNECTED</span>
                    </div>
                    <div className="flex justify-between text-xs font-mono">
                        <span className="text-zinc-500">MERKLE ROOT</span>
                        <span className="text-zinc-400">SYNCED</span>
                    </div>
                </div>
            </div>
        </div>

      </div>
    </div>
  );
}
