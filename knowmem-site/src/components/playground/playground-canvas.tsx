"use client";

import { useEffect, useRef } from "react";
import { RMMGraph } from "@/lib/rmm-engine";

interface CanvasProps {
  graph: RMMGraph;
  onNodeClick: (nodeId: string) => void;
  animating: boolean;
  phase?: "ingest" | "link" | "resonate";
}

const W = 800;
const H = 500;
const NODE_RADIUS = 20;

export function PlaygroundCanvas({ graph, onNodeClick, animating, phase = "resonate" }: CanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  // Keep mouse position without causing re-renders
  const mouseRef = useRef({ x: -999, y: -999 });
  // Track whether layout has settled
  const settledRef = useRef(false);

  // ── 1. Layout simulation: runs once when graph changes ──────────────────
  useEffect(() => {
    settledRef.current = false;
    const nodes = Array.from(graph.nodes.values());

    // Seed positions only if unset
    nodes.forEach((node, i) => {
      if (node.x === undefined || isNaN(node.x)) {
        const angle = (i / nodes.length) * 2 * Math.PI;
        node.x = W / 2 + Math.cos(angle) * 170;
        node.y = H / 2 + Math.sin(angle) * 150;
      }
      node.vx = 0;
      node.vy = 0;
    });

    // Run physics until settled (max 500 iterations)
    for (let iter = 0; iter < 500; iter++) {
      const alpha = Math.max(0, 1 - iter / 300); // cooling schedule

      // Repulsion
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x! - nodes[j].x!;
          const dy = nodes[i].y! - nodes[j].y!;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = (5000 / (dist * dist)) * alpha;
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          nodes[i].vx! += fx;
          nodes[i].vy! += fy;
          nodes[j].vx! -= fx;
          nodes[j].vy! -= fy;
        }
      }

      // Attraction along edges
      for (const edge of graph.edges) {
        const s = graph.nodes.get(edge.source);
        const t = graph.nodes.get(edge.target);
        if (!s || !t) continue;
        const dx = t.x! - s.x!;
        const dy = t.y! - s.y!;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const ideal = 160;
        const force = ((dist - ideal) / dist) * 0.3 * alpha;
        s.vx! += dx * force;
        s.vy! += dy * force;
        t.vx! -= dx * force;
        t.vy! -= dy * force;
      }

      // Center gravity
      nodes.forEach(node => {
        node.vx! += (W / 2 - node.x!) * 0.01 * alpha;
        node.vy! += (H / 2 - node.y!) * 0.01 * alpha;

        // Apply velocity with damping
        node.vx! *= 0.6;
        node.vy! *= 0.6;
        node.x! += node.vx!;
        node.y! += node.vy!;
      });
    }

    // Zero out velocities after settling
    nodes.forEach(n => { n.vx = 0; n.vy = 0; });
    settledRef.current = true;
  }, [graph]);

  // ── 2. Render loop: pure drawing, no physics ─────────────────────────────
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const handleMouseMove = (e: MouseEvent) => {
      const r = canvas.getBoundingClientRect();
      const scaleX = W / r.width;
      const scaleY = H / r.height;
      mouseRef.current = {
        x: (e.clientX - r.left) * scaleX,
        y: (e.clientY - r.top) * scaleY,
      };
    };

    const handleClick = (e: MouseEvent) => {
      const r = canvas.getBoundingClientRect();
      const scaleX = W / r.width;
      const scaleY = H / r.height;
      const cx = (e.clientX - r.left) * scaleX;
      const cy = (e.clientY - r.top) * scaleY;
      for (const node of graph.nodes.values()) {
        const dx = (node.x ?? 0) - cx;
        const dy = (node.y ?? 0) - cy;
        if (Math.sqrt(dx * dx + dy * dy) < NODE_RADIUS + 8) {
          onNodeClick(node.id);
          break;
        }
      }
    };

    canvas.addEventListener("mousemove", handleMouseMove);
    canvas.addEventListener("click", handleClick);

    let raf: number;
    let time = 0;

    const draw = () => {
      ctx.clearRect(0, 0, W, H);
      const nodes = Array.from(graph.nodes.values());
      const mx = mouseRef.current.x;
      const my = mouseRef.current.y;

      // ── Edges ──
      if (phase !== "ingest") {
        for (const edge of graph.edges) {
          const s = graph.nodes.get(edge.source);
          const t = graph.nodes.get(edge.target);
          if (!s || !t) continue;

          const energized = animating && s.energy > 0.01;

        ctx.beginPath();
        ctx.moveTo(s.x!, s.y!);
        ctx.lineTo(t.x!, t.y!);
        ctx.strokeStyle = energized ? `rgba(0,174,239,0.7)` : `rgba(255,255,255,0.12)`;
        ctx.lineWidth = energized ? 1.5 + s.energy * 2 : 1;
        ctx.shadowBlur = energized ? 8 : 0;
        ctx.shadowColor = "#00AEEF";
        ctx.stroke();
        ctx.shadowBlur = 0;

          // Edge Weights text
          if (phase === "link" || phase === "resonate") {
            const mx = (s.x! + t.x!) / 2;
            const my = (s.y! + t.y!) / 2;
            const bgAlpha = energized ? 0.8 : 0.6;
            ctx.fillStyle = `rgba(0,0,0,${bgAlpha})`;
            ctx.beginPath();
            ctx.roundRect(mx - 15, my - 8, 30, 16, 4);
            ctx.fill();
            
            ctx.fillStyle = energized ? "#fff" : "rgba(255,255,255,0.7)";
            ctx.font = "9px monospace";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText(`W:${edge.weight.toFixed(1)}`, mx, my);
          }

          // Traveling pulse dots
          if (energized && phase === "resonate") {
            const pulseT = ((time * 0.015) % 1);
            const px = s.x! + (t.x! - s.x!) * pulseT;
            const py = s.y! + (t.y! - s.y!) * pulseT;
            ctx.beginPath();
            ctx.arc(px, py, 3, 0, Math.PI * 2);
            ctx.fillStyle = "#00AEEF";
            ctx.shadowBlur = 10;
            ctx.shadowColor = "#00AEEF";
            ctx.fill();
            ctx.shadowBlur = 0;
          }
        }
      }

      // ── Nodes ──
      for (const node of nodes) {
        const dx = node.x! - mx;
        const dy = node.y! - my;
        const hovered = Math.sqrt(dx * dx + dy * dy) < NODE_RADIUS + 8;
        const r = hovered ? NODE_RADIUS + 4 : NODE_RADIUS;
        const energized = node.energy > 0;

        // Glow
        if (energized) {
          ctx.shadowBlur = 20 * node.energy;
          ctx.shadowColor = "#00AEEF";
        }

        ctx.beginPath();
        ctx.arc(node.x!, node.y!, r, 0, Math.PI * 2);
        if (energized) {
          const alpha = Math.min(1, 0.3 + node.energy * 0.7);
          ctx.fillStyle = `rgba(0,174,239,${alpha})`;
        } else {
          ctx.fillStyle = hovered ? "rgba(60,60,60,1)" : "rgba(35,35,35,1)";
        }
        ctx.fill();

        ctx.shadowBlur = 0;
        ctx.strokeStyle = energized ? "#00AEEF" : hovered ? "rgba(255,255,255,0.6)" : "rgba(255,255,255,0.25)";
        ctx.lineWidth = energized ? 2 : 1.5;
        ctx.stroke();

        // Label
        ctx.fillStyle = "rgba(255,255,255,0.9)";
        ctx.font = "11px monospace";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(node.label, node.x!, node.y! - r - 12);

        // Energy readout
        if (energized && phase === "resonate") {
          ctx.fillStyle = "#00AEEF";
          ctx.font = "bold 10px monospace";
          ctx.fillText(`E:${node.energy.toFixed(3)}`, node.x!, node.y! + r + 13);
          
          // Math Tooltip (Prev + Transfer)
          if (animating) {
            ctx.fillStyle = "rgba(0,174,239,0.2)";
            ctx.beginPath();
            ctx.roundRect(node.x! + r + 5, node.y! - 10, 120, 20, 4);
            ctx.fill();
            
            ctx.fillStyle = "#00AEEF";
            ctx.font = "9px monospace";
            ctx.textAlign = "left";
            ctx.fillText(`+ Σ(E_n*β*W)`, node.x! + r + 10, node.y!);
          }
        }
      }

      time++;
      raf = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      cancelAnimationFrame(raf);
      canvas.removeEventListener("mousemove", handleMouseMove);
      canvas.removeEventListener("click", handleClick);
    };
  }, [graph, animating, onNodeClick]);

  return (
    <div className="relative w-full bg-[#0d0d0d] rounded-xl border border-border/40 overflow-hidden shadow-2xl" style={{ aspectRatio: `${W}/${H}` }}>
      <div className="absolute top-3 left-3 z-10 text-xs font-mono text-muted-foreground bg-black/60 px-3 py-1.5 rounded border border-border/30 backdrop-blur-md">
        Click a node to inject energy
      </div>
      <canvas
        ref={canvasRef}
        width={W}
        height={H}
        className="w-full h-full cursor-pointer"
      />
    </div>
  );
}
