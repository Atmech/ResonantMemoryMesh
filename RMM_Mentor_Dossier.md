# RMM — Full Disclosure Dossier for Mentor Review

**Purpose.** This is not a pitch. It is a complete, unfiltered account of what was built, what was verified, what was wrong, and what we *hypothesize* — so you can guide us from facts, not from a story we curated to look good. Sections are separated into **FACTS** (verified, not up for debate), **DIAGNOSIS** (our interpretation), **HYPOTHESES** (believed but untested), **OPEN QUESTIONS** (where we need you), and **CONSTRAINTS**.

---

## 0. The original intent (founder's words)

Build a data structure *native* to how LLMs operate — a single substrate for memory, planning, and acting — inspired by the cortex (biophysics). The name: **Resonant Memory Mesh (RMM)**. The original paper title, *"Resonance is All You Need,"* deliberately echoes *"Attention is All You Need"* and *"Hopfield Networks is All You Need."* The ambition was attention-scale, not storage-scale.

---

## 1. FACTS — what was actually built

- **Rust kernel** (`rmm-rust`): a deterministic, layered BFS that spreads a scalar "energy" across a graph of memory nodes. Compiles, runs. Measured warm query latency **~2ms median, ~490 sequential qps** (in-memory, 1000 nodes, single core).
- **Python SDK** (`rmm-core`): `Mesh.ingest / connect / query`, in-memory + Postgres adapters, an "AutoLinker," adaptive tuning.
- **Retrieval path (verified by reading the code):** `query()` does a brute-force cosine vector search to pick *entry* nodes, then the kernel spreads energy from those entries over a **pre-existing edge graph**. Entry-node ignition energy = `e_max * significance` — **a constant, not a function of how well the node matches the query.**
- **Edge construction (verified):** the *only* automatic edge builder is the AutoLinker, which connects nodes by **cosine similarity**. There is **no** entity/relation/text→graph extraction of any kind in the codebase.
- **Test suite:** after an honesty pass, **18 passed, 2 skipped, 2 xfailed.** The 2 xfails are real limits: (a) the "hot path" still triggers a neighbor fault-in, yielding ~4× speedup not the claimed 10×; (b) concurrency is GIL-bound.

## 2. FACTS — what was wrong (found and corrected)

- **One fabricated number.** The README's headline "0.36ms hot latency" was the mathematical constant **e⁻¹ = 0.3679**, never measured. Now replaced with the real ~2ms. (Also: "900+ qps" unmeasured → real ~490; "~10ms RAG" was a strawman → removed.)
- **The headline demos were rigged by omission.** The "traverses a 5-hop causal chain with zero semantic overlap where RAG fails" demo (Bob→…→Omega) works **only because a human hand-wires the edges** with `mesh.connect()`. The benchmark test claimed a "3-group control study" but one group was never implemented, and a key assertion was vacuous. All relabeled honestly.

## 3. FACTS — the first honest evaluation (today)

Multi-hop retrieval, **MuSiQue, N=300**, local embeddings (`all-MiniLM-L6-v2`), **no LLM judge**. Metric = recall of gold supporting paragraphs / answer-bearing paragraph in top-k. Harness: `eval/run_eval.py` (reproducible). Five systems:

| System | Graph source | SupRecall@5 | AnsRecall@2 | AnsRecall@5 | AnsRecall@10 |
|---|---|---|---|---|---|
| vector-RAG | none (cosine) | **0.665** | 0.250 | 0.483 | 0.703 |
| RMM-proximity (as shipped) | cosine AutoLinker | 0.628 | 0.267 | 0.473 | 0.690 |
| **RMM-extracted** (the physics) | free spaCy-NER co-occurrence | **0.452** | 0.273 | 0.437 | 0.660 |
| **PPR-extracted** (control) | *same* NER graph | 0.602 | **0.390** | **0.570** | **0.783** |
| RMM-oracle (ceiling) | gold chain, hand-wired | 0.693 | 0.473 | 0.697 | 0.817 |

What these numbers establish, as fact:
1. **RMM as shipped (proximity) does not beat plain cosine.** Its graph is near-empty in a distractor corpus, so it collapses to a pass-through to vector search.
2. **RMM's energy physics is the *worst* system** when given a real (dense) graph — it floods and mis-ranks (the `[0,1]` activation clamp saturates everything, ties form, irrelevant hubs surface).
3. **Standard Personalized PageRank on the *identical* graph beats RMM's physics on every metric** — and beats vanilla RAG on answer recall (+9pt@5, +14pt@2, +8pt@10).
4. **Given a perfect graph (oracle), graph-based retrieval beats RAG decisively** (+21pt AnsRecall@5). So the bottleneck is *graph construction*, not the walk.

## 4. FACT — the mathematical identity that matters

RMM's "energy propagation" is, stripped of metaphor, a **restart-less Personalized PageRank** with an extra `[0,1]` clamp. PageRank's restart term is exactly what makes multi-hop retrieval stable; RMM removed it. Separately: **modern Hopfield associative memory retrieval is provably equal to transformer attention** (Ramsauer et al., *"Hopfield Networks is All You Need,"* 2020). Both facts are central to the diagnosis below.

---

## 5. DIAGNOSIS — where it drifted (our read, open to challenge)

1. **Cortex → cosine (the fatal substitution).** The brain links memories that *fire together* (Hebbian plasticity), not memories that *look alike*. RMM linked by embedding similarity — so it structurally cannot bridge a zero-semantic-overlap gap, which was the entire pitch.
2. **Data structure → physics engine.** The valuable idea was a *representation*; effort went into a *retrieval algorithm* that turned out to be a weaker PageRank.
3. **"Does it help an LLM?" → "0.36ms on a benchmark."** Performance theater replaced the real question. The fake number is the symptom.

---

## 6. THE ATTENTION QUESTION — three readings, presented without picking one

The founder's intent is to **sell attention, not memory**. There are three distinct relationships RMM could have to attention. We deliberately do **not** pre-select; we ask you to. Each is stated with its honest evidence status.

**Reading A — Servant (memory feeds attention).** RAG-style: memory retrieves, attention processes. *Risk:* low. *Novelty:* low. *Status:* this is what the current brief/paper actually say ("attention is for processing; the mesh is for retention"). Crowded (mem0, Zep, Letta, HippoRAG).

**Reading B — Generalization (memory *is* attention, extended).** Via the Hopfield identity, attention = associative recall over the context window; a **persistent, plastic** associative memory is therefore *attention generalized beyond the window, with a learning rule attention lacks.* *Risk:* medium. *Novelty:* real, and it lives in the plasticity. *Status:* conceptually grounded in published work; empirically untested here. Dissolves the "retention vs. processing" split.

**Reading C — Replacement ("Resonance is All You Need").** Resonant/associative dynamics as a substitute for, or augmentation of, softmax attention *inside the model.* *Risk:* high. *Novelty:* very high if true. *Status:* **un-backed.** Today's eval is evidence against the *untrained-graph-walk* version, but it does **not** test a *trained, integrated* version. This arena is held by well-funded lines of work (Mamba / linear attention / RETRO / Memorizing Transformers) and would require training compute we do not have. We are **not** killing this reading unilaterally — we are flagging that it is currently unfunded and unproven, and asking whether it is a credible bet or a trap.

---

## 7. HYPOTHESES — what we believe but have *not* shown

- **H1 (Plasticity).** If memory edges form and strengthen from *co-use in successful tasks* (Hebbian) and decay otherwise, then in a **multi-session** setting retrieval accuracy and task success **rise over time**, while static vector/graph baselines stay **flat**. → *Falsifiable: the learning curve's slope.*
- **H2 (Attention-generalization).** A persistent plastic associative memory is a faithful generalization of attention beyond the context window (Reading B), and this framing is both honest and defensible. → *Tested conceptually + empirically backed by H1.*
- **H3 (Replacement).** A resonance/associative mechanism could serve as an attention alternative or augmentation inside a model (Reading C). → *Would require training a small integrated model; beyond current budget.*

---

## 8. OPEN QUESTIONS — where we need your guidance

1. **Which hypothesis first?** H1 is cheap and decisive (~1 week, no budget). H3 is grand and expensive. Sequence?
2. **Is Reading B legitimate scholarship or overreach** for a solo, unfunded researcher?
3. **Is Reading C worth any pursuit** without training compute, or should it be explicitly shelved?
4. **Credit assignment** — how do we reinforce *causally* useful co-activations vs. coincidental ones? This is the crux of H1.
5. **Benchmark** — what existing longitudinal/multi-session benchmark truly tests plasticity (LongMemEval? LoCoMo?), or must we build a synthetic one (and how do we defend it from "you built a benchmark that flatters you")?
6. **Stability vs. plasticity** — known techniques to keep learned structure from drifting catastrophically?
7. **Paper, OSS tool, or company** — which is the honest vehicle, and which framing (A/B/C) fits which?
8. **The trivial-baseline test** — does plastic memory beat simply re-embedding or periodically fine-tuning? If not, it's not worth building.

---

## 9. CONSTRAINTS (so guidance is realistic)

- Solo founder. **No LLM API budget. No training compute.** Everything to date runs locally and free.
- Assets in hand: a working Rust graph kernel (~2ms), a Python SDK, a **reproducible** honest eval harness, and a free local NLP stack (spaCy + sentence-transformers + networkx).
- Disposition: willing to kill the idea fast if a number says so. Today's eval was run *to try to disprove our own engine.*

---

## 10. THE ASK

Tell us which of Readings A/B/C is real, which hypothesis to test first, what benchmark would convince *you*, and whether the honest version of this is a paper, a tool, or a company. We will bring you the learning-curve result next, whichever way it points.
