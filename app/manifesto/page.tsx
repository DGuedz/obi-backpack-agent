"use client";

import { motion } from "framer-motion";
import { ArrowLeft, Terminal, Shield, Cpu, Code, Users, Zap, Wallet } from "lucide-react";
import Link from "next/link";
import CreatorCard from "../components/CreatorCard";

export default function ManifestoPage() {
  return (
    <div className="min-h-screen bg-black text-white font-mono selection:bg-emerald-500/30">
      
      {/* Navigation */}
      <nav className="sticky top-0 z-50 border-b border-zinc-800 bg-black/80 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors">
            <ArrowLeft className="w-4 h-4" />
            <span>BACK TO TERMINAL</span>
          </Link>
          <div className="flex items-center gap-2 text-emerald-500 font-bold">
            <Terminal className="w-4 h-4" />
            <span>PARTNER.MFST</span>
          </div>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto px-6 py-12 md:py-20 space-y-20">

        {/* Header */}
        <header className="space-y-6 border-b border-zinc-800 pb-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/30 border border-emerald-900 text-emerald-400 text-xs"
          >
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            ECOSYSTEM V4.0
          </motion.div>
          
          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-4xl md:text-6xl font-bold tracking-tight"
          >
            PARTNER ECOSYSTEM: <br/>
            <span className="text-zinc-500">Scale Liquidity. Master the Game.</span>
          </motion.h1>
          <p className="text-xl text-zinc-400 max-w-2xl">
            Connect to the most advanced liquidity infrastructure. Here, execution quality defines everything.
          </p>
        </header>

        {/* Introduction */}
        <section className="space-y-8">
          <motion.div 
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-8 md:p-10 relative overflow-hidden"
          >
            <div className="absolute top-0 right-0 p-4 opacity-10">
              <Shield className="w-32 h-32" />
            </div>
            
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
              <span className="text-emerald-500">01.</span> Liquidity as a Service (LaaS)
            </h2>
            
            <blockquote className="border-l-4 border-emerald-500 pl-4 italic text-zinc-400 mb-8 text-lg">
              &quot;We don't sell promises. We deliver structural advantage.&quot;
            </blockquote>

            <div className="space-y-6 text-zinc-300 leading-relaxed">
              <p>
                The <strong className="text-white">PARTNER ECOSYSTEM</strong> is for those who understand that the market rewards consistency, precision, and alignment.
              </p>
              <p>
                Your liquidity provision is adjusted to <strong className="text-white">your risk design</strong>:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Are you <strong className="text-emerald-400">Aggressive</strong>?</li>
                <li><strong className="text-blue-400">Defensive</strong>?</li>
                <li><strong className="text-yellow-400">Strategic Conservative</strong>?</li>
              </ul>
              <p className="mt-4">
                Here, your operation is calibrated by a <strong>specialized autonomous agent</strong>, aligned with your profile, working 24/7 for you. You talk to your agent. It executes. The system learns.
              </p>
            </div>
          </motion.div>
        </section>

        {/* Elite Access */}
        <section className="space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
             <div className="p-8 border border-zinc-800 rounded-xl bg-gradient-to-br from-black to-zinc-900">
                <h3 className="text-2xl font-bold text-white mb-4">Elite Access. Institutional Desk.</h3>
                <p className="text-zinc-400 mb-6">
                  This is <strong>AA’s Elite</strong>. You sit where normally no one is invited.
                </p>
                <ul className="space-y-3 text-sm text-zinc-300">
                  <li className="flex items-center gap-2"><Zap className="w-4 h-4 text-emerald-500"/> High Speed Execution</li>
                  <li className="flex items-center gap-2"><Cpu className="w-4 h-4 text-emerald-500"/> Intelligent Automation</li>
                  <li className="flex items-center gap-2"><Users className="w-4 h-4 text-emerald-500"/> Early Access to Alpha</li>
                  <li className="flex items-center gap-2"><Shield className="w-4 h-4 text-emerald-500"/> Dedicated Infrastructure</li>
                </ul>
                <p className="mt-6 text-sm text-zinc-500 italic">
                  Here, your trades gain time. And time is the most expensive asset in the market.
                </p>
             </div>

             <div className="p-8 border border-zinc-800 rounded-xl bg-gradient-to-br from-black to-zinc-900">
                <h3 className="text-2xl font-bold text-white mb-4">Total Shielding. Absolute Control.</h3>
                <p className="text-zinc-400 mb-6">
                  We use <strong>ZK Proofs</strong> for operational shielding.
                </p>
                <ul className="space-y-3 text-sm text-zinc-300">
                  <li className="flex items-center gap-2"><Shield className="w-4 h-4 text-blue-500"/> Show what you want</li>
                  <li className="flex items-center gap-2"><Users className="w-4 h-4 text-blue-500"/> To whom you want</li>
                  <li className="flex items-center gap-2"><Zap className="w-4 h-4 text-blue-500"/> When you want</li>
                </ul>
                <p className="mt-6 text-sm text-zinc-500 italic">
                  Learn to search outside without getting lost inside. No siren song. No noise.
                </p>
             </div>
          </div>
        </section>

        {/* Brasil Profundo */}
        <section className="py-12 border-y border-zinc-800 text-center">
           <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
             From Silicon Valley to Deep Brazil.
           </h2>
           <div className="max-w-2xl mx-auto space-y-6 text-zinc-400">
             <p className="text-lg">
               This ecosystem is born with a certainty:
             </p>
             <blockquote className="text-2xl font-bold text-white italic">
               &quot;They need Brazil. They just don't know it yet.&quot;
             </blockquote>
             <p>
               And there are people here who understand exactly what we are talking about.
               It wasn't 6 hackathons by chance. It wasn't luck. It was survival inside the game.
             </p>
             <p className="text-emerald-400 font-bold uppercase tracking-widest">
               We got the password. Now the access is structural.
             </p>
           </div>
        </section>

        {/* BMC Grid (Simplified) */}
        <section className="space-y-8">
          <div className="flex items-end justify-between border-b border-zinc-800 pb-4">
            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
              <span className="text-emerald-500">02.</span> ECOSYSTEM OVERVIEW
            </h2>
            <span className="text-xs text-zinc-500">NOT FOR EVERYONE. FOR THOSE WHO KNOW.</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* Value Prop */}
            <div className="p-6 border border-zinc-800 rounded-lg bg-zinc-900/20 hover:border-emerald-500/30 transition-colors">
              <div className="flex items-center gap-3 mb-4 text-emerald-400">
                <Zap className="w-5 h-5" />
                <h3 className="font-bold">Value Proposition</h3>
              </div>
              <ul className="space-y-3 text-sm text-zinc-400">
                <li>• <strong>Financial Agentic Service</strong>: Your guide in the terminal.</li>
                <li>• <strong>Global Vision</strong>: EN / PT / ES / CN.</li>
                <li>• <strong>ZK Shield</strong>: On-chain protection.</li>
                <li>• <strong>Real Opportunities</strong>: Focus on Liquidity and Execution.</li>
              </ul>
            </div>

            {/* Segments */}
            <div className="p-6 border border-zinc-800 rounded-lg bg-zinc-900/20 hover:border-emerald-500/30 transition-colors">
              <div className="flex items-center gap-3 mb-4 text-blue-400">
                <Users className="w-5 h-5" />
                <h3 className="font-bold">Client Segments</h3>
              </div>
              <ul className="space-y-3 text-sm text-zinc-400">
                <li>• Retail Refugees: Tired of losing to emotion.</li>
                <li>• Yield Strategists: Massive liquidity for Epoch 4.</li>
                <li>• &quot;The Black Mindz&quot;: Intellectual Elite.</li>
                <li>• Dev-Traders: Comfortable with Terminal.</li>
              </ul>
            </div>

            {/* Revenue / Tiers */}
            <div className="p-6 border border-zinc-800 rounded-lg bg-zinc-900/20 hover:border-emerald-500/30 transition-colors md:col-span-2">
              <div className="flex items-center gap-3 mb-6 text-yellow-400">
                <Wallet className="w-5 h-5" />
                <h3 className="font-bold">Access Structure (Tiers)</h3>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Tier 1 */}
                <Link href="/marketplace/scout" className="block h-full">
                  <div className="p-4 bg-black rounded border border-zinc-800 flex flex-col relative group hover:border-emerald-500/50 transition-colors h-full cursor-pointer">
                    <div className="text-xs text-emerald-500 mb-2 font-bold tracking-wider">PARTNER SCOUT</div>
                    <div className="text-3xl text-white font-bold mb-1">$29.99</div>
                    <div className="text-[10px] text-zinc-500 uppercase mb-4">The Soldier (Season Pass)</div>
                    
                    <ul className="text-xs text-zinc-400 space-y-2 mt-auto">
                      <li className="flex items-center gap-2">
                        <span className="w-1 h-1 bg-emerald-500 rounded-full"></span>
                        CLI Access & Sentinel
                      </li>
                      <li className="flex items-center gap-2">
                        <span className="w-1 h-1 bg-emerald-500 rounded-full"></span>
                        Phoenix V2 Strategy
                      </li>
                      <li className="flex items-center gap-2">
                        <span className="w-1 h-1 bg-emerald-500 rounded-full"></span>
                        Single Pair Limit
                      </li>
                    </ul>
                  </div>
                </Link>

                {/* Tier 2 */}
                <Link href="/marketplace/commander" className="block h-full">
                  <div className="p-4 bg-zinc-900/40 rounded border border-zinc-700 flex flex-col relative overflow-hidden group hover:border-blue-500/50 transition-colors h-full cursor-pointer">
                    <div className="absolute top-0 right-0 w-20 h-20 bg-blue-500/5 rounded-bl-full"></div>
                    
                    <div className="text-xs text-blue-400 mb-2 font-bold tracking-wider">LIQUIDITY PROVIDER</div>
                    <div className="text-3xl text-white font-bold mb-1">$49.90</div>
                    <div className="text-[10px] text-zinc-500 uppercase mb-4">The Captain (Season Pass)</div>
                    
                    <ul className="text-xs text-zinc-400 space-y-2 relative z-10 mt-auto">
                      <li className="flex items-center gap-2">
                        <span className="w-1 h-1 bg-blue-500 rounded-full"></span>
                        Weaver Grid V2
                      </li>
                      <li className="flex items-center gap-2">
                        <span className="w-1 h-1 bg-blue-500 rounded-full"></span>
                        Delta Neutral Bot
                      </li>
                      <li className="flex items-center gap-2">
                        <span className="w-1 h-1 bg-blue-500 rounded-full"></span>
                        Multi-Pair (3x)
                      </li>
                    </ul>
                  </div>
                </Link>

                {/* Tier 3 */}
                <Link href="/marketplace/architect" className="block h-full">
                  <div className="p-4 bg-gradient-to-b from-zinc-900 to-black rounded border border-yellow-500/20 flex flex-col relative overflow-hidden group hover:border-yellow-500/50 transition-colors h-full cursor-pointer">
                    <div className="absolute top-0 right-0 w-20 h-20 bg-yellow-500/10 rounded-bl-full"></div>
                    
                    <div className="text-xs text-yellow-500 mb-2 font-bold tracking-wider">INSTITUTIONAL PARTNER</div>
                    <div className="text-3xl text-white font-bold mb-1">$99.00</div>
                    <div className="text-[10px] text-zinc-500 uppercase mb-4">The General (Season Pass)</div>
                    
                    <ul className="text-xs text-zinc-400 space-y-2 relative z-10 mt-auto">
                      <li className="flex items-center gap-2">
                        <span className="w-1 h-1 bg-yellow-500 rounded-full"></span>
                        Market Proxy Oracle
                      </li>
                      <li className="flex items-center gap-2">
                        <span className="w-1 h-1 bg-yellow-500 rounded-full"></span>
                        Flash Scalper HFT
                      </li>
                      <li className="flex items-center gap-2">
                        <span className="w-1 h-1 bg-yellow-500 rounded-full"></span>
                        Iron Dome VPS
                      </li>
                    </ul>
                  </div>
                </Link>
              </div>
            </div>

            {/* Key Resources */}
            <div className="p-6 border border-zinc-800 rounded-lg bg-zinc-900/20 hover:border-emerald-500/30 transition-colors">
              <div className="flex items-center gap-3 mb-4 text-purple-400">
                <Code className="w-5 h-5" />
                <h3 className="font-bold">Key Resources</h3>
              </div>
              <ul className="space-y-3 text-sm text-zinc-400">
                <li>• IP (Intellectual Property): Python Scripts.</li>
                <li>• Track Record: Verified volume data.</li>
                <li>• Infra: Smart License Contracts.</li>
              </ul>
            </div>

            {/* Activities */}
            <div className="p-6 border border-zinc-800 rounded-lg bg-zinc-900/20 hover:border-emerald-500/30 transition-colors">
              <div className="flex items-center gap-3 mb-4 text-red-400">
                <Cpu className="w-5 h-5" />
                <h3 className="font-bold">Key Activities</h3>
              </div>
              <ul className="space-y-3 text-sm text-zinc-400">
                <li>• Continuous Engineering: v4.0+ Maintenance.</li>
                <li>• Quant Analysis: Yield Optimization.</li>
                <li>• Community: Elite Formation.</li>
              </ul>
            </div>

          </div>
        </section>

        {/* Protocolo de Integridade */}
        <section className="space-y-8">
          <div className="flex items-end justify-between border-b border-zinc-800 pb-4">
            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
              <span className="text-emerald-500">03.</span> Protocolo de Integridade (The Judge)
            </h2>
            <span className="text-xs text-zinc-500">GOVERNANCE & COMPLIANCE</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-4">
               <h3 className="text-xl font-bold text-white font-mono">1. Lei da Ficha Limpa (SBT)</h3>
               <p className="text-zinc-400 text-sm leading-relaxed">
                 O acesso à Cidadela Digital é restrito. Utilizamos um sistema de <strong>Zero-Knowledge Compliance</strong>. 
                 Sua wallet é verificada contra listas de sanções e risco (Chainalysis/Sumsub). 
                 Aprovados recebem um <strong>Soulbound Token (SBT)</strong> intransferível.
                 <br/><br/>
                 <span className="text-red-400">Wallets High Risk são bloqueadas automaticamente pelo Gatekeeper.</span>
               </p>
            </div>
            
            <div className="space-y-4">
               <h3 className="text-xl font-bold text-white font-mono">2. Lei da Taxa de Sucesso (The Fee)</h3>
               <p className="text-zinc-400 text-sm leading-relaxed">
                 O alinhamento é total. O protocolo aplica taxas automáticas para sustentar o ecossistema:
                 <br/><br/>
                 • <strong>Mercado Secundário</strong>: 3% em todas as revendas de passes (Pre & Post-Launch).
                 <br/>
                 • <strong>Performance Fee</strong>: 3% sobre o Alpha gerado (Airdrops & Volume).
                 <br/><br/>
                 O módulo <code>fee_enforcer.py</code> garante o split matemático: <span className="text-emerald-500">97% Você</span> / <span className="text-emerald-500">3% Tesouraria</span>.
               </p>
            </div>

             <div className="md:col-span-2 p-6 border border-zinc-800 rounded-lg bg-zinc-900/20">
                <h3 className="text-xl font-bold text-white font-mono mb-2">3. O Código Ético (Knowledge for Good)</h3>
                <p className="text-zinc-400 text-sm leading-relaxed">
                  Somos caçadores de oportunidades em um mercado insano, mas temos a <strong>mente construtora</strong>.
                  Este conhecimento é uma arma que deve ser utilizada <strong>pelo bem e para o bem</strong>, nunca em desvantagem do próximo.
                  <br/><br/>
                  Buscamos <strong>oportunidades reais</strong>. Open Interest real. Ordens executadas e posicionadas.
                  Sem ilusão. Sem "Exit Liquidity" nas costas da comunidade.
                </p>
             </div>
          </div>
        </section>

        {/* Signature */}
        <section className="pt-12 border-t border-zinc-800">
          <CreatorCard />
        </section>

      </main>
    </div>
  );
}
