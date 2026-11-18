"""
RMM Multi-hop Retrieval Eval Harness
=====================================
Tests whether RMM's graph-propagation physics retrieve multi-hop
supporting evidence better than vanilla vector-RAG.

No LLM judge. No answer generation. Pure retrieval recall against gold
supporting-paragraph labels from a real multi-hop QA dataset.

Usage:
    .venv/bin/python eval/run_eval.py [--n 300] [--k 2 5 10] [--dataset auto]

Datasets tried (in order):
    1. musique (MuSiQue-Answerable)
    2. 2wikimultihop
    3. hotpot_qa (distractor setting) — fallback

Systems:
    vector-RAG          cosine similarity top-k
    RMM-proximity       RMM with AutoLinker graph (as shipped)
    RMM-extracted       RMM over a FREE spaCy-NER entity-co-occurrence graph (no LLM, no gold)
    PPR-extracted       Personalized PageRank on the SAME NER graph (control for the physics)
    RMM-oracle-graph    RMM with hand-wired gold-chain edges (upper bound)
"""

import argparse
import json
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import uuid

import numpy as np

# Silence noisy loggers
logging.basicConfig(level=logging.ERROR)
logging.getLogger("rmm").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)

# ─────────────────────────────────────────────────────────────────────────────
# Dataset loading
# ─────────────────────────────────────────────────────────────────────────────

def load_musique(n: int):
    """
    MuSiQue-Answerable dev split.
    Each example has: question, paragraphs (list of {title, paragraph_text, is_supporting}),
    answer.
    Returns list of dicts: {question, paragraphs, gold_ids, answer}
    gold_ids = indices into paragraphs where is_supporting == True
    """
    from datasets import load_dataset
    print("[dataset] Trying musique (MuSiQue-Answerable)...", flush=True)
    ds = load_dataset("dgslibisey/MuSiQue", split="validation", trust_remote_code=True)
    examples = []
    for ex in ds:
        paragraphs = ex["paragraphs"]  # list of {idx, title, paragraph_text, is_supporting}
        if not paragraphs:
            continue
        texts = [p["paragraph_text"] for p in paragraphs]
        gold_ids = [i for i, p in enumerate(paragraphs) if p.get("is_supporting", False)]
        if not gold_ids:
            continue
        answer = ex.get("answer", "") or ""
        examples.append({"question": ex["question"], "paragraphs": texts,
                         "gold_ids": gold_ids, "answer": answer})
        if len(examples) >= n:
            break
    return "musique", examples


def load_2wiki(n: int):
    """
    2WikiMultihopQA dev split.
    Each example: question, context (list of [title, sentences]), supporting_facts ([title, sent_idx]),
    answer.
    We treat each (title) as one paragraph (joined sentences), gold = paragraphs whose title appears
    in supporting_facts.
    """
    from datasets import load_dataset
    print("[dataset] Trying 2wikimultihop...", flush=True)
    ds = load_dataset("bigbio/med_qa", split="validation", trust_remote_code=True)  # wrong, just placeholder
    # The correct dataset name:
    ds = load_dataset("voidful/2wikimultihopqa", split="validation", trust_remote_code=True)
    examples = []
    for ex in ds:
        contexts = ex.get("context", [])  # [[title, [sent1, sent2, ...]], ...]
        supporting_facts = ex.get("supporting_facts", [])  # [[title, sent_idx], ...]
        if not contexts or not supporting_facts:
            continue
        # Build paragraphs: join sentences per title
        paragraphs = []
        titles = []
        for item in contexts:
            title, sents = item[0], item[1]
            paragraphs.append(" ".join(sents))
            titles.append(title)
        # Gold: paragraph indices where title in supporting_fact titles
        gold_titles = set(sf[0] for sf in supporting_facts)
        gold_ids = [i for i, t in enumerate(titles) if t in gold_titles]
        if not gold_ids:
            continue
        answer = ex.get("answer", "") or ""
        examples.append({"question": ex["question"], "paragraphs": paragraphs,
                         "gold_ids": gold_ids, "answer": answer})
        if len(examples) >= n:
            break
    return "2wikimultihop", examples


def load_hotpot(n: int):
    """
    HotpotQA dev distractor split.
    Each example: question, context (list of [title, sentences]), supporting_facts,
    answer.
    """
    from datasets import load_dataset
    print("[dataset] Trying hotpot_qa (distractor)...", flush=True)
    ds = load_dataset("hotpot_qa", "distractor", split="validation", trust_remote_code=True)
    examples = []
    for ex in ds:
        contexts = ex.get("context", {})
        supporting_facts = ex.get("supporting_facts", {})
        if not contexts or not supporting_facts:
            continue
        # contexts: {title: [str], sentences: [[str]]} — actually it's a dict with 'title' and 'sentences' lists
        # supporting_facts: {title: [str], sent_id: [int]}
        titles_list = contexts.get("title", [])
        sentences_list = contexts.get("sentences", [])
        sf_titles = set(supporting_facts.get("title", []))
        paragraphs = [" ".join(sents) for sents in sentences_list]
        gold_ids = [i for i, t in enumerate(titles_list) if t in sf_titles]
        if not gold_ids or not paragraphs:
            continue
        answer = ex.get("answer", "") or ""
        examples.append({"question": ex["question"], "paragraphs": paragraphs,
                         "gold_ids": gold_ids, "answer": answer})
        if len(examples) >= n:
            break
    return "hotpot_qa", examples


def load_dataset_auto(n: int):
    loaders = [load_musique, load_hotpot, load_2wiki]
    last_err = None
    for loader in loaders:
        try:
            name, data = loader(n)
            if len(data) >= min(n, 50):
                print(f"[dataset] Loaded {len(data)} examples from {name}", flush=True)
                return name, data
            else:
                print(f"[dataset] {name} returned only {len(data)} examples, trying next", flush=True)
        except Exception as e:
            last_err = e
            print(f"[dataset] {loader.__name__} failed: {e}", flush=True)
    raise RuntimeError(f"All dataset loaders failed. Last error: {last_err}")


# ─────────────────────────────────────────────────────────────────────────────
# Embedding
# ─────────────────────────────────────────────────────────────────────────────

def load_embedder():
    from sentence_transformers import SentenceTransformer
    print("[embed] Loading all-MiniLM-L6-v2...", flush=True)
    model = SentenceTransformer("all-MiniLM-L6-v2")
    return model


def embed_texts(model, texts: List[str]) -> np.ndarray:
    """Embed and L2-normalize."""
    vecs = model.encode(texts, batch_size=64, show_progress_bar=False,
                        normalize_embeddings=True)
    return vecs.astype(np.float32)


# ─────────────────────────────────────────────────────────────────────────────
# System 1: Vector-RAG (pure cosine similarity)
# ─────────────────────────────────────────────────────────────────────────────

def retrieve_vector_rag(q_vec: np.ndarray, para_vecs: np.ndarray, k: int) -> List[int]:
    """Return top-k paragraph indices by cosine sim (vecs already normalized)."""
    scores = para_vecs @ q_vec  # (n,)
    top_k = int(min(k, len(scores)))
    return list(np.argsort(scores)[::-1][:top_k])


# ─────────────────────────────────────────────────────────────────────────────
# System 2: RMM-proximity (AutoLinker graph)
# ─────────────────────────────────────────────────────────────────────────────

def build_rmm_proximity(para_vecs: np.ndarray, para_texts: List[str],
                        auto_link_threshold: float = 0.6):
    """
    Ingest all paragraphs into a fresh InMemoryStorage Mesh with auto_link=True.
    Returns (mesh, id_to_idx, idx_to_id).
    """
    from rmm import Mesh, MeshConfig
    from rmm.adapters.memory import InMemoryStorage

    config = MeshConfig(
        auto_link=True,
        auto_link_threshold=auto_link_threshold,
    )
    storage = InMemoryStorage()
    mesh = Mesh(storage, config)
    mesh.start()

    idx_to_id = {}
    for i, (vec, text) in enumerate(zip(para_vecs, para_texts)):
        nid = mesh.ingest(
            vector=vec.copy(),
            metadata={"label": text[:80], "para_idx": i},
            significance=1.0,
        )
        idx_to_id[i] = nid

    mesh.flush()
    id_to_idx = {v: k for k, v in idx_to_id.items()}
    return mesh, id_to_idx, idx_to_id


def retrieve_rmm(mesh, id_to_idx: Dict, q_vec: np.ndarray, k: int) -> Tuple[List[int], bool]:
    """
    Query mesh, return top-k para indices by energy and whether any entry ignited.
    """
    result = mesh.query(q_vec, top_n=k)
    ignited = len(result.nodes) > 0
    retrieved = []
    for node in result.nodes:
        idx = id_to_idx.get(node.id)
        if idx is not None:
            retrieved.append(idx)
        if len(retrieved) >= k:
            break
    # If mesh returned fewer than k, pad with vector fallback? No — report honestly.
    return retrieved, ignited


# ─────────────────────────────────────────────────────────────────────────────
# System 3: RMM-oracle-graph (gold chain wired by hand)
# ─────────────────────────────────────────────────────────────────────────────

def build_rmm_oracle(para_vecs: np.ndarray, para_texts: List[str],
                     gold_ids: List[int], q_vec: np.ndarray):
    """
    Build a fresh mesh with auto_link=False.
    Then:
      - Find the paragraph most similar to the query → entry node.
      - Wire edges along the GOLD chain (consecutive gold paras, bidirectional, weight=0.9).
      - Connect entry to the first gold paragraph (if not already same).
    Returns (mesh, id_to_idx, idx_to_id).
    """
    from rmm import Mesh, MeshConfig, Edge
    from rmm.adapters.memory import InMemoryStorage

    config = MeshConfig(auto_link=False)
    storage = InMemoryStorage()
    mesh = Mesh(storage, config)
    mesh.start()

    idx_to_id = {}
    for i, (vec, text) in enumerate(zip(para_vecs, para_texts)):
        nid = mesh.ingest(
            vector=vec.copy(),
            metadata={"label": text[:80], "para_idx": i},
            significance=1.0,
        )
        idx_to_id[i] = nid

    mesh.flush()
    id_to_idx = {v: k for k, v in idx_to_id.items()}

    # Wire gold chain (consecutive gold paragraphs bidirectionally)
    GOLD_WEIGHT = 0.9
    for a, b in zip(gold_ids[:-1], gold_ids[1:]):
        id_a = idx_to_id[a]
        id_b = idx_to_id[b]
        mesh.connect(id_a, id_b, weight=GOLD_WEIGHT)
        mesh.connect(id_b, id_a, weight=GOLD_WEIGHT)

    # Connect entry node (most query-similar) to first gold paragraph
    scores = para_vecs @ q_vec
    entry_idx = int(np.argmax(scores))
    if entry_idx not in gold_ids and gold_ids:
        mesh.connect(idx_to_id[entry_idx], idx_to_id[gold_ids[0]], weight=GOLD_WEIGHT)
        mesh.connect(idx_to_id[gold_ids[0]], idx_to_id[entry_idx], weight=GOLD_WEIGHT)

    mesh.flush()
    return mesh, id_to_idx, idx_to_id


# ─────────────────────────────────────────────────────────────────────────────
# Free local text→graph: spaCy NER entity co-occurrence (no LLM, no gold labels)
# ─────────────────────────────────────────────────────────────────────────────

_NLP = None
# Named-entity types that make good multi-hop "bridge" nodes. Numerics
# (DATE/CARDINAL/MONEY/...) excluded — too noisy with the small model.
_ENT_TYPES = {"PERSON", "ORG", "GPE", "LOC", "FAC", "EVENT",
              "WORK_OF_ART", "PRODUCT", "NORP", "LAW", "LANGUAGE"}


def _get_nlp():
    global _NLP
    if _NLP is None:
        import spacy
        # Disable parser + lemmatizer for speed; we only need the NER component.
        _NLP = spacy.load("en_core_web_sm", disable=["parser", "lemmatizer"])
    return _NLP


def extract_entities(para_texts: List[str]) -> List[set]:
    """Free local NER → list[set[str]] of normalized named entities per paragraph."""
    nlp = _get_nlp()
    ent_sets = []
    for doc in nlp.pipe(para_texts, batch_size=32):
        ents = set()
        for e in doc.ents:
            if e.label_ in _ENT_TYPES:
                norm = " ".join(e.text.lower().split())
                if len(norm) >= 2:
                    ents.add(norm)
        ent_sets.append(ents)
    return ent_sets


def build_cooccurrence_edges(ent_sets: List[set]) -> List[Tuple[int, int, float]]:
    """
    Edges between paragraphs that share >=1 named entity. These are exactly the
    'zero semantic overlap' bridges the cosine AutoLinker structurally cannot make.
    Weight scales (mildly) with number of shared entities. Returns [(i, j, weight)], i<j.
    """
    edges = []
    n = len(ent_sets)
    for i in range(n):
        if not ent_sets[i]:
            continue
        for j in range(i + 1, n):
            shared = ent_sets[i] & ent_sets[j]
            if shared:
                w = min(0.95, 0.55 + 0.1 * len(shared))
                edges.append((i, j, w))
    return edges


def build_rmm_extracted(para_vecs: np.ndarray, para_texts: List[str],
                        edges: List[Tuple[int, int, float]]):
    """
    RMM over a FREE spaCy-NER entity-co-occurrence graph (no gold, no LLM).
    Entry nodes still chosen by the engine's own vector search over the query.
    """
    from rmm import Mesh, MeshConfig
    from rmm.adapters.memory import InMemoryStorage

    config = MeshConfig(auto_link=False)
    storage = InMemoryStorage()
    mesh = Mesh(storage, config)
    mesh.start()

    idx_to_id = {}
    for i, (vec, text) in enumerate(zip(para_vecs, para_texts)):
        nid = mesh.ingest(vector=vec.copy(),
                          metadata={"label": text[:80], "para_idx": i},
                          significance=1.0)
        idx_to_id[i] = nid
    mesh.flush()

    for (i, j, w) in edges:
        mesh.connect(idx_to_id[i], idx_to_id[j], weight=w)
        mesh.connect(idx_to_id[j], idx_to_id[i], weight=w)
    mesh.flush()

    id_to_idx = {v: k for k, v in idx_to_id.items()}
    return mesh, id_to_idx, idx_to_id


def retrieve_ppr_extracted(edges: List[Tuple[int, int, float]], n_paras: int,
                           para_vecs: np.ndarray, q_vec: np.ndarray, k: int) -> List[int]:
    """
    CONTROL: Personalized PageRank (restart-based random walk) on the SAME extracted
    graph. Personalization = relu(cosine sim to query), normalized. If RMM's energy
    physics ≈ this, the physics adds nothing over standard graph propagation.
    """
    import networkx as nx
    G = nx.Graph()
    G.add_nodes_from(range(n_paras))
    for (i, j, w) in edges:
        G.add_edge(i, j, weight=w)

    sims = para_vecs @ q_vec
    pers = np.clip(sims, 0, None).astype(float)
    if pers.sum() <= 0:
        pers = np.ones(n_paras, dtype=float)
    pers = pers / pers.sum()
    pers_dict = {i: float(pers[i]) for i in range(n_paras)}

    try:
        pr = nx.pagerank(G, alpha=0.85, personalization=pers_dict,
                         weight="weight", max_iter=200)
    except Exception:
        pr = pers_dict
    ranked = sorted(range(n_paras), key=lambda i: -pr.get(i, 0.0))
    return ranked[:int(min(k, n_paras))]


# ─────────────────────────────────────────────────────────────────────────────
# Metrics
# ─────────────────────────────────────────────────────────────────────────────

def compute_metrics(retrieved: List[int], gold_ids: List[int],
                    answer: str, para_texts: List[str]) -> dict:
    """
    Returns dict with:
      supporting_recall  — fraction of gold paras in retrieved
      all_found          — 1 if all gold paras in retrieved else 0
      answer_recall      — 1 if answer string found in any retrieved para else 0
    """
    gold_set = set(gold_ids)
    retr_set = set(retrieved)
    n_gold = max(len(gold_set), 1)

    supporting_recall = len(gold_set & retr_set) / n_gold
    all_found = 1 if gold_set <= retr_set else 0

    # Answer-string recall: case-insensitive substring match in any retrieved paragraph
    answer_recall = 0
    if answer:
        ans_lower = answer.lower().strip()
        for idx in retrieved:
            if idx < len(para_texts) and ans_lower in para_texts[idx].lower():
                answer_recall = 1
                break

    return {
        "supporting_recall": supporting_recall,
        "all_found": all_found,
        "answer_recall": answer_recall,
    }


def aggregate(per_q: List[dict]) -> dict:
    n = max(len(per_q), 1)
    return {
        "supporting_recall": round(sum(x["supporting_recall"] for x in per_q) / n, 4),
        "all_found": round(sum(x["all_found"] for x in per_q) / n, 4),
        "answer_recall": round(sum(x["answer_recall"] for x in per_q) / n, 4),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main eval loop
# ─────────────────────────────────────────────────────────────────────────────

def run_eval(n: int, ks: List[int], auto_link_threshold: float = 0.6):
    results = {}
    t0 = time.time()

    # Load dataset
    dataset_name, examples = load_dataset_auto(n)
    actual_n = len(examples)
    print(f"[eval] Dataset: {dataset_name}, N={actual_n}", flush=True)

    # Load embedder
    model = load_embedder()

    # Per-system accumulators per k
    systems = ["vector-rag", "rmm-proximity", "rmm-extracted", "ppr-extracted", "rmm-oracle-graph"]
    accum = {sys: {k: [] for k in ks} for sys in systems}
    no_ignite_proximity = 0
    no_ignite_oracle = 0
    no_ignite_extracted = 0
    # Graph-density diagnostics for the free extracted graph
    edge_counts = []        # #co-occurrence edges per question
    ent_per_para = []       # avg #entities per paragraph per question
    q_with_graph = 0        # questions whose extracted graph has >=1 edge

    print(f"[eval] Starting eval loop over {actual_n} questions...", flush=True)
    t_loop = time.time()

    for qi, ex in enumerate(examples):
        if qi % 50 == 0:
            elapsed = time.time() - t_loop
            print(f"  [{qi}/{actual_n}] elapsed={elapsed:.1f}s", flush=True)

        question = ex["question"]
        paras = ex["paragraphs"]
        gold_ids = ex["gold_ids"]
        answer = ex["answer"]

        if not paras or not gold_ids:
            continue

        # Embed question + paragraphs together for efficiency
        all_texts = [question] + paras
        all_vecs = embed_texts(model, all_texts)
        q_vec = all_vecs[0]
        para_vecs = all_vecs[1:]  # (n_paras, dim) — already normalized

        # ── System 1: vector-RAG ──────────────────────────────────────────────
        for k in ks:
            retrieved = retrieve_vector_rag(q_vec, para_vecs, k)
            m = compute_metrics(retrieved, gold_ids, answer, paras)
            accum["vector-rag"][k].append(m)

        # ── System 2: RMM-proximity ──────────────────────────────────────────
        try:
            mesh_prox, id_to_idx_prox, idx_to_id_prox = build_rmm_proximity(
                para_vecs, paras, auto_link_threshold=auto_link_threshold
            )
            for k in ks:
                retrieved, ignited = retrieve_rmm(mesh_prox, id_to_idx_prox, q_vec, k)
                if not ignited:
                    no_ignite_proximity += 1
                m = compute_metrics(retrieved, gold_ids, answer, paras)
                accum["rmm-proximity"][k].append(m)
            mesh_prox.close()
        except Exception as e:
            print(f"  [WARN] RMM-proximity failed q={qi}: {e}", flush=True)
            for k in ks:
                accum["rmm-proximity"][k].append({"supporting_recall": 0, "all_found": 0, "answer_recall": 0})

        # ── Free local text→graph (shared by System 3 + 4) ───────────────────
        try:
            ent_sets = extract_entities(paras)
            edges = build_cooccurrence_edges(ent_sets)
        except Exception as e:
            print(f"  [WARN] extraction failed q={qi}: {e}", flush=True)
            ent_sets, edges = [set() for _ in paras], []
        edge_counts.append(len(edges))
        ent_per_para.append(sum(len(s) for s in ent_sets) / max(len(ent_sets), 1))
        if edges:
            q_with_graph += 1

        # ── System 3: RMM-extracted (free spaCy NER co-occurrence graph) ──────
        try:
            mesh_ext, id_to_idx_ext, idx_to_id_ext = build_rmm_extracted(
                para_vecs, paras, edges
            )
            for k in ks:
                retrieved, ignited = retrieve_rmm(mesh_ext, id_to_idx_ext, q_vec, k)
                if not ignited:
                    no_ignite_extracted += 1
                m = compute_metrics(retrieved, gold_ids, answer, paras)
                accum["rmm-extracted"][k].append(m)
            mesh_ext.close()
        except Exception as e:
            print(f"  [WARN] RMM-extracted failed q={qi}: {e}", flush=True)
            for k in ks:
                accum["rmm-extracted"][k].append({"supporting_recall": 0, "all_found": 0, "answer_recall": 0})

        # ── System 4: PPR-extracted (PageRank control on SAME graph) ──────────
        try:
            for k in ks:
                retrieved = retrieve_ppr_extracted(edges, len(paras), para_vecs, q_vec, k)
                m = compute_metrics(retrieved, gold_ids, answer, paras)
                accum["ppr-extracted"][k].append(m)
        except Exception as e:
            print(f"  [WARN] PPR-extracted failed q={qi}: {e}", flush=True)
            for k in ks:
                accum["ppr-extracted"][k].append({"supporting_recall": 0, "all_found": 0, "answer_recall": 0})

        # ── System 5: RMM-oracle-graph ────────────────────────────────────────
        try:
            mesh_oracle, id_to_idx_oracle, idx_to_id_oracle = build_rmm_oracle(
                para_vecs, paras, gold_ids, q_vec
            )
            for k in ks:
                retrieved, ignited = retrieve_rmm(mesh_oracle, id_to_idx_oracle, q_vec, k)
                if not ignited:
                    no_ignite_oracle += 1
                m = compute_metrics(retrieved, gold_ids, answer, paras)
                accum["rmm-oracle-graph"][k].append(m)
            mesh_oracle.close()
        except Exception as e:
            print(f"  [WARN] RMM-oracle-graph failed q={qi}: {e}", flush=True)
            for k in ks:
                accum["rmm-oracle-graph"][k].append({"supporting_recall": 0, "all_found": 0, "answer_recall": 0})

    total_time = time.time() - t0
    avg_edges = sum(edge_counts) / max(len(edge_counts), 1)
    avg_ents = sum(ent_per_para) / max(len(ent_per_para), 1)
    print(f"[eval] Done. Total time: {total_time:.1f}s  ({total_time/actual_n:.2f}s/q)", flush=True)
    print(f"[eval] no-ignite events: proximity={no_ignite_proximity}, "
          f"extracted={no_ignite_extracted}, oracle={no_ignite_oracle}", flush=True)
    print(f"[eval] extracted-graph: avg {avg_edges:.1f} edges/q, avg {avg_ents:.1f} entities/para, "
          f"{q_with_graph}/{actual_n} questions had >=1 edge", flush=True)

    # Aggregate
    agg = {}
    for sys in systems:
        agg[sys] = {}
        for k in ks:
            agg[sys][k] = aggregate(accum[sys][k])

    return {
        "dataset": dataset_name,
        "n": actual_n,
        "ks": ks,
        "auto_link_threshold": auto_link_threshold,
        "total_time_s": round(total_time, 2),
        "no_ignite": {"proximity": no_ignite_proximity,
                      "extracted": no_ignite_extracted,
                      "oracle": no_ignite_oracle},
        "extracted_graph_stats": {
            "avg_edges_per_q": round(avg_edges, 2),
            "avg_entities_per_para": round(avg_ents, 2),
            "questions_with_graph": q_with_graph,
        },
        "results": agg,
        "per_question": {
            sys: {str(k): accum[sys][k] for k in ks}
            for sys in systems
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Reporting
# ─────────────────────────────────────────────────────────────────────────────

def print_table(data: dict):
    ks = data["ks"]
    results = data["results"]
    dataset = data["dataset"]
    n = data["n"]

    # Column headers
    metrics = ["sup_recall", "all_found", "ans_recall"]
    metric_labels = {
        "sup_recall": "SupportingRecall",
        "all_found": "AllFound",
        "ans_recall": "AnsRecall",
    }

    # Build header row
    col_labels = []
    for k in ks:
        for m in metrics:
            col_labels.append(f"{metric_labels[m]}@{k}")

    header = "| System | " + " | ".join(col_labels) + " |"
    sep = "|--------|" + "|".join(["-" * (len(c) + 2) for c in col_labels]) + "|"

    system_display = {
        "vector-rag":        "vector-RAG         (cosine, no graph)",
        "rmm-proximity":     "RMM-proximity      (AutoLinker graph, shipped)",
        "rmm-extracted":     "RMM-extracted      (free spaCy NER graph)",
        "ppr-extracted":     "PPR-extracted      (PageRank, same NER graph)",
        "rmm-oracle-graph":  "RMM-oracle-graph   (gold-chain graph, upper bound)",
    }

    row_order = ["vector-rag", "rmm-proximity", "rmm-extracted", "ppr-extracted", "rmm-oracle-graph"]
    rows = []
    for sys in row_order:
        vals = []
        for k in ks:
            r = results[sys][k]
            vals.append(f"{r['supporting_recall']:.3f}")
            vals.append(f"{r['all_found']:.3f}")
            vals.append(f"{r['answer_recall']:.3f}")
        rows.append(f"| {system_display[sys]} | " + " | ".join(vals) + " |")

    print()
    print(f"## RMM Multi-hop Retrieval Eval")
    print(f"Dataset: **{dataset}** | N={n} questions | auto_link_threshold={data['auto_link_threshold']}")
    print(f"Runtime: {data['total_time_s']:.1f}s | {data['total_time_s']/max(n,1):.2f}s/q")
    print(f"No-ignite events: proximity={data['no_ignite']['proximity']}, oracle={data['no_ignite']['oracle']}")
    print()
    print(header)
    print(sep)
    for row in rows:
        print(row)
    print()
    print("**Metric definitions:**")
    print("- SupportingRecall@k: fraction of gold supporting paragraphs found in top-k (averaged over questions)")
    print("- AllFound@k: fraction of questions where ALL gold paragraphs appear in top-k")
    print("- AnsRecall@k: fraction of questions where the gold answer string appears in any top-k paragraph")
    print()
    print("**Graph definitions:**")
    print("- vector-RAG: pure cosine similarity ranking, no graph structure")
    print("- RMM-proximity: graph built by AutoLinker (cosine threshold=0.6) — RMM as shipped")
    print("- RMM-extracted: graph built FREE by spaCy NER entity co-occurrence (no LLM, no gold)")
    print("- PPR-extracted: networkx Personalized PageRank on the SAME NER graph — control for the physics")
    print("- RMM-oracle-graph: gold supporting-fact chain hand-wired — upper bound")
    gs = data.get("extracted_graph_stats")
    if gs:
        print()
        print(f"**Extracted-graph density:** avg {gs['avg_edges_per_q']} edges/q, "
              f"avg {gs['avg_entities_per_para']} entities/para, "
              f"{gs['questions_with_graph']}/{n} questions had a non-empty graph")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="RMM multi-hop retrieval eval")
    parser.add_argument("--n", type=int, default=300, help="Number of questions to evaluate (default: 300)")
    parser.add_argument("--k", type=int, nargs="+", default=[2, 5, 10], help="Top-k values to evaluate (default: 2 5 10)")
    parser.add_argument("--dataset", type=str, default="auto",
                        help="Dataset to use: auto (default), musique, 2wiki, hotpot")
    parser.add_argument("--threshold", type=float, default=0.6,
                        help="AutoLinker cosine threshold for RMM-proximity (default: 0.6)")
    parser.add_argument("--out", type=str, default="eval/results.json",
                        help="Output JSON path (default: eval/results.json)")
    args = parser.parse_args()

    print(f"[config] N={args.n}, k={args.k}, dataset={args.dataset}, threshold={args.threshold}")
    print(f"[config] Output: {args.out}")
    print()

    data = run_eval(n=args.n, ks=args.k, auto_link_threshold=args.threshold)

    # Save raw results
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Remove per_question from JSON if too large (keep summary only)
    save_data = {k: v for k, v in data.items() if k != "per_question"}
    with open(out_path, "w") as f:
        json.dump(save_data, f, indent=2)
    print(f"[output] Raw results → {out_path}", flush=True)

    # Print final table
    print_table(data)


if __name__ == "__main__":
    main()
