"use client";

import { RMMConfig } from "@/lib/rmm-engine";
import { SlidersHorizontal, Settings2, RotateCcw } from "lucide-react";

interface ControlsProps {
  config: RMMConfig;
  onChange: (newConfig: Partial<RMMConfig>) => void;
  onReset: () => void;
  animating: boolean;
}

export function ControlsPanel({ config, onChange, onReset, animating }: ControlsProps) {
  return (
    <div className="flex flex-col bg-[#111111] border border-border/40 rounded-xl overflow-hidden h-full">
      <div className="flex items-center justify-between p-4 border-b border-border/30 bg-black/40">
        <div className="flex items-center gap-2">
          <Settings2 className="w-4 h-4 text-primary" />
          <h3 className="font-bold text-sm">Physics Engine</h3>
        </div>
        <button
          onClick={onReset}
          className="p-1.5 text-muted-foreground hover:text-white rounded-md hover:bg-white/10 transition-colors"
          title="Reset Graph Energy"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>

      <div className="p-5 space-y-6 flex-1 overflow-y-auto">
        {/* Beta slider */}
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <label className="text-sm font-medium text-foreground">
              Dissipative Gain (β)
            </label>
            <span className="text-xs font-mono text-cyan-400 bg-cyan-400/10 px-2 py-0.5 rounded">
              {config.beta.toFixed(2)}
            </span>
          </div>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Controls how much energy transfers across an edge. Higher means broader resonance.
          </p>
          <input
            type="range"
            min="0.1"
            max="1.5"
            step="0.05"
            value={config.beta}
            onChange={(e) => onChange({ beta: parseFloat(e.target.value) })}
            className="w-full h-1.5 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
          />
        </div>

        {/* Lambda slider */}
        <div className="space-y-3 pt-2">
          <div className="flex justify-between items-center">
            <label className="text-sm font-medium text-foreground">
              Decay Constant (λ)
            </label>
            <span className="text-xs font-mono text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded">
              {config.lambdaDecay.toFixed(2)}
            </span>
          </div>
          <p className="text-xs text-muted-foreground leading-relaxed">
            How fast stored energy dissipates over time.
          </p>
          <input
            type="range"
            min="0"
            max="3"
            step="0.1"
            value={config.lambdaDecay}
            onChange={(e) => onChange({ lambdaDecay: parseFloat(e.target.value) })}
            className="w-full h-1.5 bg-muted rounded-lg appearance-none cursor-pointer accent-emerald-500"
          />
        </div>

        {/* Threshold */}
        <div className="space-y-3 pt-2">
          <div className="flex justify-between items-center">
            <label className="text-sm font-medium text-foreground">
              Pruning Threshold (ε)
            </label>
            <span className="text-xs font-mono text-purple-400 bg-purple-400/10 px-2 py-0.5 rounded">
              {config.threshold.toFixed(4)}
            </span>
          </div>
          <input
            type="range"
            min="0.001"
            max="0.05"
            step="0.001"
            value={config.threshold}
            onChange={(e) => onChange({ threshold: parseFloat(e.target.value) })}
            className="w-full h-1.5 bg-muted rounded-lg appearance-none cursor-pointer accent-purple-500"
          />
        </div>
      </div>
      
      {/* Engine Status */}
      <div className="p-3 bg-black/60 border-t border-border/30 text-xs flex justify-between items-center">
        <span className="text-muted-foreground flex items-center gap-1.5">
          <span className={`w-2 h-2 rounded-full ${animating ? 'bg-primary glow-cyan' : 'bg-muted-foreground'}`}></span>
          Kernel Status
        </span>
        <span className={animating ? "text-primary font-mono" : "text-muted-foreground font-mono"}>
          {animating ? "HOT (Resonating)" : "IDLE"}
        </span>
      </div>
    </div>
  );
}
