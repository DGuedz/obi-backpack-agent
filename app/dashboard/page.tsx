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

interface TriageItem {
  applicationId: string;
  receivedAt: string;
  walletAddress: string;
  status: "pending" | "review" | "approved" | "rejected";
  triage: { score: number; tier: string; tags: string[] };
  gatekeeper?: { allowed?: boolean; mode?: string };
}

interface ServiceStatus {
  overall?: { ok?: boolean; status?: string };
  services?: {
    gatekeeper?: { ok?: boolean; status?: string; latency?: number; details?: Record<string, unknown> };
    reports?: { ok?: boolean; status?: string; latency?: number; details?: Record<string, unknown> };
    payments?: { ok?: boolean; status?: string; latency?: number; details?: Record<string, unknown> };
    mentorship?: { ok?: boolean; status?: string; latency?: number; details?: Record<string, unknown> };
    backpack?: { ok?: boolean; status?: string; latency?: number; details?: Record<string, unknown> };
  };
  gatekeeper?: { mintConfigured?: boolean; rpcConfigured?: boolean };
  reports?: { latestGeneratedAt?: string | null };
  payments?: { cieloConfigured?: boolean };
  mentorship?: { googleConfigured?: boolean };
  backpack?: { configured?: boolean };
}

export default function DashboardHome() {
  const [stats, setStats] = useState<DashboardStats>({
    totalBalance: "---",
    totalPnl: "---",
    connected: false,
    activePositions: []
  });
  const [loading, setLoading] = useState(true);
  const [triageItems, setTriageItems] = useState<TriageItem[]>([]);
  const [triageLoading, setTriageLoading] = useState(true);
  const [triageError, setTriageError] = useState<string | null>(null);
  const [serviceStatus, setServiceStatus] = useState<ServiceStatus | null>(null);

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

  useEffect(() => {
    const loadStatus = async () => {
      try {
        const res = await fetch("/api/status");
        const data = await res.json();
        if (res.ok && data?.ok) {
          setServiceStatus(data.status);
          try {
            localStorage.setItem(
              "obi_service_status_cache",
              JSON.stringify({ ts: Date.now(), status: data.status })
            );
          } catch {
            void 0;
          }
        }
      } catch {
        setServiceStatus(null);
      }
    };
    try {
      const cached = localStorage.getItem("obi_service_status_cache");
      if (cached) {
        const parsed = JSON.parse(cached);
        if (parsed?.ts && parsed?.status && Date.now() - parsed.ts < 60000) {
          setServiceStatus(parsed.status);
        }
      }
    } catch {
      void 0;
    }
    loadStatus();
    const interval = setInterval(loadStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const loadTriage = async () => {
      setTriageLoading(true);
      setTriageError(null);
      try {
        const res = await fetch("/api/triage");
        const data = await res.json();
        if (!res.ok || !data?.ok) {
          setTriageError("Falha ao carregar fila de triagem.");
          setTriageLoading(false);
          return;
        }
        setTriageItems(data.items || []);
      } catch {
        setTriageError("Falha ao carregar fila de triagem.");
      } finally {
        setTriageLoading(false);
      }
    };
    loadTriage();
  }, []);

  const updateTriageStatus = async (applicationId: string, status: TriageItem["status"]) => {
    try {
      const res = await fetch("/api/triage", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ applicationId, status, reviewer: "dashboard" })
      });
      const data = await res.json();
      if (!res.ok || !data?.ok) {
        return;
      }
      setTriageItems((prev) =>
        prev.map((item) => (item.applicationId === applicationId ? { ...item, status } : item))
      );
    } catch {
      return;
    }
  };

  const gatekeeperOk = Boolean(
    serviceStatus?.services?.gatekeeper?.ok ??
      (serviceStatus?.gatekeeper?.mintConfigured && serviceStatus?.gatekeeper?.rpcConfigured)
  );
  const reportsStatus =
    serviceStatus?.services?.reports?.status ??
    (serviceStatus?.reports?.latestGeneratedAt ? "ok" : "pending");
  const paymentsOk = Boolean(
    serviceStatus?.services?.payments?.ok ?? serviceStatus?.payments?.cieloConfigured
  );
  const mentorshipOk = Boolean(
    serviceStatus?.services?.mentorship?.ok ?? serviceStatus?.mentorship?.googleConfigured
  );
  const backpackOk = Boolean(
    serviceStatus?.services?.backpack?.ok ?? serviceStatus?.backpack?.configured
  );
  const overallOk = Boolean(
    serviceStatus?.overall?.ok ??
      (gatekeeperOk && reportsStatus === "ok" && paymentsOk && mentorshipOk && backpackOk)
  );
  const reportsLabel =
    reportsStatus === "ok" ? "READY" : reportsStatus === "stale" ? "STALE" : "PENDING";

  const renderLatency = (ms?: number) => {
    if (ms === undefined) return null;
    return <span className="text-[10px] text-zinc-600 font-mono ml-2">({ms}ms)</span>;
  };

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
            
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
                <h3 className="text-sm font-bold text-white font-mono mb-4 flex items-center gap-2">
                    <Activity className="w-4 h-4 text-purple-500" />
                    SYSTEM STATUS
                </h3>
                <div className="space-y-3">
                    <div className="flex justify-between text-xs font-mono">
                        <span className="text-zinc-500">OVERALL</span>
                        <span className={overallOk ? "text-emerald-500" : "text-yellow-400"}>
                          {overallOk ? "HEALTHY" : "DEGRADED"}
                        </span>
                    </div>
                    <div className="flex justify-between text-xs font-mono">
                        <span className="text-zinc-500">GATEKEEPER</span>
                        <div className="flex items-center">
                            <span className={gatekeeperOk ? "text-emerald-500" : "text-yellow-400"}>
                            {gatekeeperOk ? "ACTIVE" : "CONFIG REQUIRED"}
                            </span>
                            {renderLatency(serviceStatus?.services?.gatekeeper?.latency)}
                        </div>
                    </div>
                    <div className="flex justify-between text-xs font-mono">
                        <span className="text-zinc-500">REPORT PIPELINE</span>
                        <div className="flex items-center">
                            <span className={reportsStatus === "ok" ? "text-emerald-500" : "text-yellow-400"}>
                            {reportsLabel}
                            </span>
                            {renderLatency(serviceStatus?.services?.reports?.latency)}
                        </div>
                    </div>
                    <div className="flex justify-between text-xs font-mono">
                        <span className="text-zinc-500">PAYMENTS</span>
                        <div className="flex items-center">
                            <span className={paymentsOk ? "text-emerald-500" : "text-yellow-400"}>
                            {paymentsOk ? "CONNECTED" : "MOCK"}
                            </span>
                            {renderLatency(serviceStatus?.services?.payments?.latency)}
                        </div>
                    </div>
                    <div className="flex justify-between text-xs font-mono">
                        <span className="text-zinc-500">MENTORSHIP</span>
                        <div className="flex items-center">
                            <span className={mentorshipOk ? "text-emerald-500" : "text-yellow-400"}>
                            {mentorshipOk ? "CONNECTED" : "OFFLINE"}
                            </span>
                            {renderLatency(serviceStatus?.services?.mentorship?.latency)}
                        </div>
                    </div>
                    <div className="flex justify-between text-xs font-mono">
                        <span className="text-zinc-500">BACKPACK</span>
                        <div className="flex items-center">
                            <span className={backpackOk ? "text-emerald-500" : "text-yellow-400"}>
                            {backpackOk ? "CONNECTED" : "OFFLINE"}
                            </span>
                            {renderLatency(serviceStatus?.services?.backpack?.latency)}
                        </div>
                    </div>
                </div>
            </div>

            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
                        <RefreshCw className={`w-4 h-4 ${triageLoading ? "animate-spin" : ""}`} />
                        TRIAGE QUEUE
                    </h3>
                </div>
                {triageError && (
                  <div className="text-xs text-red-400 mb-3">{triageError}</div>
                )}
                {triageLoading ? (
                  <div className="text-xs text-zinc-500 font-mono">Loading triage...</div>
                ) : triageItems.length === 0 ? (
                  <div className="text-xs text-zinc-500 font-mono">No applications in queue.</div>
                ) : (
                  <div className="space-y-3">
                    {triageItems.slice(0, 5).map((item) => {
                      const triage = item.triage || { score: 0, tier: "standard", tags: [] };
                      const statusColor =
                        item.status === "approved"
                          ? "text-emerald-400"
                          : item.status === "rejected"
                          ? "text-red-400"
                          : item.status === "review"
                          ? "text-yellow-400"
                          : "text-zinc-400";
                      return (
                        <div key={item.applicationId} className="border border-zinc-800 rounded-lg p-3 bg-black/40">
                          <div className="flex justify-between items-center text-[10px] font-mono text-zinc-500">
                            <span>{new Date(item.receivedAt).toLocaleDateString()}</span>
                            <span className={statusColor}>{item.status.toUpperCase()}</span>
                          </div>
                          <div className="text-xs font-mono text-zinc-300 mt-1">
                            {item.walletAddress.slice(0, 6)}...{item.walletAddress.slice(-4)}
                          </div>
                          <div className="text-[10px] text-zinc-500 mt-1">
                            Score {triage.score} · {triage.tier.toUpperCase()}
                          </div>
                          <div className="flex gap-2 mt-2">
                            <button
                              onClick={() => updateTriageStatus(item.applicationId, "review")}
                              className="px-2 py-1 text-[10px] font-mono border border-zinc-700 rounded text-zinc-400 hover:text-white hover:bg-zinc-800"
                            >
                              REVIEW
                            </button>
                            <button
                              onClick={() => updateTriageStatus(item.applicationId, "approved")}
                              className="px-2 py-1 text-[10px] font-mono border border-emerald-700 rounded text-emerald-300 hover:bg-emerald-900/30"
                            >
                              APPROVE
                            </button>
                            <button
                              onClick={() => updateTriageStatus(item.applicationId, "rejected")}
                              className="px-2 py-1 text-[10px] font-mono border border-red-700 rounded text-red-300 hover:bg-red-900/30"
                            >
                              REJECT
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
            </div>
        </div>

      </div>
    </div>
  );
}
