// "use client"
'use client';

import { useEffect, useRef } from 'react';

/**
 * Animated mesh background that visualizes the "topological resonance" concept.
 * Nodes connect and occasional "energy" pulses travel along edges.
 */
export function MeshAnimation() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    
    // Canvas dimensions
    let width = 0;
    let height = 0;

    const resize = () => {
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = width;
      canvas.height = height;
    };
    
    window.addEventListener('resize', resize);
    resize();

    // Node configuration
    const NODE_COUNT = Math.floor((width * height) / 20000); // Responsive density
    const CONNECTION_DISTANCE = 180;
    
    class Node {
      x: number;
      y: number;
      vx: number;
      vy: number;
      radius: number;
      
      constructor() {
        this.x = Math.random() * width;
        this.y = Math.random() * height;
        this.vx = (Math.random() - 0.5) * 0.5; // Slow drift
        this.vy = (Math.random() - 0.5) * 0.5;
        this.radius = Math.random() * 2 + 1.5;
      }
      
      update() {
        this.x += this.vx;
        this.y += this.vy;
        
        // Wrap around edges softly
        if (this.x < -50) this.x = width + 50;
        if (this.x > width + 50) this.x = -50;
        if (this.y < -50) this.y = height + 50;
        if (this.y > height + 50) this.y = -50;
      }
      
      draw(ctx: CanvasRenderingContext2D) {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        // White nodes to match brand kit logo
        ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
        ctx.fill();
      }
    }
    
    const nodes = Array.from({ length: NODE_COUNT }, () => new Node());
    
    // Time for pulsing
    let time = 0;

    const render = () => {
      ctx.clearRect(0, 0, width, height);
      time += 0.05;
      
      // Update nodes
      nodes.forEach(node => node.update());
      
      // Draw connections
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x;
          const dy = nodes[i].y - nodes[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          
          if (dist < CONNECTION_DISTANCE) {
            ctx.beginPath();
            ctx.moveTo(nodes[i].x, nodes[i].y);
            ctx.lineTo(nodes[j].x, nodes[j].y);
            
            // Opacity based on distance
            const alpha = 1 - (dist / CONNECTION_DISTANCE);
            
            // Random "Energy Pulse" simulation along some edges
            const isPulse = (i * j + time) % 100 < 5;
            
            if (isPulse) {
              // Brand Cyan glow for pulsing energy
              ctx.strokeStyle = `rgba(0, 174, 239, ${alpha})`;
              ctx.lineWidth = 1.5;
            } else {
              // Standard faint edge (white tint)
              ctx.strokeStyle = `rgba(255, 255, 255, ${alpha * 0.15})`;
              ctx.lineWidth = 0.8;
            }
            
            ctx.stroke();
          }
        }
      }
      
      // Draw nodes on top
      nodes.forEach(node => node.draw(ctx));
      
      animationFrameId = requestAnimationFrame(render);
    };
    
    render();

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none -z-10">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-[#1A1A1A] via-[#1A1A1A] to-[#0a0a0a] z-0" />
      <canvas 
        ref={canvasRef} 
        className="absolute inset-0 w-full h-full opacity-60 z-10"
        style={{ mixBlendMode: 'screen' }}
      />
      {/* Falloff gradients to blend into page perfectly */}
      <div className="absolute bottom-0 left-0 right-0 h-48 bg-gradient-to-t from-background to-transparent z-20" />
    </div>
  );
}
