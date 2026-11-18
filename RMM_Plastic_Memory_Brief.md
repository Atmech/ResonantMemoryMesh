# RMM — A Memory Substrate That Learns From Use
### One-page brief for review

**One line:** Memory for LLM agents should be a *plastic* associative graph whose edges form and strengthen from co-use during real tasks — so retrieval improves with experience — instead of a static index where associations are frozen at write time.

---

## 1. The gap

Every production memory system today is **static**:

| System | Structure | Learns from use? |
|---|---|---|
| mem0 / Zep / Letta | vector index | No |
| Graphiti / Cognee | LLM-extracted graph | No |
| HippoRAG | PageRank over a graph built **once, offline** | No |

In all of them, the associations are fixed at write time. Retrieval quality on day 100 equals day 1. **No agent memory in the market gets better the more the agent uses it.** That is the open ground.

## 2. The thesis

Take the one mechanism the cortex is actually built on — **Hebbian plasticity** ("neurons that fire together, wire together") — and make it the edge-formation rule for agent memory. Associations should encode **what was useful together**, not **what looks similar** (which is all cosine similarity can ever capture).

## 3. The mechanism (the loop)

```
            ┌──────────────── current context (the cue) ────────────────┐
            │                                                            │
   recall   ▼                                                            │
  ┌───────────────────┐   spread activation    ┌──────────────────┐     │
  │ similarity lookup  │ ─────────────────────▶ │ along LEARNED     │     │
  │ (candidate nodes)  │   over the graph        │ edges → top-k     │ ────┘ inject into
  └───────────────────┘                          └──────────────────┘        context window
            ▲                                              │
            │                                              ▼
            │                              LLM attention computes the step
            │                                              │
            │   plasticity (the novel part)                ▼
            └────── strengthen edges among items used together in a       
                    SUCCESSFUL step · decay unused edges (forgetting)      
```

- **Nodes** = facts, observations, tool results, plan steps (each with an embedding).
- **Recall** = similarity pulls candidates → activation spreads along *learned* edges → top-k enters the context window.
- **Plasticity** = co-used items on a successful step get their edge strengthened; unused edges decay. Over time, structure reflects **task-usefulness, not surface similarity**.
- **Plans** = strengthened *sequences* of activations — episodic chains replayable as a unit.
- **Acting** = tool calls/results are nodes too, so the agent learns which memories + tools fire together for which goals.

## 4. How this relates to attention

Transformer attention is associative recall — but only over the **context window**, and **stateless across calls**. This substrate is the **persistent associative layer that feeds attention**: it chooses what enters the window so the LLM's own attention can compute on it — and, unlike attention, it **learns which associations matter across a lifetime.** The substrate is the synapse; attention is the spike.

## 5. The claim we will test (falsifiable)

> In a **multi-session** agent setting, retrieval accuracy and task success **improve over time** with Hebbian edges, while a static vector/graph baseline stays **flat**. The metric is the **learning curve** (performance vs. session index), not a single recall number.

If the curve is flat, the thesis is wrong — and we know in roughly a week.

### Experiment design
- **Benchmark:** a setting where experience accumulates — multi-session memory (LongMemEval / LoCoMo style) or a sequential agent task suite where related problems recur. *Not* one-shot QA (nothing to learn from).
- **Systems:** (a) static-vector baseline, (b) static-graph baseline, (c) RMM-plastic (Hebbian edges from co-use).
- **Metric:** retrieval accuracy and/or task success **as a function of episode index** → the slope. Plastic slope > 0, baselines ≈ 0 = win.
- **Cold start (expected):** plastic begins equal to the vector baseline and diverges as it learns. That's the signature, not a bug.

## 6. Honest risks (the hard parts)

1. **Credit assignment** — distinguishing *causally useful* co-activation from coincidence. The crux. Start conservative: reinforce only on verified-success steps; rely on decay to wash out noise.
2. **Right benchmark** — if no public multi-session set fits cleanly, we must build a synthetic harness, and then defend against "you built a benchmark that flatters you" by also reporting a public set.
3. **Stability vs. plasticity** — too much plasticity drifts catastrophically; too little never learns. A real tuning problem.
4. **Worth-the-complexity** — does the lift beat just periodically re-embedding or fine-tuning? Open and must be measured.

## 7. What we are retiring from the old framing (intellectual honesty)

A first honest evaluation (N=300, MuSiQue, local, no LLM judge) already settled several things — and that rigor is a credibility asset, not a liability:

- **"Energy/resonance physics" is not the novelty.** Measured head-to-head, the energy-propagation kernel was *worse* than textbook Personalized PageRank on the same graph. Propagation is a known primitive. **The novelty is the learning rule, not the walk.** (We keep the RMM name; "resonance" now means activation over edges that experience has strengthened.)
- **All latency/throughput claims are retired** until re-measured honestly (the prior "0.36ms" was not a measurement).
- **"Beats RAG on multi-hop from raw text" is retired** — unproven, and no longer the point. The point is *learning over time*.

---

**Status:** working Rust/Python graph substrate + a reproducible eval harness exist. The physics-as-moat framing is dropped. The next step is the learning-curve experiment above — the single test that decides whether plastic memory is real.
