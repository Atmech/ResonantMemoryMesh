import Link from "next/link";
import { Github, Twitter } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-border/40 py-12 md:py-16">
      <div className="container mx-auto px-4 grid gap-8 md:grid-cols-4">
        
        <div className="col-span-1 md:col-span-2">
          <Link href="/" className="mb-4 inline-block">
             <span className="font-sans font-bold text-xl tracking-tight">Know<span className="font-normal text-muted-foreground">Mem</span></span>
          </Link>
          <p className="max-w-xs text-sm text-muted-foreground leading-relaxed">
            The associative memory engine for AI agents. 
            Powered by topological resonance, built for the next generation of reasoning applications.
          </p>
          <div className="flex gap-4 mt-6">
            <Link href="https://github.com/affantanke/ResonantMemoryMesh" target="_blank" className="text-muted-foreground hover:text-primary transition-colors">
              <Github className="h-5 w-5" />
            </Link>
            <Link href="#" className="text-muted-foreground hover:text-primary transition-colors">
              <Twitter className="h-5 w-5" />
            </Link>
          </div>
        </div>
        
        <div className="space-y-4">
          <h4 className="font-semibold text-sm">Open Source</h4>
          <ul className="space-y-3 text-sm text-muted-foreground">
            <li><Link href="#" className="hover:text-primary transition-colors">Documentation</Link></li>
            <li><Link href="#" className="hover:text-primary transition-colors">Python SDK</Link></li>
            <li><Link href="#" className="hover:text-primary transition-colors">Rust Kernel</Link></li>
            <li><Link href="#" className="hover:text-primary transition-colors">Research Paper</Link></li>
          </ul>
        </div>
        
        <div className="space-y-4">
          <h4 className="font-semibold text-sm">Enterprise</h4>
          <ul className="space-y-3 text-sm text-muted-foreground">
            <li><Link href="#" className="hover:text-primary transition-colors">KnowMem Cloud</Link></li>
            <li><Link href="#" className="hover:text-primary transition-colors">Security</Link></li>
            <li><Link href="#" className="hover:text-primary transition-colors">Support</Link></li>
            <li><Link href="#" className="hover:text-primary transition-colors">Contact</Link></li>
          </ul>
        </div>
        
      </div>
      
      <div className="container mx-auto px-4 mt-12 pt-8 border-t border-border/40 flex flex-col md:flex-row items-center justify-between text-xs text-muted-foreground">
        <p>&copy; {new Date().getFullYear()} Resonant Memory Mesh. Open Core under MIT License.</p>
        <div className="flex gap-4 mt-4 md:mt-0">
          <Link href="#" className="hover:text-foreground transition-colors">Privacy</Link>
          <Link href="#" className="hover:text-foreground transition-colors">Terms</Link>
        </div>
      </div>
    </footer>
  );
}
