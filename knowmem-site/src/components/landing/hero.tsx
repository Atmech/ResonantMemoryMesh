import { MeshAnimation } from "./mesh-animation";
import Link from "next/link";
import { ArrowRight, Terminal } from "lucide-react";

export function HeroSection() {
  return (
    <section className="relative min-h-[90vh] flex flex-col items-center justify-center pt-24 pb-16 overflow-hidden">
      {/* Background Mesh Animation */}
      <MeshAnimation />
      
      <div className="container relative z-10 px-4 mx-auto text-center flex flex-col items-center">
        
        {/* Release Badge */}
        <div className="inline-flex items-center rounded-full border border-border/40 bg-card/40 backdrop-blur-md px-3 py-1 text-sm font-medium mb-8">
          <span className="flex h-2 w-2 rounded-full bg-primary mr-2 glow-cyan"></span>
          <span className="text-muted-foreground">KnowMem v0.1.0 Open Source Core is live</span>
        </div>
        
        {/* Main Headline */}
        <h1 className="text-4xl md:text-6xl lg:text-7xl font-sans font-bold tracking-tight text-white mb-6">
          Memory that <span className="text-transparent bg-clip-text bg-gradient-to-r from-white to-primary">reasons</span>.
        </h1>
        
        {/* Subhead */}
        <p className="max-w-2xl text-lg md:text-xl text-muted-foreground mb-10 leading-relaxed mx-auto">
          Break the Flashcard Fallacy of standard RAG. KnowMem is the first associative memory engine 
          that retrieves 5-hop causal chains using topological resonance physics.
        </p>
        
        {/* CTAs */}
        <div className="flex flex-col sm:flex-row gap-4 mb-16 justify-center w-full sm:w-auto">
          <Link href="#getting-started" className="inline-flex h-12 items-center justify-center rounded-md bg-primary px-8 text-sm font-medium text-primary-foreground shadow-lg shadow-primary/20 hover:bg-primary/90 transition-all glow-cyan gap-2">
            Read the Docs
          </Link>
          <Link href="https://github.com/affantanke/ResonantMemoryMesh" target="_blank" className="inline-flex h-12 items-center justify-center rounded-md border border-border/50 bg-card/50 backdrop-blur px-8 text-sm font-medium text-white hover:bg-card/80 transition-all gap-2">
            <Terminal className="w-4 h-4" />
            pip install knowmem
          </Link>
        </div>
        
        {/* Code Snippet Box */}
        <div className="w-full max-w-3xl border border-border/40 rounded-xl bg-[#1A1A1A]/80 backdrop-blur-xl shadow-2xl shadow-primary/10 overflow-hidden text-left">
          <div className="flex items-center px-4 py-3 border-b border-border/40 bg-black/40">
            <div className="flex gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
              <div className="w-3 h-3 rounded-full bg-yellow-500/80"></div>
              <div className="w-3 h-3 rounded-full bg-green-500/80"></div>
            </div>
            <div className="mx-auto text-xs text-muted-foreground font-mono">mesh.py</div>
          </div>
          <div className="p-6 overflow-x-auto text-sm md:text-base font-mono leading-relaxed">
            <pre className="text-gray-300">
              <span className="text-pink-400">from</span> knowmem <span className="text-pink-400">import</span> Mesh, MeshConfig{'\n'}
              <span className="text-pink-400">from</span> knowmem.adapters <span className="text-pink-400">import</span> InMemoryStorage{'\n'}
              {'\n'}
              <span className="text-slate-500"># 1. Initialize Resonance Engine (Hot Kernel: ~0.3ms)</span>{'\n'}
              mesh = Mesh(InMemoryStorage(), MeshConfig(<span className="text-orange-300">beta</span>=<span className="text-blue-300">0.7</span>, <span className="text-orange-300">lambda_decay</span>=<span className="text-blue-300">0.1</span>)){'\n'}
              {'\n'}
              <span className="text-slate-500"># 2. Query structural relationships impossible in vector databases</span>{'\n'}
              result = mesh.<span className="text-blue-400">query</span>(query_vector, <span className="text-orange-300">top_n</span>=<span className="text-blue-300">5</span>){'\n'}
              {'\n'}
              <span className="text-pink-400">for</span> node <span className="text-pink-400">in</span> result.nodes:{'\n'}
              {'    '}<span className="text-cyan-300">print</span>(<span className="text-green-300">f"Energy: </span>&#123;node.energy<span className="text-green-300">:</span><span className="text-blue-300">.4f</span>&#125;<span className="text-green-300"> | Rationale: </span>&#123;result.rationale&#125;<span className="text-green-300">"</span>){'\n'}
            </pre>
          </div>
        </div>
        
        {/* Stats bar */}
        <div className="mt-16 pt-8 border-t border-border/30 w-full max-w-4xl grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="flex flex-col items-center">
            <span className="text-3xl font-bold text-white mb-2">0.36<span className="text-primary text-xl">ms</span></span>
            <span className="text-sm text-muted-foreground">Hot Query Latency</span>
          </div>
          <div className="flex flex-col items-center">
            <span className="text-3xl font-bold text-white mb-2">503<span className="text-primary text-xl">x</span></span>
            <span className="text-sm text-muted-foreground">Faster than LLM Graph Traversal</span>
          </div>
          <div className="flex flex-col items-center">
            <span className="text-3xl font-bold text-white mb-2">5<span className="text-primary text-xl">-hop</span></span>
            <span className="text-sm text-muted-foreground">Causal Chain Retrieval</span>
          </div>
        </div>
      </div>
    </section>
  );
}
