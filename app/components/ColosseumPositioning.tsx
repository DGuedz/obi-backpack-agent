import Link from "next/link";

export default function ColosseumPositioning() {
  return (
    <section className="relative z-10 py-16 md:py-24 bg-zinc-950 border-t border-zinc-800">
      {/* Background Grid - Subtle/Technical */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />
      
      <div className="container mx-auto px-4 relative z-20">
        
        {/* Header Block - Left Aligned for more technical feel, or Centered for impact. Sticking to OBI standard centered but clean. */}
        <div className="max-w-4xl mx-auto text-center mb-20">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-emerald-500/20 bg-emerald-500/5 text-emerald-400 text-xs font-mono mb-6">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            COLOSSEUM S4 CANDIDATE
          </div>
          
          <h2 className="text-3xl md:text-5xl font-bold font-mono text-white mb-6 tracking-tight">
            OBI AGENT <span className="text-zinc-500">{"///"}</span> PROVA DE EXECUÇÃO
          </h2>
          
          <p className="text-lg text-zinc-400 font-mono max-w-2xl mx-auto leading-relaxed">
            Agente autônomo que valida, simula e liquida ações on-chain. <br className="hidden md:block"/>
            <span className="text-zinc-200">Operação humana limitada a deploy e monitoramento.</span>
          </p>
        </div>

        {/* Technical Features Strip - Minimalist */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-zinc-800 border border-zinc-800 rounded-lg overflow-hidden mb-20">
          {[
            { title: "AgentWallet", desc: "Assinatura segura isolada" },
            { title: "Heartbeat Sync", desc: "Status endpoints em tempo real" },
            { title: "On-Chain Settle", desc: "Execução atômica na Solana" },
          ].map((item, i) => (
            <div key={i} className="bg-zinc-950 p-6 hover:bg-zinc-900/80 transition-colors group">
              <div className="text-emerald-500 text-xs font-mono mb-2 opacity-50 group-hover:opacity-100 transition-opacity">0{i+1}</div>
              <div className="text-white font-mono font-bold text-sm mb-1">{item.title}</div>
              <div className="text-zinc-500 text-xs font-mono">{item.desc}</div>
            </div>
          ))}
        </div>

        {/* Deep Dive Grid - Institutional Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-20">
          
          {/* Problema */}
          <div className="space-y-4">
            <h3 className="text-lg font-bold font-mono text-white flex items-center gap-2">
              <span className="w-1 h-4 bg-red-500/50 rounded-sm"></span>
              THE PROBLEM
            </h3>
            <div className="p-6 border border-zinc-800 bg-zinc-900/30 rounded-lg h-full hover:border-zinc-700 transition-colors">
              <p className="text-sm font-mono text-zinc-400 mb-6 leading-relaxed">
                Falta de prova verificável de contribuição em liquidez e sinais frágeis de execução real em agentes atuais.
              </p>
              <ul className="space-y-3">
                {[
                  "Emoção humana impactando em perdas",
                  "Baixo Farm em Pepr Dex",
                  "Execução off-chain sem auditabilidade"
                ].map((item, i) => (
                  <li key={i} className="flex items-start gap-3 text-xs font-mono text-zinc-500">
                    <span className="text-red-500/50 mt-0.5">×</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Solução */}
          <div className="space-y-4">
            <h3 className="text-lg font-bold font-mono text-white flex items-center gap-2">
              <span className="w-1 h-4 bg-emerald-500 rounded-sm"></span>
              THE SOLUTION
            </h3>
            <div className="p-6 border border-zinc-800 bg-zinc-900/30 rounded-lg h-full hover:border-emerald-500/20 transition-colors relative overflow-hidden">
              <div className="absolute top-0 right-0 p-2 opacity-10">
                <TargetIcon />
              </div>
              <p className="text-sm font-mono text-zinc-300 mb-6 leading-relaxed">
                Painel com métricas reais, provas e relatórios que validam o fluxo do agente do pré-flight à liquidação.
              </p>
              <ul className="space-y-3">
                {[
                  "Validação pré-execução (State Check)",
                  "AgentWallet (Key Isolation)",
                  "Logs verificáveis on-chain"
                ].map((item, i) => (
                  <li key={i} className="flex items-start gap-3 text-xs font-mono text-zinc-400">
                    <span className="text-emerald-500 mt-0.5">✓</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Impacto */}
          <div className="space-y-4">
            <h3 className="text-lg font-bold font-mono text-white flex items-center gap-2">
              <span className="w-1 h-4 bg-blue-500/50 rounded-sm"></span>
              THE IMPACT
            </h3>
            <div className="p-6 border border-zinc-800 bg-zinc-900/30 rounded-lg h-full hover:border-blue-500/20 transition-colors">
              <p className="text-sm font-mono text-zinc-400 mb-6 leading-relaxed">
                Construção de reputação técnica e transparência absoluta para a Backpack Season 4.
              </p>
              <ul className="space-y-3">
                {[
                  "Confiança na liquidez aportada",
                  "Transparência operacional total",
                  "Auditabilidade simplificada"
                ].map((item, i) => (
                  <li key={i} className="flex items-start gap-3 text-xs font-mono text-zinc-500">
                    <span className="text-blue-500/50 mt-0.5">➜</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* Proof of Volume - Data Strip */}
        <div className="border-y border-zinc-800 bg-zinc-900/20 py-12 mb-20">
          <div className="max-w-5xl mx-auto px-4">
            <div className="flex flex-col md:flex-row items-center justify-between gap-8">
              <div className="text-left">
                <h3 className="text-xl font-bold font-mono text-white mb-2">PROOF OF VOLUME</h3>
                <p className="text-sm font-mono text-zinc-500 max-w-md">
                  Métricas reais extraídas do pipeline de validação. Não é marketing, é evidência on-chain.
                </p>
              </div>
              <div className="flex gap-8 md:gap-12">
                <div className="text-right">
                  <div className="text-xs font-mono text-zinc-500 mb-1">LIQUIDEZ</div>
                  <div className="text-2xl font-mono font-bold text-emerald-400">$1.3M+</div>
                </div>
                <div className="text-right">
                  <div className="text-xs font-mono text-zinc-500 mb-1">SYNC LATENCY</div>
                  <div className="text-2xl font-mono font-bold text-emerald-400">&lt;45ms</div>
                </div>
                <div className="text-right">
                  <div className="text-xs font-mono text-zinc-500 mb-1">UPTIME</div>
                  <div className="text-2xl font-mono font-bold text-emerald-400">99.9%</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Hackathon Criteria - Checklist Mode */}
        <div className="max-w-3xl mx-auto mb-16">
          <div className="text-center mb-8">
            <h3 className="text-sm font-mono text-zinc-500 uppercase tracking-widest">Critérios de Julgamento</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              "Impacto mensurável na Season 4",
              "Inovação em execução autônoma",
              "Complexidade técnica (Logs/Provas)",
              "Clareza Operacional (UX/Docs)"
            ].map((item, i) => (
              <div key={i} className="flex items-center gap-3 p-3 rounded border border-zinc-800/50 bg-zinc-900/20">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500/50" />
                <span className="text-sm font-mono text-zinc-300">{item}</span>
              </div>
            ))}
          </div>
        </div>

        {/* CTA */}
        <div className="flex justify-center">
          <Link
            href="/#proof"
            className="group relative px-8 py-4 bg-zinc-100 hover:bg-white text-black font-bold font-mono text-sm rounded transition-all flex items-center gap-2"
          >
            VER EVIDÊNCIAS
            <ArrowRightIcon className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>
      </div>
    </section>
  );
}

// Icons
function TargetIcon() {
  return (
    <svg className="w-24 h-24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
      <circle cx="12" cy="12" r="10" />
      <circle cx="12" cy="12" r="6" />
      <circle cx="12" cy="12" r="2" />
    </svg>
  );
}

function ArrowRightIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 12h14" />
      <path d="M12 5l7 7-7 7" />
    </svg>
  );
}
