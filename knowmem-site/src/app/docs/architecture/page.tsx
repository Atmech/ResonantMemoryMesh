"use client";

import { motion } from "framer-motion";
import { Layers, Network, Database, Cpu, ArrowRight } from "lucide-react";

export default function ArchitecturePage() {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="max-w-4xl"
    >
      <div className="mb-10">
        <div className="inline-flex items-center rounded-full border border-purple-500/30 bg-purple-500/10 px-3 py-1 text-sm font-medium text-purple-400 mb-6 shadow-[0_0_15px_rgba(168,85,247,0.2)]">
          <Layers className="mr-2 h-4 w-4" />
          Core Concepts
        </div>
        <h1 className="text-4xl font-extrabold tracking-tight lg:text-5xl mb-4 bg-gradient-to-r from-purple-400 to-pink-600 bg-clip-text text-transparent">
          Architecture Deep Dive
        </h1>
        <p className="text-lg text-muted-foreground leading-relaxed">
          ResonantMemoryMesh is built to bridge the gap between flat vector databases and true artificial reasoning. Here is how the system is structured.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
          <Network className="h-8 w-8 text-primary mb-4" />
          <h3 className="text-xl font-semibold text-foreground mb-2">Hierarchical Graph</h3>
          <p className="text-muted-foreground text-sm">
            Documents are not just chunked; they are parsed into a multi-layered graph where local entities, structural sections, and global themes are seamlessly interconnected.
          </p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
          <Database className="h-8 w-8 text-purple-400 mb-4" />
          <h3 className="text-xl font-semibold text-foreground mb-2">Dual Storage Engine</h3>
          <p className="text-muted-foreground text-sm">
            We utilize a hybrid approach: a high-performance vector index for semantic search, tightly coupled with a graph database for relational traversal.
          </p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur md:col-span-2 relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 via-purple-500/10 to-pink-500/10 opacity-50 group-hover:opacity-100 transition-opacity" />
          <div className="relative z-10 flex flex-col md:flex-row items-center gap-6">
            <div className="p-4 bg-background/80 rounded-full border border-white/10 shrink-0">
              <Cpu className="h-10 w-10 text-pink-400" />
            </div>
            <div>
              <h3 className="text-xl font-semibold text-foreground mb-2">Resonant Synthesis</h3>
              <p className="text-muted-foreground text-sm leading-relaxed mb-4">
                At query time, the system doesn't just retrieve the top-K chunks. It triggers a "resonance" across the memory mesh, illuminating connected pathways and synthesizing a coherent answer grounded in the source material.
              </p>
              <button className="text-sm font-medium text-pink-400 flex items-center gap-2 group/btn">
                Read the Paper
                <ArrowRight className="h-4 w-4 group-hover/btn:translate-x-1 transition-transform" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="prose prose-invert max-w-none">
        <h2 className="text-2xl font-semibold mt-10 mb-4 border-b border-border/50 pb-2">The Ingestion Pipeline</h2>
        <div className="bg-black/50 border border-white/10 rounded-xl p-6 font-mono text-sm text-cyan-300 shadow-inner overflow-x-auto">
          {`1. Parsing    -> Structure extraction (PDF, MD, Docx)
2. Chunking   -> Semantic boundary detection
3. Entity Ext -> NER & Relationship mapping via LLM
4. Embedding  -> Dense vector encoding
5. Indexing   -> Bi-directional graph + Vector Store
`}
        </div>
      </div>
    </motion.div>
  );
}
