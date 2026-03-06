"use client";

import { RMMNode } from "@/lib/rmm-engine";
import { Zap, AlertTriangle } from "lucide-react";

interface ResultsProps {
  results: RMMNode[];
  compareRag: boolean;
  onToggleRag: (val: boolean) => void;
}

export function ResultsPanel({ results, compareRag, onToggleRag }: ResultsProps) {
  // If no results, show empty state
  if (results.length === 0) {
    return (
      <div className="flex flex-col bg-[#111111] border border-border/40 rounded-xl overflow-hidden h-full">
        <div className="p-4 border-b border-border/30 bg-black/40">
          <h3 className="font-bold text-sm flex items-center gap-2">
            <Zap className="w-4 h-4 text-yellow-500" />
            Active Resonance
          </h3>
        </div>
        <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-muted-foreground">
          <div className="w-12 h-12 rounded-full bg-muted/20 flex items-center justify-center mb-4">
            <Zap className="w-6 h-6 opacity-40" />
          </div>
          <p className="text-sm">Click a node on the canvas to inject energy and observe retrieval.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col bg-[#111111] border border-border/40 rounded-xl overflow-hidden h-full">
      <div className="p-4 border-b border-border/30 bg-black/40 flex justify-between items-center">
        <h3 className="font-bold text-sm flex items-center gap-2">
          <Zap className="w-4 h-4 text-yellow-500" />
          Top Retrieved Nodes
        </h3>
        
        {/* RAG Toggle */}
        <div className="flex items-center gap-2">
          <label className="text-xs text-muted-foreground cursor-pointer select-none">
            Compare vRAG
          </label>
          <button 
            onClick={() => onToggleRag(!compareRag)}
            className={`w-8 h-4 rounded-full transition-colors relative ${compareRag ? 'bg-primary' : 'bg-muted'}`}
          >
            <div className={`absolute top-0.5 w-3 h-3 rounded-full bg-white transition-transform ${compareRag ? 'left-4.5' : 'left-0.5'}`}></div>
          </button>
        </div>
      </div>

      <div className="p-4 space-y-4 flex-1 overflow-y-auto">
        {results.map((node, i) => {
          // In "Compare RAG" mode, nodes beyond 1 hop (low cosine sim) would be missed
          // We simulate this by checking if it's the target in the causal chain (N5), distant medical (M5, M7),
          // bug root causes (B6), or the Diamond Heist suspect (D4, D5)
          const isMissedByRag = compareRag && (
            node.id === "N5" || 
            node.id === "M7" || 
            node.id === "M5" || 
            node.id === "B6" ||
            node.id === "D5" || // Victor Vance (indirect suspect)
            node.id === "D4"    // Front Company (indirect link)
          );
          return (
            <div key={node.id} className="relative">
              <div className={`flex justify-between text-xs mb-1.5 ${isMissedByRag ? 'text-red-400' : 'text-foreground'}`}>
                <span className="font-medium truncate pr-4">
                  {i + 1}. {node.label}
                  {isMissedByRag && <span className="ml-2 text-[10px] uppercase font-bold text-red-500/80 bg-red-500/10 px-1.5 rounded">Rag Miss</span>}
                </span>
                <span className="font-mono">{node.energy.toFixed(3)}</span>
              </div>
              
              <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                <div 
                  className={`h-full transition-all duration-300 ${isMissedByRag ? 'bg-red-500/50' : 'bg-cyan-500 shadow-[0_0_10px_#00AEEF]'}`} 
                  style={{ width: `${Math.min(100, node.energy * 100)}%` }}
                />
              </div>
            </div>
          );
        })}

        {compareRag && (
          <div className="mt-6 p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex gap-3 text-xs text-red-200">
            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
            <p>
              Standard Vector RAG assumes relevance equals cosine similarity. The deep causal targets shown above are <strong>orthogonal</strong> to the query and would be completely missed by a vector database.
            </p>
          </div>
        )}
      </div>
      
      <div className="p-3 bg-black/60 border-t border-border/30 flex justify-between items-center">
        <div className="text-xs text-muted-foreground font-mono">
          <span className="text-primary text-sm font-bold mr-1">0.36</span>ms
        </div>
        <div className="text-[10px] text-muted-foreground uppercase tracking-wider">
          Simulated Query Time
        </div>
      </div>
    </div>
  );
}
