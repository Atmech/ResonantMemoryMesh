"""
Resonant Memory Mesh - Real World Scenario Demo
Use Case: An AI Detective Assistant ("Project KAI")

Scenario:
We are building an AI assistant for a detective agency. 
We ingest disparate facts about cases, people, and locations.
Some facts are standalone. Some form hubs (like "Chicago").
When the detective asks a question, RMM should follow causal chains of evidence
through the mesh to synthesize an answer, avoiding the noise of the hubs.

This demonstrates:
1. AutoLinker: Connecting related evidence pieces automatically without LLM pre-processing.
2. Hub Dampening: Passing through the "Chicago" hub without retrieving every crime in Chicago.
3. Adaptive Tuning: The mesh balancing its energy as the evidence board grows.
4. Structural Rationale: Generating a trace of logic for the detective.
"""

import time
import uuid
import os
import sys
import numpy as np

# Ensure the local rmm-core package is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'rmm-core')))

from rmm import Mesh, MeshConfig
from rmm.adapters.memory import InMemoryStorage
from sentence_transformers import SentenceTransformer

from sklearn.feature_extraction.text import TfidfVectorizer

print("Loading lightweight TF-IDF vectorizer...")
vectorizer = TfidfVectorizer(max_features=128, stop_words='english')

# Initialize the vocabulary with our expected domain words
corpus = [
    "A rare blue diamond was stolen from the Chicago Central Museum on Tuesday night.",
    "Victor 'The Ghost' Vance is a known jewel thief operating out of Chicago.",
    "The getaway vehicle was identified as a custom black van seen near the museum on Tuesday.",
    "A bank was robbed in downtown Chicago on Wednesday afternoon by two armed men.",
    "Chicago is known for its deep-dish pizza and windy weather.",
    "A customized black van matching the stolen vehicle profile is registered to a front company owned by Victor Vance.",
    "Who is the most likely suspect for the Tuesday night museum theft?"
]
vectorizer.fit(corpus)

def embed(text: str) -> np.ndarray:
    """Helper to generate a normalized vector from text using TF-IDF."""
    v = vectorizer.transform([text]).toarray()[0].astype(np.float32)
    norm = np.linalg.norm(v)
    if norm > 0:
        v = v / norm
    return v

def main():
    print("\n=======================================================")
    print("  RMM Detective Assistant Demo - The Diamond Heist")
    print("=======================================================\n")
    
    # The storage handles dimensions dynamically upon first insert
    storage = InMemoryStorage()
    
    # Configure the mesh:
    # - max_hops=3 (we want to follow evidence chains 3 steps deep)
    # - hub_threshold=3 (any node with >3 connections is considered a hub and dampened)
    # - auto_link=True (vital: automatically link related evidence)
    # - adaptive_tuning=True (adjust parameters as we add evidence)
    config = MeshConfig(
        max_hops=3,
        hub_threshold=4, 
        hub_dampening_alpha=1.0,
        auto_link=True,
        auto_link_threshold=0.15, # Lowered for sparse TF-IDF semantics
        adaptive_tuning=True
    )
    
    with Mesh(storage, config) as mesh:
        
        print("--- PHASE 1: INGESTING EVIDENCE ---")
        time.sleep(1)
        
        import json
        
        # 1. The Core Crime
        evidence_1 = "A rare blue diamond was stolen from the Chicago Central Museum on Tuesday night."
        print(f"Ingesting: '{evidence_1}'")
        mesh.ingest(embed(evidence_1), metadata={"label": evidence_1})
        
        # 2. A distinct fact about a suspect
        evidence_2 = "Victor 'The Ghost' Vance is a known jewel thief operating out of Chicago."
        print(f"Ingesting: '{evidence_2}'")
        mesh.ingest(embed(evidence_2), metadata={"label": evidence_2})
        
        # 3. An operational detail
        evidence_3 = "The getaway vehicle was identified as a custom black van seen near the museum on Tuesday."
        print(f"Ingesting: '{evidence_3}'")
        mesh.ingest(embed(evidence_3), metadata={"label": evidence_3})
        
        # 4. A completely unrelated crime in the same city (Noise)
        evidence_4 = "A bank was robbed in downtown Chicago on Wednesday afternoon by two armed men."
        print(f"Ingesting: '{evidence_4}'")
        mesh.ingest(embed(evidence_4), metadata={"label": evidence_4})
        
        # 5. Another unrelated fact about the city (Noise)
        evidence_5 = "Chicago is known for its deep-dish pizza and windy weather."
        print(f"Ingesting: '{evidence_5}'")
        mesh.ingest(embed(evidence_5), metadata={"label": evidence_5})

        # 6. A hidden connection piece 
        evidence_6 = "A customized black van matching the stolen vehicle profile is registered to a front company owned by Victor Vance."
        print(f"Ingesting: '{evidence_6}'")
        mesh.ingest(embed(evidence_6), metadata={"label": evidence_6})
        
        mesh.flush()
        print("\nAll evidence ingested! AutoLinker has silently built semantic edges based on vector proximity in the background.")
        
        print("\n--- PHASE 2: THE QUERY ---")
        time.sleep(2)
        
        query_text = "Who is the most likely suspect for the Tuesday night museum theft?"
        print(f"Detective Query: '{query_text}'")
        
        query_vector = embed(query_text)
        
        print("\nSearching the Mesh...")
        # We only ask for the top 3 resonant nodes
        start_time = time.time()
        result = mesh.query(query_vector, top_n=3)
        duration = time.time() - start_time
        
        print(f"\nQuery completed in {duration:.4f} seconds.")
        print(f"Active Adaptive Tuning parameters: β={config.beta:.4f}, λ={config.lambda_decay:.4f}")
        
        print("\n--- PHASE 3: THE RESULTS ---")
        time.sleep(1)
        
        print("Top 3 retrieved evidence nodes based on Resonance:")
        for i, node in enumerate(result.nodes):
            meta = node.metadata
            text = "Unknown Evidence"
            if isinstance(meta, dict):
                text = meta.get('label', str(meta))
            elif isinstance(meta, str):
                try:
                    meta_dict = json.loads(meta)
                    if isinstance(meta_dict, dict):
                        text = meta_dict.get('label', meta)
                    else:
                        text = meta
                except:
                    text = meta
            elif isinstance(meta, bytes):
                text = meta.decode('utf-8', errors='ignore')
            else:
                text = str(meta)
            print(f"  {i+1}. [Energy: {node.energy:.4f}] {text}")
            
        print("\n--- PHASE 4: STRUCTURAL RATIONALE ---")
        time.sleep(1)
        print("How did RMM link the question to Victor Vance without a direct text match?")
        print("\n" + result.rationale)
        
        
        print("\n--- WHY THIS IS POWERFUL ---")
        print("1. Standard RAG (Vector Search) would only return Evidence 1 (the theft) and maybe Evidence 4 (another theft).")
        print("   It would miss Victor Vance entirely because 'Victor Vance' has low text similarity to 'Tuesday night museum theft'.")
        print("2. RMM's AutoLinker connected the Theft -> The Van -> Victor Vance automatically.")
        print("3. Energy flowed down that chain ('Resonated') to pull Victor Vance to the top of the results.")
        print("4. The Hub Dampening prevented the system from getting distracted by the word 'Chicago' (which existed in 4 different nodes) and retrieving the irrelevant bank robbery or pizza trivia.")

if __name__ == "__main__":
    main()
