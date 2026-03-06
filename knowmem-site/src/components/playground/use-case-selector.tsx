"use client";

import { cn } from "@/lib/utils";
import { Network, Stethoscope, Bug, Plus, Gem } from "lucide-react";

interface SelectorProps {
  selected: string;
  onSelect: (id: string) => void;
}

export function UseCaseSelector({ selected, onSelect }: SelectorProps) {
  const cases = [
    { id: "causal_chain", label: "Causal Chain (Paper)", icon: Network },
    { id: "diamond_heist", label: "The Diamond Heist", icon: Gem },
    { id: "medical_diagnosis", label: "Medical Diagnosis", icon: Stethoscope },
    { id: "bug_analysis", label: "Root Cause Analysis", icon: Bug },
  ];

  return (
    <div className="flex gap-2 overflow-x-auto pb-4 hide-scrollbar">
      {cases.map((c) => {
        const Icon = c.icon;
        const isActive = selected === c.id;
        return (
          <button
            key={c.id}
            onClick={() => onSelect(c.id)}
            className={cn(
              "flex items-center gap-2 px-4 py-2.5 rounded-lg border transition-all text-sm font-medium whitespace-nowrap",
              isActive 
                ? "bg-primary/10 border-primary text-primary shadow-[0_0_15px_rgba(0,174,239,0.2)]" 
                : "bg-card border-border/40 text-muted-foreground hover:bg-muted/50 hover:text-foreground"
            )}
          >
            <Icon className="w-4 h-4" />
            {c.label}
          </button>
        );
      })}
      
      <button 
        className="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-dashed border-border/60 bg-transparent text-muted-foreground hover:bg-muted/30 transition-colors text-sm font-medium whitespace-nowrap opacity-50 cursor-not-allowed"
        title="Custom graphing coming soon"
      >
        <Plus className="w-4 h-4" />
        Custom Graph
      </button>
    </div>
  );
}
