export interface RMMNode {
    id: string;
    label: string;
    energy: number;
    metadata?: any;
    // Canvas physics props
    x?: number;
    y?: number;
    vx?: number;
    vy?: number;
}

export interface RMMEdge {
    source: string;
    target: string;
    weight: number;
}

export interface RMMConfig {
    beta: number; // Dissipative gain (0 - 1)
    lambdaDecay: number; // Decay constant
    threshold: number; // Pruning threshold
    maxHops: number;
}

export const DEFAULT_CONFIG: RMMConfig = {
    beta: 0.7,
    lambdaDecay: 1.0,
    threshold: 0.005,
    maxHops: 5,
};

export class RMMGraph {
    nodes: Map<string, RMMNode> = new Map();
    edges: RMMEdge[] = [];
    config: RMMConfig;

    // Cache for adjacency list
    adjacencyList: Map<string, { target: string; weight: number }[]> = new Map();

    constructor(config: Partial<RMMConfig> = {}) {
        this.config = { ...DEFAULT_CONFIG, ...config };
    }

    addNode(node: Omit<RMMNode, 'energy'>) {
        this.nodes.set(node.id, { ...node, energy: 0 });
        if (!this.adjacencyList.has(node.id)) {
            this.adjacencyList.set(node.id, []);
        }
        return this;
    }

    addEdge(source: string, target: string, weight: number = 1.0) {
        this.edges.push({ source, target, weight });
        const list = this.adjacencyList.get(source) || [];
        list.push({ target, weight });
        this.adjacencyList.set(source, list);
        return this;
    }

    resetEnergy() {
        this.nodes.forEach(node => {
            node.energy = 0;
        });
    }

    /**
     * Ignite a node, giving it initial energy (usually 1.0)
     */
    ignite(nodeId: string, initialEnergy: number = 1.0) {
        this.resetEnergy();
        const node = this.nodes.get(nodeId);
        if (node) {
            node.energy = initialEnergy;
        }
    }

    /**
     * Performs ONE hop of topological resonance.
     * Modifies the node energies in place.
     */
    step(deltaTime: number = 0.1): { activeNodes: string[] } {
        const nextEnergies = new Map<string, number>();
        let activeNodes: string[] = [];

        // 1. Decay all nodes lazily
        this.nodes.forEach((node, id) => {
            let energy = node.energy;
            if (energy > 0) {
                energy = energy * Math.exp(-this.config.lambdaDecay * deltaTime);
                if (energy < this.config.threshold) {
                    energy = 0;
                } else {
                    activeNodes.push(id);
                }
            }
            nextEnergies.set(id, energy);
        });

        // 2. Propagate energy along edges from active nodes
        this.nodes.forEach((sourceNode, sourceId) => {
            if (sourceNode.energy <= 0) return;

            const neighbors = this.adjacencyList.get(sourceId) || [];
            for (const edge of neighbors) {
                const transferredEnergy = sourceNode.energy * this.config.beta * edge.weight;

                let currentNextEnergy = nextEnergies.get(edge.target) || 0;
                // e_j(t+1) = max(0, min(1, e_decayed + Σ(e_i * β * W_ij)))
                let newEnergy = Math.min(1.0, currentNextEnergy + transferredEnergy);

                nextEnergies.set(edge.target, newEnergy);

                if (newEnergy >= this.config.threshold && !activeNodes.includes(edge.target)) {
                    activeNodes.push(edge.target);
                }
            }
        });

        // 3. Apply updates
        nextEnergies.forEach((energy, id) => {
            const node = this.nodes.get(id);
            if (node) {
                node.energy = energy;
            }
        });

        return { activeNodes };
    }

    /**
     * Get all active nodes sorted by energy descending
     */
    getResults(): RMMNode[] {
        return Array.from(this.nodes.values())
            .filter(n => n.energy >= this.config.threshold)
            .sort((a, b) => b.energy - a.energy);
    }

    /**
     * Generate preset graphs
     */
    static getPreset(presetName: "causal_chain" | "medical_diagnosis" | "bug_analysis" | "diamond_heist") {
        const graph = new RMMGraph();

        if (presetName === "causal_chain") {
            // 5-hop causal chain from paper
            graph.addNode({ id: "N1", label: "Query Context A" })
                .addNode({ id: "N2", label: "Bridging Fact B" })
                .addNode({ id: "N3", label: "Bridging Fact C" })
                .addNode({ id: "N4", label: "Bridging Fact D" })
                .addNode({ id: "N5", label: "Target Answer E" })
                .addNode({ id: "N6", label: "Irrelevant Fact" })
                .addNode({ id: "N7", label: "Semantic Distractor" });

            graph.addEdge("N1", "N2", 0.9)
                .addEdge("N2", "N3", 0.8)
                .addEdge("N3", "N4", 0.9)
                .addEdge("N4", "N5", 0.9)
                .addEdge("N1", "N6", 0.2)
                .addEdge("N6", "N7", 0.1);

        } else if (presetName === "medical_diagnosis") {
            graph.addNode({ id: "M1", label: "Symptom: Headaches" })
                .addNode({ id: "M2", label: "Symptom: Visual Aura" })
                .addNode({ id: "M3", label: "Condition: Migraine" })
                .addNode({ id: "M4", label: "Treatment: Triptans" })
                .addNode({ id: "M5", label: "Side-Effect: Vasoconstriction" })
                .addNode({ id: "M6", label: "Patient Record: Hypertension" })
                .addNode({ id: "M7", label: "Contraindication Alert" });

            graph.addEdge("M1", "M3", 0.8)
                .addEdge("M2", "M3", 0.9)
                .addEdge("M3", "M4", 0.9)
                .addEdge("M4", "M5", 0.7)
                .addEdge("M5", "M7", 0.9)
                .addEdge("M6", "M7", 0.9);

        } else if (presetName === "bug_analysis") {
            graph.addNode({ id: "B1", label: "Error: NullPointerException" })
                .addNode({ id: "B2", label: "Log: UserService:42" })
                .addNode({ id: "B3", label: "Commit: c7f9a2" })
                .addNode({ id: "B4", label: "PR: Add User Caching" })
                .addNode({ id: "B5", label: "Jira: Improve Login Speed" })
                .addNode({ id: "B6", label: "Design Doc: Cache Invalidation" });

            graph.addEdge("B1", "B2", 1.0)
                .addEdge("B2", "B3", 0.9)
                .addEdge("B3", "B4", 0.9)
                .addEdge("B4", "B5", 0.8)
                .addEdge("B5", "B6", 0.8);

        } else if (presetName === "diamond_heist") {
            // Core Narrative Nodes
            graph.addNode({ id: "D1", label: "Query: Museum Theft" })
                .addNode({ id: "D2", label: "Fact: Blue Diamond Stolen" })
                .addNode({ id: "D3", label: "Fact: Black Van Seen" })
                .addNode({ id: "D4", label: "Fact: Van tied to Front Co" })
                .addNode({ id: "D5", label: "Suspect: Victor Vance" })
                .addNode({ id: "D6", label: "Event: Bank Robbery" })
                .addNode({ id: "D7", label: "Context: Chicago" });

            // Noise Nodes (Distractors)
            graph.addNode({ id: "N1", label: "Concept: Deep-dish Pizza" })
                .addNode({ id: "N2", label: "Context: Windy Weather" })
                .addNode({ id: "N3", label: "Event: Museum Tour" })
                .addNode({ id: "N4", label: "Event: Art Gallery Opening" })
                .addNode({ id: "N5", label: "Vehicle: Red Sedan" })
                .addNode({ id: "N6", label: "Vehicle: White Truck" })
                .addNode({ id: "N7", label: "Suspect: Jimmy 'Fingers'" })
                .addNode({ id: "N8", label: "Suspect: 'Fast' Eddie" })
                .addNode({ id: "N9", label: "Front Co: Acme Corp" })
                .addNode({ id: "N10", label: "Front Co: Global Imports" })
                .addNode({ id: "N11", label: "Item: Stolen Painting" })
                .addNode({ id: "N12", label: "Item: Gold Watch" });

            // Direct semantic similarity connections (AutoLinker)
            // The Chain to Victor
            graph.addEdge("D1", "D2", 0.9)  // Query matches the theft fact
                .addEdge("D2", "D3", 0.8)  // Police tied the theft to the van
                .addEdge("D3", "D4", 0.9)  // DMV tied the van to the front company
                .addEdge("D4", "D5", 0.8); // Investigation tied front to Victor Vance

            // The Noise (Tied to various concepts, but not completing the chain)
            graph.addEdge("D1", "D7", 0.4)  // Query mentions Chicago
                .addEdge("D6", "D7", 0.5)  // Bank Robbery is also in Chicago
                .addEdge("D5", "D7", 0.2)  // Victor Vance is known to operate in Chicago
                .addEdge("N1", "D7", 0.6)  // Chicago -> Pizza
                .addEdge("N2", "D7", 0.6)  // Chicago -> Weather
                .addEdge("D1", "N3", 0.7)  // Museum Theft shares "Museum" with Museum Tour
                .addEdge("D1", "N4", 0.5)  // Museum Theft -> Art Gallery
                .addEdge("D2", "N11", 0.6) // Stolen Diamond -> Stolen Painting
                .addEdge("D2", "N12", 0.5) // Stolen Diamond -> Gold Watch
                .addEdge("D3", "N5", 0.4)  // Black Van -> Red Sedan (vehicles)
                .addEdge("D3", "N6", 0.4)  // Black Van -> White Truck
                .addEdge("D6", "N7", 0.7)  // Bank Robbery -> Jimmy Fingers
                .addEdge("N7", "D7", 0.3)  // Jimmy Fingers -> Chicago
                .addEdge("D6", "N8", 0.6)  // Bank Robbery -> Fast Eddie
                .addEdge("D4", "N9", 0.3)  // Front Co (Vance) -> Acme Corp
                .addEdge("D4", "N10", 0.3) // Front Co (Vance) -> Global Imports
                .addEdge("N9", "N8", 0.5); // Acme Corp -> Fast Eddie
        }

        return graph;
    }
}
