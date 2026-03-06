import { Check, X } from "lucide-react";

export function BenchmarkSection() {
  return (
    <section id="benchmarks" className="py-24 bg-background">
      <div className="container mx-auto px-4">
        
        <div className="text-center mb-16 max-w-3xl mx-auto">
          <h2 className="text-3xl md:text-5xl font-sans font-bold mb-6">
            Sub-millisecond latency. <br className="hidden md:block"/>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-cyan-300">Infinite context depth.</span>
          </h2>
          <p className="text-muted-foreground text-lg">
            RMM eliminates the LLM extraction bottleneck natively using the Rust-FFI Bimodal Kernel. 
            Results from the Causal Chain Test ("Six Degrees of Project X", 5-hop causal retrieval).
          </p>
        </div>

        <div className="max-w-5xl mx-auto overflow-hidden rounded-2xl border border-border/40 bg-card shadow-xl shadow-primary/5">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-[#111111] border-b border-border/40">
                <tr>
                  <th className="px-6 py-5 font-semibold text-foreground">Architecture</th>
                  <th className="px-6 py-5 font-semibold text-foreground">Paradigm</th>
                  <th className="px-6 py-5 font-semibold text-foreground">p50 Latency</th>
                  <th className="px-6 py-5 font-semibold text-foreground">5-Hop Success</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/20">
                <tr className="hover:bg-muted/30 transition-colors">
                  <td className="px-6 py-4 text-muted-foreground">Standard Vector RAG</td>
                  <td className="px-6 py-4 text-muted-foreground">Semantic Similarity</td>
                  <td className="px-6 py-4 text-muted-foreground line-through">0.120 s</td>
                  <td className="px-6 py-4"><X className="w-5 h-5 text-destructive" /></td>
                </tr>
                <tr className="hover:bg-muted/30 transition-colors">
                  <td className="px-6 py-4 text-muted-foreground">Mem0 (Graph)</td>
                  <td className="px-6 py-4 text-muted-foreground">LLM Relational</td>
                  <td className="px-6 py-4 text-muted-foreground">1.091 s</td>
                  <td className="px-6 py-4"><Check className="w-5 h-5 text-emerald-500" /></td>
                </tr>
                <tr className="hover:bg-muted/30 transition-colors">
                  <td className="px-6 py-4 text-muted-foreground">Full-Context Baseline</td>
                  <td className="px-6 py-4 text-muted-foreground">Context Stuffing</td>
                  <td className="px-6 py-4 text-muted-foreground">9.870 s</td>
                  <td className="px-6 py-4"><Check className="w-5 h-5 text-emerald-500" /></td>
                </tr>
                {/* RMM Winning Row */}
                <tr className="bg-primary/5 border-l-4 border-l-primary relative">
                  <td className="px-6 py-5 font-semibold text-primary">KnowMem (Hot Kernel)</td>
                  <td className="px-6 py-5 text-foreground font-medium">Topological Resonance</td>
                  <td className="px-6 py-5 font-bold text-primary text-xl">&lt; 0.001 s</td>
                  <td className="px-6 py-5"><Check className="w-6 h-6 text-primary glow-cyan rounded-full bg-primary/20" /></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </section>
  );
}
