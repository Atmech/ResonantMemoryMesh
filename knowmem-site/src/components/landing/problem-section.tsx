import { Search, BrainCircuit, XCircle, CheckCircle2 } from "lucide-react";

export function ProblemSection() {
  return (
    <section id="features" className="py-24 bg-[#111111]">
      <div className="container mx-auto px-4">
        
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl md:text-5xl font-sans font-bold mb-6">
            The <span className="text-destructive">Flashcard Fallacy</span>
          </h2>
          <p className="text-lg text-muted-foreground">
            Standard RAG assumes relevance equals cosine similarity. 
            But in complex reasoning tasks, the correct context often resides in nodes that are semantically orthogonal to the query, but topologically vital.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
          {/* RAG Card */}
          <div className="rounded-2xl border border-destructive/20 bg-background/50 p-8 shadow-lg relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-destructive"></div>
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-xl bg-destructive/10 text-destructive">
                <Search className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-semibold">Standard Vector RAG</h3>
            </div>
            
            <p className="text-sm text-muted-foreground mb-8 min-h-[60px]">
              Extracts isolated memory fragments closest to the query string. Fails on multi-hop logical deductions.
            </p>
            
            <div className="space-y-4">
              <div className="flex items-center text-sm">
                <XCircle className="w-4 h-4 text-destructive mr-3 flex-shrink-0" />
                <span className="text-muted-foreground">Hits a wall at 2-hop logical steps</span>
              </div>
              <div className="flex items-center text-sm">
                <XCircle className="w-4 h-4 text-destructive mr-3 flex-shrink-0" />
                <span className="text-muted-foreground">Requires massive context stuffing, increasing cost and latency</span>
              </div>
              <div className="flex items-center text-sm">
                <XCircle className="w-4 h-4 text-destructive mr-3 flex-shrink-0" />
                <span className="text-muted-foreground">Truncates causal chains if intermediate steps lack semantic overlap</span>
              </div>
            </div>
          </div>

          {/* KnowMem Card */}
          <div className="rounded-2xl border border-primary/20 bg-primary/5 p-8 shadow-xl shadow-primary/5 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary to-cyan-400 glow-cyan"></div>
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-xl bg-primary/10 text-primary">
                <BrainCircuit className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-semibold">Resonant Memory Mesh</h3>
            </div>
            
            <p className="text-sm text-muted-foreground mb-8 min-h-[60px]">
              Retrieval modeled as standard physical energy propagation. The entry node excites, and energy flows topologically through the graph.
            </p>
            
            <div className="space-y-4">
              <div className="flex items-center text-sm">
                <CheckCircle2 className="w-4 h-4 text-primary mr-3 flex-shrink-0" />
                <span className="text-foreground">Crosses semantic gaps to retrieve 5-hop causal targets</span>
              </div>
              <div className="flex items-center text-sm">
                <CheckCircle2 className="w-4 h-4 text-primary mr-3 flex-shrink-0" />
                <span className="text-foreground">Maintains bounded LLM context windows (cheap & fast)</span>
              </div>
              <div className="flex items-center text-sm">
                <CheckCircle2 className="w-4 h-4 text-primary mr-3 flex-shrink-0" />
                <span className="text-foreground">Protects critical bridge nodes via proprietary V-LRU scaling</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
