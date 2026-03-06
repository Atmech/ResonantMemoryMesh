"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Terminal, Lightbulb, BookOpen, Layers, Zap, ArrowRight, Settings, Command } from "lucide-react";

export const DOCS_NAV = [
  {
    title: "Getting Started",
    items: [
      { title: "Introduction", href: "/docs", icon: BookOpen },
      { title: "Installation", href: "/docs/installation", icon: Terminal },
      { title: "Quickstart", href: "/docs/quickstart", icon: Zap },
    ],
  },
  {
    title: "Core Concepts",
    items: [
      { title: "Architecture", href: "/docs/architecture", icon: Layers },
      { title: "Models & Tasks", href: "/docs/models", icon: Lightbulb },
      { title: "CLI Reference", href: "/docs/cli", icon: Command },
    ],
  },
  {
    title: "Advanced",
    items: [
      { title: "Cloud Integration", href: "/docs/cloud", icon: Settings },
    ]
  }
];

export function DocsSidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed top-16 left-0 z-30 hidden w-72 shrink-0 border-r border-border/40 bg-background/50 backdrop-blur-xl md:block h-[calc(100vh-4rem)] overflow-y-auto">
      <div className="flex h-full flex-col px-6 py-8">
        <div className="flex flex-col gap-8">
          {DOCS_NAV.map((section, index) => (
            <div key={index} className="flex flex-col gap-2">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground/70 mb-1">
                {section.title}
              </h4>
              {section.items.map((item, itemIndex) => {
                const isActive = pathname === item.href;
                const Icon = item.icon;
                return (
                  <Link
                    key={itemIndex}
                    href={item.href}
                    className={cn(
                      "group flex items-center justify-between rounded-lg px-3 py-2 text-sm font-medium ring-offset-background transition-all hover:bg-white/5 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 border border-transparent",
                      isActive
                        ? "bg-primary/10 text-primary border-primary/20 shadow-[0_0_15px_rgba(0,174,239,0.15)] hover:bg-primary/20"
                        : "text-muted-foreground"
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <Icon className={cn("size-4", isActive ? "text-primary shadow-sm" : "text-muted-foreground group-hover:text-foreground transition-colors duration-200")} />
                      <span>{item.title}</span>
                    </div>
                    {isActive && (
                      <ArrowRight className="size-3 text-primary animate-pulse" />
                    )}
                  </Link>
                );
              })}
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}
