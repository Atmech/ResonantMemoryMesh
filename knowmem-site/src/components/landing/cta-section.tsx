"use client";

import Link from "next/link";
import { ArrowRight, Terminal, Atom } from "lucide-react";

export function CTASection() {
  return (
    <section className="py-24 border-t border-border/30 relative overflow-hidden">
      
      {/* Background glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-3xl h-full max-h-96 bg-primary/10 blur-[100px] pointer-events-none rounded-full" />

      <div className="container mx-auto px-4 relative z-10 text-center">
        <h2 className="text-3xl md:text-5xl font-sans font-bold mb-6">
          Ready to build memory that reasons?
        </h2>
        <p className="text-muted-foreground text-lg max-w-2xl mx-auto mb-8">
          Get started with the open-source KnowMem engine today, or try the interactive Playground to see resonance in action.
        </p>

        <div className="flex justify-center mb-12">
           <Link href="/playground" className="inline-flex h-12 items-center justify-center rounded-full bg-primary/10 border border-primary/50 px-8 text-sm font-bold text-primary shadow-lg shadow-primary/20 hover:bg-primary/20 hover:scale-105 transition-all gap-2">
             <Atom className="w-4 h-4" /> Try the Playground
           </Link>
        </div>

        <div className="flex flex-col sm:flex-row gap-6 justify-center max-w-lg mx-auto">
          
          <div className="flex-1 bg-card border border-border/40 rounded-xl p-6 text-left shadow-lg">
            <h3 className="font-bold text-lg mb-2 flex items-center gap-2">
              <Terminal className="w-4 h-4 text-primary" /> Open Source
            </h3>
            <p className="text-sm text-muted-foreground mb-4">Install the Python SDK and spin up your first mesh locally.</p>
            <div className="bg-[#111111] border border-border/50 rounded-md p-3 font-mono text-sm text-center mb-4 text-green-400">
              pip install knowmem
            </div>
            <Link href="#docs" className="text-sm text-primary hover:text-cyan-300 font-medium inline-flex items-center gap-1 transition-colors">
              Read the documentation <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          <div className="flex-1 bg-primary/10 border border-primary/30 rounded-xl p-6 text-left shadow-xl shadow-primary/5 relative overflow-hidden group hover:border-primary/60 transition-colors">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary to-cyan-400 glow-cyan" />
            <h3 className="font-bold text-lg mb-2 text-primary">KnowMem Cloud</h3>
            <p className="text-sm text-foreground/80 mb-6">Scale instantly with managed infrastructure and proprietary topological auto-tuning.</p>
            <form className="flex gap-2" onSubmit={(e) => e.preventDefault()}>
              <input 
                type="email" 
                placeholder="developer@company.com" 
                className="flex-1 bg-background/80 border border-border/50 rounded-md px-3 py-2 text-sm focus:outline-none focus:border-primary/50 text-foreground transition-colors"
                required
              />
              <button type="submit" className="bg-primary hover:bg-primary/90 text-primary-foreground px-4 py-2 rounded-md text-sm font-medium transition-colors shadow shadow-primary/20">
                Join Waitlist
              </button>
            </form>
          </div>

        </div>
      </div>
    </section>
  );
}
