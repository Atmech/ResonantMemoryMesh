"""Illustrate retrieval on six fictional reports using TF-IDF and proximity links."""

import time
import uuid
import os
import sys
import numpy as np

# Ensure the local rmm-core package is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'rmm-core')))

from rmm import Mesh, MeshConfig
from rmm.adapters.memory import InMemoryStorage

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
        print("\nAll evidence ingested! The graph uses proximity links.")
        
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
        print(f"Base parameters: β={config.beta:.4f}, λ={config.lambda_decay:.4f}")
        
        print("\n--- PHASE 3: THE RESULTS ---")
        time.sleep(1)
        
        print("Top 3 retrieved evidence nodes based on Resonance:")
        for i, node in enumerate(result.nodes[:3], start=1):
            print(f"  {i}. [Energy: {node.energy:.4f}] {node.metadata['label']}")

        print("\nDirect cosine matches")
        for i, node_id in enumerate(storage.vector_search(query_vector, top_k=3), start=1):
            print(f"  {i}. {storage.get_node(node_id).metadata['label']}")

        print("\nGraph rationale")
        print(result.rationale)


if __name__ == "__main__":
    main()
