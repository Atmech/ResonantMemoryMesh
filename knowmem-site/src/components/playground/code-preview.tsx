"use client";

import { RMMConfig } from "@/lib/rmm-engine";
import { Terminal } from "lucide-react";

interface CodePreviewProps {
  config: RMMConfig;
  selectedCase: string;
}

export function CodePreview({ config, selectedCase }: CodePreviewProps) {
  return (
    <div className="flex flex-col bg-[#0A0A0A] border border-border/40 rounded-xl overflow-hidden shadow-2xl">
      <div className="flex items-center px-4 py-3 border-b border-border/30 bg-[#111111]">
        <div className="flex gap-2">
           <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
           <div className="w-3 h-3 rounded-full bg-yellow-500/80"></div>
           <div className="w-3 h-3 rounded-full bg-green-500/80"></div>
        </div>
        <div className="mx-auto flex items-center gap-2 text-xs text-muted-foreground font-mono">
          <Terminal className="w-3.5 h-3.5" />
          mesh.py
        </div>
      </div>
      
      <div className="p-5 overflow-x-auto text-sm font-mono leading-relaxed h-[200px] overflow-y-auto custom-scrollbar">
        <pre className="text-gray-300">
          <span className="text-pink-400">from</span> knowmem <span className="text-pink-400">import</span> Mesh, MeshConfig{'\n'}
          <span className="text-pink-400">from</span> knowmem.adapters <span className="text-pink-400">import</span> InMemoryStorage{'\n'}
          {'\n'}
          <span className="text-slate-500"># 1. Initialize Engine (Hot Kernel: ~0.36ms)</span>{'\n'}
          mesh = Mesh(InMemoryStorage(), MeshConfig({'\n'}
          {'    '}<span className="text-orange-300">beta</span>=<span className="text-blue-300">{config.beta.toFixed(2)}</span>,{'\n'}
          {'    '}<span className="text-orange-300">lambda_decay</span>=<span className="text-blue-300">{config.lambdaDecay.toFixed(2)}</span>,{'\n'}
          {'    '}<span className="text-orange-300">threshold</span>=<span className="text-blue-300">{config.threshold.toFixed(4)}</span>{'\n'}
          )){'\n'}
          {'\n'}
          <span className="text-slate-500"># 2. Ingest Fact Sequence (Zero-Copy)</span>{'\n'}
          {selectedCase === "causal_chain" && (
            <>
              mesh.ingest(vec_a, metadata=<span className="text-green-300">&#123;"fact": "Query Context A"&#125;</span>){'\n'}
              mesh.ingest(vec_b, metadata=<span className="text-green-300">&#123;"fact": "Bridging Fact B"&#125;</span>){'\n'}
              <span className="text-slate-500"># ...</span>{'\n'}
              mesh.connect(<span className="text-green-300">"Node_A"</span>, <span className="text-green-300">"Node_B"</span>, weight=<span className="text-blue-300">0.9</span>){'\n'}
            </>
          )}
          {selectedCase === "diamond_heist" && (
            <>
              mesh.ingest(vec_diamond, metadata=<span className="text-green-300">&#123;"fact": "A rare blue diamond was stolen..."&#125;</span>){'\n'}
              mesh.ingest(vec_vance, metadata=<span className="text-green-300">&#123;"suspect": "Victor 'The Ghost' Vance..."&#125;</span>){'\n'}
              <span className="text-slate-500"># AutoLinker silently builds vector proximity edges</span>{'\n'}
              mesh.connect(<span className="text-green-300">"Diamond"</span>, <span className="text-green-300">"BlackVan"</span>, weight=<span className="text-blue-300">0.8</span>){'\n'}
            </>
          )}
          {selectedCase !== "causal_chain" && selectedCase !== "diamond_heist" && (
            <>
              mesh.ingest(vec_1, metadata=<span className="text-green-300">&#123;"concept": "Domain Graph"&#125;</span>){'\n'}
              mesh.connect(<span className="text-green-300">"Node_1"</span>, <span className="text-green-300">"Node_2"</span>, weight=<span className="text-blue-300">0.9</span>){'\n'}
            </>
          )}
          {'\n'}
          <span className="text-slate-500"># 3. Resonate (Atomic Ping)</span>{'\n'}
          result = mesh.<span className="text-blue-400">query</span>(query_vector, <span className="text-orange-300">top_n</span>=<span className="text-blue-300">5</span>){'\n'}
          {'\n'}
          <span className="text-pink-400">for</span> n <span className="text-pink-400">in</span> result.nodes:{'\n'}
          {'    '}<span className="text-cyan-300">print</span>(<span className="text-green-300">f"&#123;</span>n.id<span className="text-green-300">&#125; | Energy: &#123;</span>n.energy<span className="text-green-300">:</span><span className="text-blue-300">.3f</span><span className="text-green-300">&#125;"</span>){'\n'}
        </pre>
      </div>
    </div>
  );
}
