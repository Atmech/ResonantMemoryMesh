import { Database, Network, Zap } from "lucide-react";

export function HowItWorksSection() {
  const steps = [
    {
      title: "1. Ingest",
      icon: Database,
      description: "Text is chunked and embedded via standard models (OpenAI, Voyage, Nomic). These become nodes in the mesh.",
      code: 'mesh.ingest(vector, metadata={"label": "Fact A"})'
    },
    {
      title: "2. Connect",
      icon: Network,
      description: "Agents assert relationships between facts. The mesh forms explicit structural edges allowing energy to flow.",
      code: 'mesh.connect(node_A_id, node_B_id, weight=0.9)'
    },
    {
      title: "3. Query (Resonate)",
      icon: Zap,
      description: "An atomic ping injects energy at an entry point. The Rust FFI Kernel computes topological decay instantly.",
      code: 'mesh.query(query_vector, top_n=5)'
    }
  ];

  return (
    <section className="py-24 border-t border-border/30 relative">
      <div className="container mx-auto px-4">
        
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-sans font-bold mb-4">How it works</h2>
          <p className="text-muted-foreground text-lg">Three steps to give your agent a reasoning moat.</p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <div key={index} className="flex flex-col rounded-2xl border border-border/40 bg-card p-6 md:p-8 hover:border-primary/50 transition-colors duration-500">
                <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-6 text-primary border border-primary/20">
                  <Icon className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-bold mb-3">{step.title}</h3>
                <p className="text-muted-foreground text-sm mb-6 flex-grow">{step.description}</p>
                
                <div className="bg-[#111111] p-3 rounded-lg border border-border/50 font-mono text-xs overflow-x-auto text-emerald-400">
                  <code>{step.code}</code>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
