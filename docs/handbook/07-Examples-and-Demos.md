# Examples and Demos

To truly grasp the power of the Resonant Memory Mesh, you must see causality in action. The best way to learn is by studying the included demos.

## 1. The Diamond Heist (`detective_demo.py`)

The `detective_demo.py` script is the premier test case for RMM's "Reasoning Moat." It demonstrates how RMM can uncover hidden connections that a standard Vector Database (like Pinecone or Milvus) would completely miss.

### The Premise

You are a detective investigating the theft of the **Star of India** diamond from a museum. You feed an unorganized pile of 13 clues into the mesh. These clues cover a range of suspects, events, and locations.

### The Setup

1. **Ingestion**: The script generates synthetic embeddings for 13 related facts and ingests them into the mesh.
2. **Connection**: It then programmatically links these clues based on the logic of the crime.
   * `Clue 2 -> Clue 7 -> Clue 11 -> Clue 13`
   * Translation: The *Museum alarm was disabled* is linked to a *Custom electronic exploit tool*, which was found at *Blackwood Warehouse*, which is owned by *Marcus Vance*.

### The Query

The system is queried with a vector perfectly aligned with **"Analyze museum security breach"** (Clue 2). 

### The Result

A standard RAG system would return Clue 2 (highly similar), and maybe Clue 6 (deals with security protocols).

**RMM Returns:**
1.  **Clue 2:** "Museum alarm disabled..." (Direct match)
2.  **Clue 7:** "Custom electronic exploit tool found..." (1 Hop)
3.  **Clue 11:** "Exploit tool shipped to Blackwood Warehouse..." (2 Hops)
4.  **Clue 13:** "Blackwood Warehouse owned by Marcus Vance." (3 Hops)

Because RMM utilizes topological resonance, the energy from the "security breach" query flowed directly down the causal chain. The system successfully deduced that **Marcus Vance** is the prime suspect, even though the embedding for "Marcus Vance" has absolutely zero semantic overlap with "security breach."

### Running the Demo

```bash
python -m demo_features
```
*Note: Depending on your installation, you may run the detective demo directly if it's the active script.*

## 2. Integration with LLMs (RAG)

While RMM handles the retrieval, the generation step still requires an LLM.

Instead of passing the top-K semantically similar chunks directly to `gpt-4o` or `claude-3-opus`, you pass the **Top-K Most Resonant Nodes**.

```python
# 1. Query the mesh
results = mesh.query(user_query_vector, top_n=5)

# 2. Extract the text payloads from the metadata
context_chunks = [node.metadata["text"] for node in results.nodes]
context_string = "\n\n".join(context_chunks)

# 3. Construct your augmented prompt
prompt = f"""
You are an expert analyst. Answer the user's question using ONLY the provided causal context.

<context>
{context_string}
</context>

Question: {user_question}
"""

# 4. Generate the response
# (e.g., openai.chat.completions.create(..., messages=[{"role": "user", "content": prompt}]))
```

In the Diamond Heist scenario, feeding this resonant context to an LLM allows it to instantly output: *"Based on the evidence, the alarm was disabled using a custom tool found at Blackwood Warehouse, which points directly to Marcus Vance."* Standard RAG would fail to make this leap.
