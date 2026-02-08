"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { ShieldCheck, Hash, FileText, CheckCircle2, ExternalLink, Copy, Activity, Server, Database } from "lucide-react";
import Link from "next/link";

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

export default function ProofPage() {
  const [data, setData] = useState<ProofData | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetch('/api/proof/latest')
      .then(res => res.json())
      .then(json => {
        if (json.ok) setData(json.data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const copyHash = () => {
    if (data?.hash) {
      navigator.clipboard.writeText(data.hash);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center py-20">
        <ShieldCheck className="w-16 h-16 text-zinc-700 mx-auto mb-4" />
        <h2 className="text-xl font-mono text-zinc-500">No Proof Generated Yet</h2>
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-12">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold font-mono text-white flex items-center gap-2">
            <ShieldCheck className="w-6 h-6 text-emerald-500" />
            PROOF OF VOLUME
          </h1>
          <p className="text-zinc-400 text-sm font-mono mt-1">
            Cryptographic verification of trading performance.
          </p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-full">
          <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
          <span className="text-xs font-mono text-emerald-500 font-bold">ON-CHAIN VERIFIED</span>
        </div>
      </div>

      {/* Main Hash Card */}
      <motion.div 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 p-8 opacity-5">
          <Hash className="w-64 h-64" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 relative z-10">
          <div>
            <h3 className="text-xs font-mono text-zinc-500 uppercase tracking-wider mb-2">Report Hash (SHA256)</h3>
            <div className="flex items-center gap-3 bg-black/50 p-3 rounded border border-zinc-800 font-mono text-sm text-zinc-300 break-all">
              <Hash className="w-4 h-4 text-zinc-600 shrink-0" />
              <span className="truncate">{data.hash}</span>
              <button onClick={copyHash} className="p-1 hover:text-white transition-colors">
                {copied ? <CheckCircle2 className="w-4 h-4 text-emerald-500" /> : <Copy className="w-4 h-4" />}
              </button>
            </div>
            <p className="text-xs text-zinc-600 mt-2 font-mono">
              Generated from file: <span className="text-zinc-500">{data.filename}</span>
            </p>
          </div>

          <div>
            <h3 className="text-xs font-mono text-zinc-500 uppercase tracking-wider mb-2">Validator Signature</h3>
            <div className="flex items-center gap-3 bg-black/50 p-3 rounded border border-zinc-800 font-mono text-sm text-emerald-400 break-all">
              <Activity className="w-4 h-4 text-emerald-600 shrink-0" />
              <span className="truncate">{data.signature}</span>
              <a 
                href={`https://solscan.io/tx/${data.signature}?cluster=devnet`} 
                target="_blank" 
                rel="noopener noreferrer"
                className="p-1 hover:text-white transition-colors"
              >
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>
            <p className="text-xs text-zinc-600 mt-2 font-mono">
              Signed by AgentWallet on Solana Network
            </p>
          </div>
        </div>
      </motion.div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {Object.entries(data.metrics).map(([key, value], i) => (
          <motion.div
            key={key}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="bg-zinc-900 border border-zinc-800 p-4 rounded-lg"
          >
            <h4 className="text-xs font-mono text-zinc-500 uppercase mb-1">{key}</h4>
            <div className="text-lg font-bold font-mono text-white">{value}</div>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Top Assets */}
        <div className="lg:col-span-1 bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
          <div className="p-4 border-b border-zinc-800 flex items-center gap-2">
            <Database className="w-4 h-4 text-purple-500" />
            <h3 className="font-mono text-sm font-bold text-white">TOP ASSETS</h3>
          </div>
          <div className="divide-y divide-zinc-800">
            {data.topAssets.map((asset, i) => (
              <div key={i} className="p-3 flex justify-between items-center hover:bg-zinc-800/50 transition-colors">
                <span className="font-mono text-sm text-zinc-300">{asset.asset}</span>
                <div className="text-right">
                  <div className="font-mono text-xs text-white">{asset.volume}</div>
                  <div className="font-mono text-[10px] text-zinc-500">{asset.trades} trades</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Audit Trail */}
        <div className="lg:col-span-2 bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
          <div className="p-4 border-b border-zinc-800 flex items-center gap-2">
            <Server className="w-4 h-4 text-blue-500" />
            <h3 className="font-mono text-sm font-bold text-white">AUDIT TRAIL (Last 5 Fills)</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-zinc-950 text-zinc-500 font-mono text-xs uppercase">
                <tr>
                  <th className="px-4 py-3">Time</th>
                  <th className="px-4 py-3">Symbol</th>
                  <th className="px-4 py-3">Side</th>
                  <th className="px-4 py-3 text-right">Price</th>
                  <th className="px-4 py-3 text-right">Qty</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800 font-mono text-xs text-zinc-300">
                {data.auditTrail.map((log, i) => (
                  <tr key={i} className="hover:bg-zinc-800/30 transition-colors">
                    <td className="px-4 py-3 text-zinc-500">{log.time.split(' ')[1]}</td>
                    <td className="px-4 py-3">{log.symbol}</td>
                    <td className={`px-4 py-3 ${log.side === 'BUY' ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {log.side}
                    </td>
                    <td className="px-4 py-3 text-right">{log.price}</td>
                    <td className="px-4 py-3 text-right">{log.quantity}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
