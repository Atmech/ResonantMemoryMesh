import { Cpu, Terminal, Shield, Lock, Database } from "lucide-react";

export function ArchitectureSection() {
  return (
    <section className="py-24 bg-[#111111] overflow-hidden">
      <div className="container mx-auto px-4">
        
        <div className="text-center mb-16 max-w-3xl mx-auto">
          <h2 className="text-3xl md:text-5xl font-sans font-bold mb-6">
            The Open-Core Architecture
          </h2>
          <p className="text-muted-foreground text-lg">
            A Bimodal Kernel design separating inference from storage. Build on the open-source engine, scale with KnowMem Cloud.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-12 max-w-5xl mx-auto items-center">
          
          {/* Open Source Block */}
          <div className="space-y-6">
            <div className="flex items-center gap-4 border-b border-border/40 pb-4">
              <div className="p-3 bg-white/10 rounded-lg text-white">
                <Terminal className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-xl font-bold">KnowMem Open Source</h3>
                <p className="text-sm text-green-400 font-mono mt-1">Free & Self-Hosted</p>
              </div>
            </div>
            
            <ul className="space-y-4">
              <li className="flex gap-4">
                <div className="mt-1 w-2 h-2 rounded-full bg-white opacity-50 flex-shrink-0" />
                <div>
                  <strong className="text-foreground block">Python SDK (rmm-core)</strong>
                  <p className="text-sm text-muted-foreground">The developer interface for managing nodes, edges, and triggering queries.</p>
                </div>
              </li>
              <li className="flex gap-4">
                <div className="mt-1 w-2 h-2 rounded-full bg-white opacity-50 flex-shrink-0" />
                <div>
                  <strong className="text-foreground block">Rust Bimodal Kernel</strong>
                  <p className="text-sm text-muted-foreground">Zero-copy FFI bridge running a lock-free BFS algorithm via Rayon & DashMap.</p>
                </div>
              </li>
              <li className="flex gap-4">
                <div className="mt-1 w-2 h-2 rounded-full bg-white opacity-50 flex-shrink-0" />
                <div>
                  <strong className="text-foreground block">Static Physics Engine</strong>
                  <p className="text-sm text-muted-foreground">Fixed decay and gain propagation (suitable for standard predictable AI workflows).</p>
                </div>
              </li>
            </ul>
          </div>

          {/* Cloud Block */}
          <div className="space-y-6 rounded-2xl border border-primary/30 bg-primary/5 p-8 relative">
             <div className="absolute top-0 right-0 p-4">
                <span className="text-xs font-bold px-3 py-1 bg-primary/20 text-primary rounded-full uppercase tracking-wider">
                  Enterprise
                </span>
             </div>
             
            <div className="flex items-center gap-4 border-b border-primary/20 pb-4">
              <div className="p-3 bg-primary/20 rounded-lg text-primary glow-cyan">
                <Cpu className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-primary text-shadow-glow">KnowMem Cloud</h3>
                <p className="text-sm text-muted-foreground mt-1">Managed Auto-Tuning Platform</p>
              </div>
            </div>
            
            <ul className="space-y-4">
              <li className="flex gap-4">
                <Lock className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                <div>
                  <strong className="text-foreground block">Dynamic Auto-Tune Physics</strong>
                  <p className="text-sm text-muted-foreground">Proprietary logic dynamically adjusts gain (β) and decay (λ) based on local mesh topology, preventing energy explosions in 100M+ node graphs.</p>
                </div>
              </li>
              <li className="flex gap-4">
                <Shield className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                <div>
                  <strong className="text-foreground block">Predictive V-LRU Scaling</strong>
                  <p className="text-sm text-muted-foreground">Advanced predictive eviction models protecting critical bridge nodes in distributed environments.</p>
                </div>
              </li>
              <li className="flex gap-4">
                <Database className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                <div>
                  <strong className="text-foreground block">Managed Postgres + pgvector</strong>
                  <p className="text-sm text-muted-foreground">Zero-ops distributed storage layer handling sharding and hybrid search indexing.</p>
                </div>
              </li>
            </ul>
          </div>
          
        </div>
      </div>
    </section>
  );
}
