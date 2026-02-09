"use client"

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Calculator, Percent, BarChart3, Info } from 'lucide-react'

export default function AirdropCalculator() {
  // Input States
  const [userPoints, setUserPoints] = useState<string>("1000")
  const [fdvBillions, setFdvBillions] = useState(0.7)
  const [airdropPercent, setAirdropPercent] = useState(25)
  const [totalSeasonPoints] = useState(423.77)

  // Constants
  const SEASON_START = new Date("2025-11-20")
  const SEASON_END = new Date("2026-01-28")
  const TODAY = new Date("2026-01-29") // Matches env date roughly
  
  // Progress Calculation
  const totalDuration = SEASON_END.getTime() - SEASON_START.getTime()
  const elapsed = TODAY.getTime() - SEASON_START.getTime()
  const progress = Math.min(Math.max((elapsed / totalDuration) * 100, 0), 100)
  const daysElapsed = Math.min(Math.floor(elapsed / (1000 * 60 * 60 * 24)), 70)

  // Calculations
  const numericPoints = parseFloat(userPoints.replace(/,/g, '')) || 0
  const totalAirdropValue = (fdvBillions * 1_000_000_000) * (airdropPercent / 100)
  const valuePerPoint = totalSeasonPoints > 0 ? totalAirdropValue / (totalSeasonPoints * 1_000_000) : 0
  const estimatedUserValue = numericPoints * valuePerPoint

  const t = {
    epoch_badge: "LIQUIDITY EPOCH 4",
    title_projected: "PROJECTED",
    title_yield: "YIELD",
    epoch_status: "Epoch 4 Status",
    window_active: "Allocation window active",
    your_score: "Your Volume Score",
    fdv_label: "FDV (Fully Diluted Valuation)",
    billion: "Billion",
    allocation_label: "% Allocation",
    supply: "Supply",
    conservative: "Conservative (10%)",
    optimistic: "Optimistic (50%)",
    point_val: "1 point ≈",
    proj_alloc: "PROJECTED ALLOCATION",
    est_value: "ESTIMATED PARTNERSHIP VALUE",
    score: "SCORE",
    fdv: "FDV",
    alloc: "ALLOCATION",
    analysis: "Analysis by",
    partner_intel: "Partner Intelligence"
  }

  return (
    <section className="py-16 md:py-20 bg-zinc-950 relative overflow-hidden">
      <div className="container mx-auto px-4 relative z-10">
        <div className="mb-12 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-blue-500/20 bg-blue-500/10 text-blue-400 text-xs font-mono mb-4">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
            </span>
            {t.epoch_badge}
          </div>
          <h2 className="text-3xl md:text-4xl font-bold font-mono text-white mb-4 tracking-tight">
            {t.title_projected} <span className="text-blue-500">{t.title_yield}</span>
          </h2>
        </div>

        <div className="max-w-5xl mx-auto">
          {/* Season Progress Card */}
          <div className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-6 mb-8 backdrop-blur-sm">
            <div className="flex justify-between items-end mb-2">
              <div>
                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                  <span className="text-blue-400"></span> {t.epoch_status}
                </h3>
                <p className="text-zinc-500 text-xs font-mono mt-1">
                  20 Nov 2025 → 28 Jan 2026 • {totalSeasonPoints}M volume units
                </p>
              </div>
              <div className="text-right">
                <span className="text-2xl font-bold text-white">{progress.toFixed(1)}%</span>
              </div>
            </div>
            <div className="h-3 bg-zinc-800 rounded-full overflow-hidden mb-2">
              <motion.div 
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                className="h-full bg-linear-to-r from-blue-600 to-cyan-400 rounded-full"
              />
            </div>
            <div className="flex justify-between text-xs font-mono text-zinc-500">
              <span>Day {daysElapsed} / 70</span>
              <span className="text-blue-400">{t.window_active}</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
            {/* Input Panel */}
            <div className="md:col-span-5 space-y-6">
              <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 space-y-6">
                {/* Your Points */}
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-2 flex items-center gap-2">
                    <span className="text-blue-400"></span> {t.your_score}
                  </label>
                  <div className="relative">
                    <input 
                      type="text" 
                      value={userPoints}
                      onChange={(e) => {
                        // Allow only numbers and decimals
                        const val = e.target.value.replace(/[^0-9.]/g, '')
                        setUserPoints(val)
                      }}
                      className="w-full bg-zinc-950 border border-zinc-700 rounded-xl py-4 px-4 text-2xl font-bold text-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all"
                      placeholder="0"
                    />
                  </div>
                </div>

                {/* FDV */}
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-2 flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-blue-400" />
                    {t.fdv_label}
                  </label>
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <input 
                        type="number" 
                        value={fdvBillions}
                        onChange={(e) => setFdvBillions(Number(e.target.value))}
                        step="0.1"
                        className="w-full bg-zinc-950 border border-zinc-700 rounded-xl py-4 px-4 text-2xl font-bold text-white focus:border-blue-500 outline-none transition-all"
                      />
                    </div>
                    <div className="bg-zinc-800 border border-zinc-700 rounded-xl px-4 flex items-center justify-center min-w-[100px]">
                      <span className="text-white font-medium">{t.billion}</span>
                    </div>
                  </div>
                </div>

                {/* Airdrop % */}
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <label className="block text-sm font-medium text-zinc-300 flex items-center gap-2">
                      <Percent className="w-4 h-4 text-blue-400" />
                      {t.allocation_label}
                    </label>
                    <span className="text-blue-400 font-bold">{airdropPercent}% {t.supply}</span>
                  </div>
                  <input 
                    type="range" 
                    min="1" 
                    max="100" 
                    value={airdropPercent}
                    onChange={(e) => setAirdropPercent(Number(e.target.value))}
                    className="w-full h-2 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                  />
                  <div className="flex justify-between text-xs text-zinc-500 mt-2 font-mono">
                    <span>{t.conservative}</span>
                    <span>{t.optimistic}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Results Panel */}
            <div className="md:col-span-7">
              <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8 h-full relative overflow-hidden flex flex-col justify-between">
                <div className="absolute top-0 right-0 p-4 opacity-20">
                   <Calculator className="w-32 h-32 text-blue-500" />
                </div>
                
                <div>
                  <div className="flex justify-between items-start mb-8">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center border border-red-500/30">
                        <span className="text-red-500 text-lg"></span>
                      </div>
                      <div>
                        <h3 className="font-bold text-white text-lg">Backpack</h3>
                        <div className="text-zinc-400 text-sm font-mono">{t.point_val} ${valuePerPoint.toFixed(2)}</div>
                      </div>
                    </div>
                    <div className="text-right">
                       <span className="text-xs font-mono text-zinc-500 block">{t.proj_alloc}</span>
                    </div>
                  </div>

                  <div className="text-center py-8">
                    <div className="text-zinc-500 text-sm font-mono mb-2">{t.est_value}</div>
                    <div className="text-4xl sm:text-5xl md:text-7xl font-bold text-emerald-400 tracking-tighter break-words">
                      ${estimatedUserValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 mt-8">
                  <div className="bg-zinc-950/50 rounded-xl p-4 border border-zinc-800 text-center">
                    <div className="text-xs text-zinc-500 font-mono mb-1">{t.score}</div>
                    <div className="text-white font-bold">{numericPoints.toLocaleString()}</div>
                  </div>
                  <div className="bg-zinc-950/50 rounded-xl p-4 border border-zinc-800 text-center">
                    <div className="text-xs text-zinc-500 font-mono mb-1">{t.fdv}</div>
                    <div className="text-white font-bold">${fdvBillions}B</div>
                  </div>
                  <div className="bg-zinc-950/50 rounded-xl p-4 border border-zinc-800 text-center">
                    <div className="text-xs text-zinc-500 font-mono mb-1">{t.alloc}</div>
                    <div className="text-white font-bold">{airdropPercent}%</div>
                  </div>
                </div>

                <div className="mt-8 pt-6 border-t border-zinc-800/50">
                  <div className="flex justify-between items-center">
                    <div className="text-xs text-zinc-500 font-mono">
                      {t.analysis} <span className="text-blue-400">{t.partner_intel}</span>
                    </div>
                    <button 
                      onClick={() => window.print()}
                      className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2"
                    >
                      <Info className="w-4 h-4" />
                      Export Analysis
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
