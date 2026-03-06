"use client";

import { motion } from "framer-motion";
import { ArrowRight, BookOpen, Layers, Zap, Terminal, Lightbulb } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

const fadeIn = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
};

const stagger = {
  visible: { transition: { staggerChildren: 0.1 } }
};

const CARDS = [
  {
    title: "Quickstart Guide",
    description: "Get up and running with ResonantMemoryMesh in under 5 minutes.",
    icon: Zap,
    href: "/docs/quickstart",
    color: "from-cyan-500/20 to-blue-500/0",
    border: "group-hover:border-cyan-500/50"
  },
  {
    title: "Architecture",
    description: "Deep dive into the hierarchical memory mesh and how it connects contexts.",
    icon: Layers,
    href: "/docs/architecture",
    color: "from-purple-500/20 to-pink-500/0",
    border: "group-hover:border-purple-500/50"
  },
  {
    title: "CLI Reference",
    description: "Learn how to use the KnowMem CLI for dataset extraction and benchmarking.",
    icon: Terminal,
    href: "/docs/cli",
    color: "from-green-500/20 to-emerald-500/0",
    border: "group-hover:border-green-500/50"
  },
];

export default function DocsIntroduction() {
  return (
    <motion.div 
      initial="hidden"
      animate="visible"
      variants={stagger}
      className="max-w-3xl"
    >
      <motion.div variants={fadeIn} className="mb-10">
        <div className="inline-flex items-center rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-sm font-medium text-primary mb-6 shadow-[0_0_15px_rgba(0,174,239,0.2)]">
          <BookOpen className="mr-2 h-4 w-4" />
          Documentation
        </div>
        <h1 className="text-4xl font-extrabold tracking-tight lg:text-5xl mb-4 bg-gradient-to-r from-white via-white to-white/60 bg-clip-text text-transparent">
          Introduction to KnowMem
        </h1>
        <p className="text-lg text-muted-foreground leading-relaxed">
          Welcome to the official documentation for ResonantMemoryMesh. Learn how to build highly intelligent, connected memory systems for your AI applications.
        </p>
      </motion.div>

      <motion.div variants={fadeIn} className="grid sm:grid-cols-2 gap-4 mb-12">
        {CARDS.map((card, idx) => {
          const Icon = card.icon;
          return (
            <Link key={idx} href={card.href} className="group relative rounded-2xl border border-white/10 bg-white/5 p-6 transition-all hover:bg-white/10 hover:shadow-2xl overflow-hidden overflow-hidden">
              <div className={cn("absolute inset-0 bg-gradient-to-br opacity-0 transition-opacity group-hover:opacity-100", card.color)} />
              <div className="relative z-10 flex flex-col items-start gap-4">
                <div className="rounded-lg bg-background p-3 shadow-inner ring-1 ring-white/10 group-hover:ring-primary/50 transition-all">
                  <Icon className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold text-foreground flex items-center gap-2">
                    {card.title}
                    <ArrowRight className="h-4 w-4 opacity-0 -translate-x-2 transition-all group-hover:opacity-100 group-hover:translate-x-0 text-primary" />
                  </h3>
                  <p className="mt-2 text-sm text-muted-foreground line-clamp-2">
                    {card.description}
                  </p>
                </div>
              </div>
            </Link>
          );
        })}
      </motion.div>

      <motion.div variants={fadeIn} className="prose prose-invert max-w-none">
        <h2 className="text-2xl font-semibold mt-10 mb-4 border-b border-border/50 pb-2">What is ResonantMemoryMesh?</h2>
        <p className="text-muted-foreground mb-4">
          ResonantMemoryMesh (KnowMem) is a revolutionary architecture bypassing traditional RAG limitations. Imagine giving your AI not just a search engine, but a perfectly mapped, hierarchical brain.
        </p>
        <p className="text-muted-foreground mb-4">
          Unlike flat vector databases that struggle with long-context synthesis, KnowMem creates a dynamic mesh of interconnected concepts, allowing intelligent traversal and deep, multi-hop reasoning.
        </p>

        <div className="my-8 rounded-xl border border-white/10 bg-card/50 p-6 backdrop-blur shadow-lg">
          <h3 className="text-lg font-medium text-white mb-3 flex items-center gap-2">
            <Lightbulb className="h-5 w-5 text-yellow-500" />
            Key Benefits
          </h3>
          <ul className="space-y-2 text-muted-foreground">
            <li className="flex items-start gap-2">
              <span className="text-primary mt-1">•</span>
              <strong>Hierarchical Understanding:</strong> Extracts knowledge across local, structural, and global semantic concepts.
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary mt-1">•</span>
              <strong>Multi-hop Retrieval:</strong> Connects disparate dots of information effortlessly.
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary mt-1">•</span>
              <strong>Reduced Hallucination:</strong> Grounded context generation maintains exact provenance.
            </li>
          </ul>
        </div>
      </motion.div>
    </motion.div>
  );
}
