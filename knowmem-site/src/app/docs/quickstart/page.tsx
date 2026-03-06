"use client";

import { motion } from "framer-motion";
import { Zap, Terminal, CheckCircle2, ChevronRight } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

export default function QuickstartPage() {
  const [copied, setCopied] = useState(false);
  const codeSnippet = "pip install knowmem\nknowmem init --workspace my_mesh";

  const handleCopy = () => {
    navigator.clipboard.writeText(codeSnippet);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="max-w-4xl"
    >
      <div className="mb-10">
        <div className="inline-flex items-center rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 text-sm font-medium text-cyan-400 mb-6 shadow-[0_0_15px_rgba(0,174,239,0.2)]">
          <Zap className="mr-2 h-4 w-4" />
          Quickstart
        </div>
        <h1 className="text-4xl font-extrabold tracking-tight lg:text-5xl mb-4 bg-gradient-to-r from-cyan-400 to-blue-600 bg-clip-text text-transparent">
          Get Started in 5 Minutes
        </h1>
        <p className="text-lg text-muted-foreground leading-relaxed">
          Set up your first ResonantMemoryMesh locally and start ingesting documents immediately.
        </p>
      </div>

      <div className="space-y-8 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-white/10 before:to-transparent">
        
        {/* Step 1 */}
        <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group md:flex-row">
          <div className="flex items-center justify-center w-10 h-10 rounded-full border border-white/10 bg-background shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10 transition-colors group-hover:bg-primary/20 group-hover:border-primary/50 text-muted-foreground group-hover:text-primary">
            1
          </div>
          <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] bg-white/5 border border-white/10 p-6 rounded-2xl backdrop-blur group-hover:border-white/20 transition-all ml-4 md:ml-0 md:group-odd:mr-4 md:group-even:ml-4">
            <h3 className="text-xl font-semibold text-foreground mb-2 flex items-center gap-2">
              <Terminal className="h-5 w-5 text-cyan-400" />
              Installation
            </h3>
            <p className="text-muted-foreground text-sm mb-4">
              Install the KnowMem CLI and core engine via pip. We recommend doing this inside a virtual environment.
            </p>
            <div className="relative">
              <pre className="bg-black/50 p-4 rounded-xl text-sm font-mono text-gray-300 overflow-x-auto border border-white/5">
                <code className="block text-cyan-300">pip install knowmem</code>
                <code className="block mt-1">knowmem init --workspace my_mesh</code>
              </pre>
              <button 
                onClick={handleCopy}
                className="absolute top-2 right-2 p-2 bg-white/10 hover:bg-white/20 rounded-md transition-colors"
              >
                {copied ? <CheckCircle2 className="h-4 w-4 text-green-400" /> : <ChevronRight className="h-4 w-4 text-gray-400" />}
              </button>
            </div>
          </div>
        </div>

        {/* Step 2 */}
        <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group md:flex-row">
          <div className="flex items-center justify-center w-10 h-10 rounded-full border border-white/10 bg-background shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10 transition-colors group-hover:bg-primary/20 group-hover:border-primary/50 text-muted-foreground group-hover:text-primary">
            2
          </div>
          <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] bg-white/5 border border-white/10 p-6 rounded-2xl backdrop-blur group-hover:border-white/20 transition-all ml-4 md:ml-0 md:group-odd:mr-4 md:group-even:ml-4">
            <h3 className="text-xl font-semibold text-foreground mb-2">Configure Keys</h3>
            <p className="text-muted-foreground text-sm">
              We need an OpenAI API key for embeddings and structural parsing. Ensure your .env file is set up.
            </p>
            <pre className="mt-4 bg-black/50 p-4 rounded-xl text-sm font-mono overflow-x-auto border border-white/5">
              <code className="text-green-400">OPENAI_API_KEY=sk-...</code>
            </pre>
          </div>
        </div>

        {/* Step 3 */}
        <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group md:flex-row">
          <div className="flex items-center justify-center w-10 h-10 rounded-full border border-white/10 bg-background shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10 transition-colors group-hover:bg-primary/20 group-hover:border-primary/50 text-muted-foreground group-hover:text-primary">
            3
          </div>
          <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] bg-white/5 border border-white/10 p-6 rounded-2xl backdrop-blur group-hover:border-white/20 transition-all ml-4 md:ml-0 md:group-odd:mr-4 md:group-even:ml-4">
            <h3 className="text-xl font-semibold text-foreground mb-2">Ingest Documents</h3>
            <p className="text-muted-foreground text-sm">
              Drop PDFs or markdown files into your `my_mesh/data` folder and run the ingestion pipeline.
            </p>
            <pre className="mt-4 bg-black/50 p-4 rounded-xl text-sm font-mono overflow-x-auto border border-white/5">
              <code className="text-purple-300">knowmem ingest --source ./data</code>
            </pre>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
