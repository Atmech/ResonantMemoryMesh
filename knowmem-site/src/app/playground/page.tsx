"use client";

import { useEffect, useState, useRef } from "react";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { PlaygroundCanvas } from "@/components/playground/playground-canvas";
import { UseCaseSelector } from "@/components/playground/use-case-selector";
import { ControlsPanel } from "@/components/playground/controls-panel";
import { ResultsPanel } from "@/components/playground/results-panel";
import { CodePreview } from "@/components/playground/code-preview";
import { RMMGraph, DEFAULT_CONFIG, RMMConfig } from "@/lib/rmm-engine";
import { Atom, FileSearch, Play, Layers, Link as LinkIcon, Zap, ArrowRight, RotateCcw } from "lucide-react";

type Phase = "ingest" | "link" | "resonate";

export default function PlaygroundPage() {
  const [selectedCase, setSelectedCase] = useState("causal_chain");
  const [config, setConfig] = useState<RMMConfig>(DEFAULT_CONFIG);
  const [graph, setGraph] = useState<RMMGraph | null>(null);
  const [animating, setAnimating] = useState(false);
  const [compareRag, setCompareRag] = useState(false);
  const [phase, setPhase] = useState<Phase>("resonate");
  const [tutorialStep, setTutorialStep] = useState(0);
  
  // Animation ref
  const lastTimeRef = useRef<number>(0);
  const frameRef = useRef<number>(0);

  // Initialize graph when use case changes
  useEffect(() => {
    const newGraph = RMMGraph.getPreset(selectedCase as any);
    newGraph.config = config;
    setGraph(newGraph);
    setAnimating(false);
    // Reset tutorial state
    setTutorialStep(0);
    // Auto-set the story mode back to ingest for a fresh start for all cases
    setPhase("ingest");
  }, [selectedCase]);

  // Update config in live graph
  const handleConfigChange = (newConfig: Partial<RMMConfig>) => {
    const nextConfig = { ...config, ...newConfig };
    setConfig(nextConfig);
    if (graph) {
      graph.config = nextConfig;
    }
  };

  const handleReset = () => {
    if (graph) {
      graph.resetEnergy();
      setAnimating(false);
      // Force re-render
      setGraph(Object.assign(new RMMGraph(), graph));
    }
  };

  const handleNodeClick = (nodeId: string) => {
    if (!graph) return;
    
    // Auto switch to resonate phase to show the animation
    setPhase("resonate");
    
    // Ignite the mesh
    graph.ignite(nodeId, 1.0);
    setAnimating(true);
    lastTimeRef.current = performance.now();
    
    // Force render to start animation
    setGraph(Object.assign(new RMMGraph(), graph));
  };

  // The Physics Loop
  useEffect(() => {
    if (!animating || !graph) return;

    const loop = (time: number) => {
      // We simulate slow time so it's visible. 
      // Rust kernel runs this in 0.36ms real time.
      const dt = 0.05; // fixed slow step
      
      const { activeNodes } = graph.step(dt);
      
      // Update UI with new state
      setGraph(Object.assign(new RMMGraph(), graph));

      // Stop animating if all nodes decay below threshold
      if (activeNodes.length === 0) {
        setAnimating(false);
      } else {
        frameRef.current = requestAnimationFrame(loop);
      }
    };

    frameRef.current = requestAnimationFrame(loop);

    return () => cancelAnimationFrame(frameRef.current);
  }, [animating, graph]);

  if (!graph) return null;

  return (
    <div className="flex min-h-screen flex-col bg-background selection:bg-primary/30 selection:text-primary-foreground text-foreground font-sans">
      <Navbar />
      
      <main className="flex-1 py-8">
        <div className="container mx-auto px-4 max-w-7xl">
          
          <div className="mb-8">
            <h1 className="text-3xl md:text-4xl font-bold font-sans flex items-center gap-3 mb-2">
              <Atom className="w-8 h-8 text-primary" />
              Resonance Playground
            </h1>
            <p className="text-muted-foreground">
              Experience topological resonance interactively. The engine below is a pure TypeScript port of the exact physical equations governing the RMM Rust Kernel.
            </p>
          </div>

          <div className="mb-6">
            <UseCaseSelector selected={selectedCase} onSelect={setSelectedCase} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            
            {/* Left Column: Canvas & Code */}
            <div className="lg:col-span-8 flex flex-col gap-6">
              
              {/* Visual Explainer Phase Toggle */}
              <div className="flex bg-[#111111] p-1.5 rounded-xl border border-border/40 w-full sm:w-fit mx-auto lg:mx-0 shadow-lg">
                <button
                  onClick={() => setPhase("ingest")}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${phase === 'ingest' ? 'bg-primary/20 text-primary shadow-sm' : 'text-muted-foreground hover:text-foreground hover:bg-white/5'}`}
                >
                  <Layers className="w-4 h-4" />
                  1. Ingestion
                </button>
                <div className="w-px bg-border/40 mx-1 my-2"></div>
                <button
                  onClick={() => setPhase("link")}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${phase === 'link' ? 'bg-primary/20 text-primary shadow-sm' : 'text-muted-foreground hover:text-foreground hover:bg-white/5'}`}
                >
                  <LinkIcon className="w-4 h-4" />
                  2. AutoLinking
                </button>
                <div className="w-px bg-border/40 mx-1 my-2"></div>
                <button
                  onClick={() => setPhase("resonate")}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${phase === 'resonate' ? 'bg-primary/20 text-primary shadow-sm' : 'text-muted-foreground hover:text-foreground hover:bg-white/5'}`}
                >
                  <Zap className="w-4 h-4" />
                  3. Resonance
                </button>
              </div>

              <PlaygroundCanvas 
                graph={graph} 
                onNodeClick={handleNodeClick} 
                animating={animating}
                phase={phase}
              />
              <CodePreview 
                config={config} 
                selectedCase={selectedCase} 
              />
            </div>

            {/* Right Column: Controls & Results */}
            <div className="lg:col-span-4 flex flex-col gap-6 h-[500px] lg:h-auto">
              <div className="flex-1 min-h-[300px]">
                <ResultsPanel 
                  results={graph.getResults()} 
                  compareRag={compareRag} 
                  onToggleRag={setCompareRag} 
                />
              </div>
              <div className="h-[350px]">
                <ControlsPanel 
                  config={config} 
                  onChange={handleConfigChange} 
                  onReset={handleReset}
                  animating={animating}
                />
              </div>
            </div>

          </div>

          {/* Interactive Guided Story Section for All Cases */}
          {(() => {
            const stories: Record<string, {
              queryNode: string;
              queryLabel: string;
              steps: { icon: any; title: string; text: React.ReactNode; buttonText: string }[];
            }> = {
              diamond_heist: {
                queryNode: "D1",
                queryLabel: "Museum Theft",
                steps: [
                  {
                    icon: Layers,
                    title: "Step 1: The Setup",
                    text: <>Welcome to the <strong>Diamond Heist</strong>. First, KnowMem reads in raw police files, witness reports, and random Chicago trivia. Look at the canvas above—right now, it's just a pile of disconnected data points. No connections have been made yet.</>,
                    buttonText: "Connect the Evidence"
                  },
                  {
                    icon: LinkIcon,
                    title: "Step 2: The Connections",
                    text: <>In the background, the <strong>AutoLinker</strong> analyzes the semantic meaning of every fact and draws invisible threads between related concepts. Notice how the <em>Stolen Diamond</em> is now linked to the <em>Black Van</em>, even though no human explicitly connected them. It also linked a bunch of noise.</>,
                    buttonText: "Why Vector Search Fails"
                  },
                  {
                    icon: FileSearch,
                    title: "Step 3: The AI Blindspot",
                    text: <>A standard Vector Database (like ChatGPT uses) looks for matching words. If we ask <em>"Who stole the museum diamond?"</em>, it finds the Museum, the Diamond, and maybe another robbery. <strong>But it completely misses the real suspect, Victor Vance</strong>, because his specific file doesn't mention the museum.</>,
                    buttonText: "Try Topological Resonance"
                  },
                  {
                    icon: Zap,
                    title: "Step 4: Topological Resonance",
                    text: <>Watch how Resonance solves this. Energy flows structurally from the <em>Query</em>, to the <em>Van</em>, to the <em>Front Company</em>, and finally illuminates <strong>Victor Vance</strong>. The noise is ignored because it doesn't form a coherent resonant path.</>,
                    buttonText: ""
                  }
                ]
              },
              causal_chain: {
                queryNode: "N1",
                queryLabel: "Context A",
                steps: [
                  {
                    icon: Layers,
                    title: "Step 1: The Setup",
                    text: <>Welcome to the <strong>Six Degrees of Project X</strong>. This benchmark models a 5-hop causal chain (A→B→C→D→E). Right now, they're just raw unlinked facts in a database.</>,
                    buttonText: "Calculate Proximity"
                  },
                  {
                    icon: LinkIcon,
                    title: "Step 2: The Connections",
                    text: <>The <strong>AutoLinker</strong> calculates vector similarities and draws edges between locally related facts (e.g., A to B, B to C).</>,
                    buttonText: "Why Vector Search Fails"
                  },
                  {
                    icon: FileSearch,
                    title: "Step 3: The AI Blindspot",
                    text: <>If you query A, a standard vector search might return B, or a semantic distractor. It fundamentally cannot find E, because the cosine similarity between A and E is a mere 0.28—a complete miss.</>,
                    buttonText: "Try Topological Resonance"
                  },
                  {
                    icon: Zap,
                    title: "Step 4: Topological Resonance",
                    text: <>Topological Resonance passes energy through the physical structure of the memory mesh. Watch how querying <em>A</em> effortlessly illuminates <strong>E</strong> at the end of the chain.</>,
                    buttonText: ""
                  }
                ]
              },
              medical_diagnosis: {
                queryNode: "M1",
                queryLabel: "Symptoms",
                steps: [
                  {
                    icon: Layers,
                    title: "Step 1: The Setup",
                    text: <>In <strong>Medical Diagnosis</strong>, we ingest a patient's symptoms, medical literature on conditions and treatments, and their personal health records. No connections exist yet.</>,
                    buttonText: "Map Medical Concepts"
                  },
                  {
                    icon: LinkIcon,
                    title: "Step 2: The Connections",
                    text: <>The <strong>AutoLinker</strong> connects symptoms to conditions, and conditions to typical treatments based on overlapping medical terminology.</>,
                    buttonText: "Why Vector Search Fails"
                  },
                  {
                    icon: FileSearch,
                    title: "Step 3: The AI Blindspot",
                    text: <>A standard RAG system asked to treat 'Headaches' will retrieve 'Migraine' and its treatment 'Triptans'. But it misses the patient's existing <strong>Hypertension</strong> and ignores the severe <strong>Contraindication Alert</strong>.</>,
                    buttonText: "Try Topological Resonance"
                  },
                  {
                    icon: Zap,
                    title: "Step 4: Topological Resonance",
                    text: <>Topological Resonance traverses side-effects automatically. Querying the symptoms illuminates the entire treatment path, lighting up the dangerous Contraindication before a mistake is made.</>,
                    buttonText: ""
                  }
                ]
              },
              bug_analysis: {
                queryNode: "B1",
                queryLabel: "Null Pointer Error",
                steps: [
                  {
                    icon: Layers,
                    title: "Step 1: The Setup",
                    text: <>In <strong>Root Cause Analysis</strong>, we ingest application error logs, Git commits, PR descriptions, Jira tickets, and Design Docs.</>,
                    buttonText: "Link Code Artefacts"
                  },
                  {
                    icon: LinkIcon,
                    title: "Step 2: The Connections",
                    text: <>The <strong>AutoLinker</strong> connects the 'NullPointerException' log to a specific code file, to the commit that changed it, to the PR, and so on.</>,
                    buttonText: "Why Vector Search Fails"
                  },
                  {
                    icon: FileSearch,
                    title: "Step 3: The AI Blindspot",
                    text: <>A developer searching a standard RAG system for 'NullPointerException' will only find the immediate log trace. It has zero chance of returning the original <strong>Cache Invalidation Design Doc</strong> that caused the architectural flaw.</>,
                    buttonText: "Try Topological Resonance"
                  },
                  {
                    icon: Zap,
                    title: "Step 4: Topological Resonance",
                    text: <>Watch Topological Resonance trace the structure backward from the Error Log directly into the Architect's original Design Doc over 5 discrete hops.</>,
                    buttonText: ""
                  }
                ]
              }
            };

            const currentStory = stories[selectedCase];
            if (!currentStory) return null;
            
            const stepContent = currentStory.steps[tutorialStep];
            const StepIcon = stepContent.icon;

            return (
              <div key={selectedCase} className="mt-8 bg-[#111111] border border-border/40 rounded-xl p-8 shadow-2xl relative overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-500 max-w-4xl mx-auto">
                {/* Background glow decoration */}
                <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-[80px] pointer-events-none"></div>
                
                <div className="flex flex-col md:flex-row gap-8 items-center">
                  
                  {/* Text Content */}
                  <div className="flex-1 space-y-4">
                    <div className="animate-in fade-in slide-in-from-right-4 duration-300" key={tutorialStep}>
                      <h3 className={`text-xl font-bold flex items-center gap-2 mb-3 ${tutorialStep === 2 ? 'text-red-400' : 'text-primary'}`}>
                        <StepIcon className="w-6 h-6" />
                        {stepContent.title}
                      </h3>
                      <p className="text-muted-foreground leading-relaxed text-sm md:text-base">
                        {stepContent.text}
                      </p>
                    </div>

                    {/* Progress Dots */}
                    <div className="flex gap-2 pt-4">
                      {[0, 1, 2, 3].map((step) => (
                        <div 
                          key={step} 
                          className={`h-1.5 rounded-full transition-all duration-300 ${tutorialStep === step ? 'w-8 bg-primary' : 'w-2 bg-border'}`}
                        />
                      ))}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="w-full md:w-auto shrink-0 flex flex-col gap-3">
                    {tutorialStep < 3 && (
                      <button 
                        onClick={() => { 
                          if (tutorialStep === 0) setPhase("link");
                          if (tutorialStep === 1) {
                            // nothing changes phase, just text changes
                          }
                          if (tutorialStep === 2) {
                            setCompareRag(true);
                          }
                          setTutorialStep(tutorialStep + 1); 
                        }}
                        className="w-full flex items-center justify-center gap-2 bg-white/10 hover:bg-white/15 text-white font-semibold py-3 px-6 rounded-lg transition-all active:scale-[0.98]"
                      >
                        {stepContent.buttonText} <ArrowRight className="w-4 h-4" />
                      </button>
                    )}
                    
                    {tutorialStep === 3 && (
                      <div className="flex flex-col gap-2">
                         <button 
                          onClick={() => handleNodeClick(currentStory.queryNode)}
                          disabled={animating}
                          className="w-full flex items-center justify-center gap-2 bg-primary hover:bg-primary/90 text-primary-foreground font-bold py-3 px-6 rounded-lg transition-all active:scale-[0.98] disabled:opacity-50 shadow-[0_0_20px_rgba(0,174,239,0.3)] hover:shadow-[0_0_30px_rgba(0,174,239,0.5)]"
                        >
                          {animating ? (
                            <span className="flex items-center gap-2">
                              <div className="w-4 h-4 rounded-full border-2 border-primary-foreground border-t-transparent animate-spin"></div>
                              Resonating...
                            </span>
                          ) : (
                            <>
                              <Play className="w-4 h-4 fill-current" />
                              Run Query: {currentStory.queryLabel}
                            </>
                          )}
                        </button>
                        <button 
                          onClick={() => {
                            setTutorialStep(0);
                            setPhase("ingest");
                            setCompareRag(false);
                            handleReset();
                          }}
                          disabled={animating}
                          className="w-full flex items-center justify-center gap-2 text-muted-foreground hover:text-white font-medium py-2 px-4 rounded-lg transition-all disabled:opacity-50"
                        >
                           <RotateCcw className="w-4 h-4" /> Start Over
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })()}

        </div>
      </main>

      <Footer />
    </div>
  );
}
