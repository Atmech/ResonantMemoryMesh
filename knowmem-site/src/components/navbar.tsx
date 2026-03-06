import Link from "next/link";
import Image from "next/image";
import { Github, Menu } from "lucide-react";

export function Navbar() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <Image src="/logo.png" alt="KnowMem Logo" width={32} height={32} className="opacity-90" />
          <span className="font-sans font-bold text-xl tracking-tight">Know<span className="font-normal text-muted-foreground">Mem</span></span>
        </Link>
        
        <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-muted-foreground">
          <Link href="/#features" className="hover:text-primary transition-colors">Features</Link>
          <Link href="/#benchmarks" className="hover:text-primary transition-colors">Benchmarks</Link>
          <Link href="/playground" className="hover:text-primary transition-colors text-primary border-b border-primary pb-0.5">Playground</Link>
          <Link href="/docs" className="hover:text-primary transition-colors">Documentation</Link>
          <Link href="/#cloud" className="hover:text-primary transition-colors">Cloud</Link>
        </nav>
        
        <div className="flex items-center gap-4">
          <Link href="https://github.com/affantanke/ResonantMemoryMesh" target="_blank" rel="noreferrer" className="text-muted-foreground hover:text-foreground transition-colors">
            <span className="sr-only">GitHub</span>
            <Github className="h-5 w-5" />
          </Link>
          <Link href="/#getting-started" className="hidden md:inline-flex h-9 items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90">
            Get Started
          </Link>
          <button className="md:hidden text-foreground">
            <Menu className="h-6 w-6" />
          </button>
        </div>
      </div>
    </header>
  );
}
