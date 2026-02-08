"use client";

import { useState, useEffect } from "react";
import { CreditCard, CheckCircle, AlertTriangle, Shield, Calendar, RefreshCw, Star, Activity } from "lucide-react";
import Link from "next/link";

interface License {
  id: string;
  walletAddress: string;
  tierId: string;
  status: string;
  issuedAt: string;
  paymentId: string;
}

export default function SubscriptionPage() {
  const [license, setLicense] = useState<License | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [wallet, setWallet] = useState<string | null>(null);

  const fetchLicense = async () => {
    setLoading(true);
    setError(null);
    try {
        // First check cookies for wallet
        const getCookie = (name: string) => {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) return parts.pop()?.split(';').shift();
        };
        const walletCookie = getCookie('obi_access_wallet');
        
        if (!walletCookie) {
            setError("Wallet not connected. Please go through the gatekeeper check.");
            setLoading(false);
            return;
        }
        setWallet(walletCookie);

        const res = await fetch('/api/licenses/status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ walletAddress: walletCookie })
        });
        
        const data = await res.json();
        if (data.ok) {
            setLicense(data.license);
        } else {
            setLicense(null);
        }

    } catch (e) {
        console.error("Failed to fetch license", e);
        setError("Unable to retrieve license details.");
    } finally {
        setLoading(false);
    }
  };

  useEffect(() => {
    fetchLicense();
  }, []);

  const formatDate = (isoString: string) => {
    return new Date(isoString).toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
  };

  const getTierDetails = (tierId: string) => {
      switch(tierId.toLowerCase()) {
          case 'scout':
              return { name: 'SCOUT', color: 'text-blue-400', border: 'border-blue-500/50', bg: 'bg-blue-500/10' };
          case 'commander':
              return { name: 'COMMANDER', color: 'text-purple-400', border: 'border-purple-500/50', bg: 'bg-purple-500/10' };
          case 'architect':
              return { name: 'ARCHITECT', color: 'text-yellow-400', border: 'border-yellow-500/50', bg: 'bg-yellow-500/10' };
          default:
              return { name: tierId.toUpperCase(), color: 'text-zinc-400', border: 'border-zinc-500/50', bg: 'bg-zinc-500/10' };
      }
  };

  return (
    <div className="space-y-8">
      
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold font-mono text-white">MY SUBSCRIPTION</h1>
          <p className="text-zinc-400 text-sm font-mono">Manage your license and access tiers.</p>
        </div>
        <button 
            onClick={fetchLicense}
            disabled={loading}
            className="p-2 hover:bg-zinc-800 rounded-full transition-colors text-zinc-500 hover:text-white"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        
        {/* License Card */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 relative overflow-hidden">
             {/* Background Pattern */}
            <div className="absolute top-0 right-0 p-8 opacity-5">
                <Shield className="w-32 h-32" />
            </div>

            <h3 className="text-sm font-bold text-white font-mono mb-6 flex items-center gap-2 relative z-10">
                <CreditCard className="w-4 h-4 text-emerald-500" />
                ACTIVE LICENSE
            </h3>

            {loading ? (
                <div className="py-12 flex flex-col items-center justify-center text-zinc-500 font-mono text-sm">
                    <RefreshCw className="w-8 h-8 animate-spin mb-2 opacity-50" />
                    <span>Verifying License Status...</span>
                </div>
            ) : error ? (
                <div className="py-8 text-center">
                    <AlertTriangle className="w-8 h-8 text-yellow-500 mx-auto mb-2" />
                    <p className="text-zinc-400 font-mono text-sm mb-4">{error}</p>
                    <Link href="/" className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded font-mono text-xs">Return to Gatekeeper</Link>
                </div>
            ) : license ? (
                <div className="space-y-6 relative z-10">
                    <div className={`p-4 rounded-lg border ${getTierDetails(license.tierId).border} ${getTierDetails(license.tierId).bg}`}>
                        <div className="flex justify-between items-start mb-2">
                            <span className="text-xs font-mono text-zinc-400 uppercase tracking-wider">Current Tier</span>
                            <Star className={`w-4 h-4 ${getTierDetails(license.tierId).color}`} />
                        </div>
                        <div className={`text-2xl font-bold font-mono ${getTierDetails(license.tierId).color}`}>
                            {getTierDetails(license.tierId).name}
                        </div>
                    </div>

                    <div className="space-y-3 font-mono text-sm">
                        <div className="flex justify-between py-2 border-b border-zinc-800/50">
                            <span className="text-zinc-500">Status</span>
                            <span className="flex items-center gap-2 text-emerald-400">
                                <CheckCircle className="w-3 h-3" />
                                {license.status.toUpperCase()}
                            </span>
                        </div>
                        <div className="flex justify-between py-2 border-b border-zinc-800/50">
                            <span className="text-zinc-500">Wallet</span>
                            <span className="text-zinc-300">
                                {wallet ? `${wallet.slice(0, 6)}...${wallet.slice(-4)}` : '---'}
                            </span>
                        </div>
                        <div className="flex justify-between py-2 border-b border-zinc-800/50">
                            <span className="text-zinc-500">Issued Date</span>
                            <span className="text-zinc-300">{formatDate(license.issuedAt)}</span>
                        </div>
                         <div className="flex justify-between py-2 border-b border-zinc-800/50">
                            <span className="text-zinc-500">License ID</span>
                            <span className="text-zinc-500 text-xs">{license.id.slice(0, 12)}...</span>
                        </div>
                    </div>

                    <div className="pt-4">
                        <button className="w-full py-2 border border-zinc-700 hover:bg-zinc-800 text-zinc-300 rounded font-mono text-xs transition-colors">
                            VIEW INVOICE
                        </button>
                    </div>
                </div>
            ) : (
                <div className="py-12 text-center relative z-10">
                    <div className="w-16 h-16 bg-zinc-800 rounded-full flex items-center justify-center mx-auto mb-4">
                        <Shield className="w-8 h-8 text-zinc-600" />
                    </div>
                    <h4 className="text-white font-bold font-mono mb-2">No Active License</h4>
                    <p className="text-zinc-500 text-sm font-mono mb-6 max-w-xs mx-auto">
                        You are currently viewing the dashboard in Guest Mode. Upgrade to unlock full features.
                    </p>
                    <Link href="/marketplace" className="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-mono text-sm transition-colors inline-block">
                        BROWSE PLANS
                    </Link>
                </div>
            )}
        </div>

        {/* Benefits / Usage */}
        <div className="space-y-8">
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
                <h3 className="text-sm font-bold text-white font-mono mb-6 flex items-center gap-2">
                    <Activity className="w-4 h-4 text-purple-500" />
                    USAGE METRICS
                </h3>
                
                <div className="space-y-4">
                     <div>
                        <div className="flex justify-between text-xs font-mono text-zinc-400 mb-1">
                            <span>API CALLS (Daily)</span>
                            <span>{license ? "142 / 1000" : "0 / 100"}</span>
                        </div>
                        <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
                            <div className="h-full bg-purple-500 w-[14%]" />
                        </div>
                     </div>
                     <div>
                        <div className="flex justify-between text-xs font-mono text-zinc-400 mb-1">
                            <span>REPORT ACCESS</span>
                            <span>{license ? "UNLIMITED" : "LIMITED"}</span>
                        </div>
                        <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
                            <div className={`h-full ${license ? "bg-emerald-500 w-full" : "bg-yellow-500 w-[20%]"}`} />
                        </div>
                     </div>
                </div>
            </div>

            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
                 <h3 className="text-sm font-bold text-white font-mono mb-4 flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-blue-500" />
                    NEXT RENEWAL
                </h3>
                <div className="flex items-center justify-between">
                     <div>
                        <div className="text-2xl font-bold text-white font-mono">LIFETIME</div>
                        <div className="text-xs text-zinc-500 font-mono">One-time payment active</div>
                     </div>
                     <div className="p-3 bg-zinc-800 rounded-lg opacity-50">
                        <Shield className="w-6 h-6 text-zinc-400" />
                     </div>
                </div>
            </div>
        </div>

      </div>
    </div>
  );
}
