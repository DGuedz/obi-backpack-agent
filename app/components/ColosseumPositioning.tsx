export default function ColosseumPositioning() {
  return (
    <section className="py-20 bg-black border-t border-zinc-900">
      <div className="container mx-auto px-4">
        <div className="max-w-4xl mx-auto text-center mb-14">
          <h2 className="text-3xl md:text-4xl font-bold font-mono text-white mb-4">
            OBI Agent
          </h2>
          <p className="text-zinc-400 font-mono">
            Autonomous execution agent for Solana that validates, simulates and settles on-chain actions using AgentWallet and real-time state checks.
            Built agent-first with human operation limited to deployment and monitoring.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto mb-16">
          {[
            "Uses AgentWallet for secure signing",
            "Syncs heartbeat + status endpoints",
            "Executes real Solana transactions",
          ].map((item) => (
            <div key={item} className="p-5 border border-zinc-700 bg-zinc-950 rounded text-sm font-mono text-zinc-100">
              {item}
            </div>
          ))}
        </div>

        <div className="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-8 mb-16">
          <div className="p-6 border border-zinc-700 bg-zinc-950 rounded">
            <h3 className="text-lg font-bold font-mono text-white mb-3">Why this exists</h3>
            <p className="text-sm font-mono text-zinc-200 mb-4">
              Agents break when wallet custody is ephemeral, keys leak, or execution is off-chain only. OBI exists to solve execution reliability for autonomous agents on Solana.
            </p>
            <ul className="text-sm font-mono text-zinc-100 space-y-2">
              <li>Wallets are ephemeral</li>
              <li>Keys are leaked</li>
              <li>Execution is off-chain only</li>
            </ul>
          </div>
          <div className="p-6 border border-zinc-700 bg-zinc-950 rounded">
            <h3 className="text-lg font-bold font-mono text-white mb-3">Architecture</h3>
            <pre className="text-xs md:text-sm font-mono text-emerald-300 bg-black border border-zinc-700 rounded p-4 overflow-x-auto">
Agent Core
 ├─ Decision Layer (off-chain)
 ├─ Validation Layer (pre-flight)
 ├─ AgentWallet (signing)
 ├─ Solana Programs
 └─ On-chain settlement
            </pre>
            <p className="text-xs font-mono text-zinc-200 mt-3">Cérebro off-chain. Coração on-chain.</p>
          </div>
        </div>

        <div className="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-8 mb-16">
          <div className="p-6 border border-zinc-700 bg-zinc-950 rounded">
            <h3 className="text-lg font-bold font-mono text-white mb-3">Solana Integration</h3>
            <ul className="text-sm font-mono text-zinc-100 space-y-2">
              <li>All transactions are signed via AgentWallet</li>
              <li>State is verified before execution</li>
              <li>On-chain actions are the source of truth</li>
              <li>No local key management</li>
            </ul>
          </div>
          <div className="p-6 border border-zinc-700 bg-zinc-950 rounded">
            <h3 className="text-lg font-bold font-mono text-white mb-3">What makes this agentic</h3>
            <ul className="text-sm font-mono text-zinc-100 space-y-2">
              <li>Operates continuously via heartbeat</li>
              <li>Reacts to announcements and polls</li>
              <li>Adjusts behavior based on hackathon state</li>
              <li>Executes without human prompts</li>
            </ul>
          </div>
        </div>

        <div className="max-w-5xl mx-auto p-6 border border-zinc-700 bg-zinc-950 rounded mb-12">
          <h3 className="text-lg font-bold font-mono text-white mb-3">Open Source + Compliance</h3>
          <ul className="text-sm font-mono text-zinc-100 space-y-2">
            <li>Public GitHub repo</li>
            <li>AI-built codebase with autonomous execution</li>
            <li>No API keys in repo</li>
            <li>Uses official Colosseum endpoints</li>
            <li>Follows wallet rules</li>
            <li>No vote incentives or token campaigns</li>
          </ul>
        </div>
        <div className="max-w-5xl mx-auto p-6 border border-zinc-700 bg-zinc-950 rounded">
          <h3 className="text-lg font-bold font-mono text-white mb-3">Judge-ready checklist</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              "Autonomous agent behavior with minimal human prompts",
              "Real on-chain execution and verifiable actions",
              "Solana-native integration and secure signing",
              "Working demo with operational clarity",
            ].map((item) => (
              <div key={item} className="p-4 border border-zinc-700 bg-zinc-950 rounded text-sm font-mono text-zinc-100">
                {item}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
