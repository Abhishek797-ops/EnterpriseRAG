"""
Pagani Zonda R – Vector Store with FAISS + Gemini Embeddings
Handles document storage, embedding, persistence, and role-based search.
"""

import os
import re
import pickle
import logging
import json
import numpy as np
import faiss
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("pagani.vector_store")

# ── Gemini Configuration ──
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
EMBEDDING_MODEL = "models/gemini-embedding-001"

# ── Persistence Paths ──
INDEX_PATH = os.path.join(os.path.dirname(__file__), "faiss_index.bin")
META_PATH = os.path.join(os.path.dirname(__file__), "faiss_meta.pkl")

# ── Enterprise Knowledge Base ──
# Each document has content and role_access metadata
PAGANI_DOCUMENTS = [
    {
        "content": "The Pagani Zonda R is the ultimate track-focused evolution of the Zonda lineage. It was unveiled in 2007 as a pure racing machine not homologated for road use. The Zonda R represents the pinnacle of Pagani's engineering philosophy: art and science in perfect harmony. It was designed by Horacio Pagani and his team at Pagani Automobili in Modena, Italy.",
        "role_access": ["admin", "engineer", "viewer"],
        "source": "Pagani Heritage Archives"
    },
    {
        "content": "The Pagani Zonda R is powered by a naturally aspirated Mercedes-Benz AMG M120 6.0-liter V12 engine, producing 750 horsepower at 7,500 RPM and 710 Nm of torque at 5,700 RPM. The engine is mated to a sequential 6-speed gearbox developed in collaboration with Xtrac. The V12 delivers a linear power curve with instantaneous throttle response, characteristic of naturally aspirated high-performance engines.",
        "role_access": ["admin", "engineer", "viewer"],
        "source": "Engine Technical Specification Sheet"
    },
    {
        "content": "The Zonda R features a carbon-titanium monocoque chassis, a material technology pioneered by Pagani. The monocoque weighs just 68 kg and provides exceptional torsional rigidity of 32,000 Nm/degree. The entire body is constructed from advanced carbon fiber composites, including the floor, roof, and aerodynamic elements. Total dry weight is 1,070 kg, giving a power-to-weight ratio of 701 hp per tonne.",
        "role_access": ["admin", "engineer", "viewer"],
        "source": "Chassis Engineering Report"
    },
    {
        "content": "Aerodynamics: The Zonda R generates over 1,500 kg of downforce at 300 km/h through its advanced aerodynamic package. The front splitter, rear diffuser, and adjustable rear wing work together to create ground-effect downforce. The underbody is fully flat with Venturi tunnels. The drag coefficient is optimized for circuit use rather than top speed. Wind tunnel testing was conducted at Dallara's facility in Varano de' Melegari.",
        "role_access": ["admin", "engineer"],
        "source": "Aerodynamics R&D Report"
    },
    {
        "content": "Performance data: The Pagani Zonda R accelerates from 0-100 km/h in 2.7 seconds, 0-200 km/h in 6.2 seconds, and has a top speed exceeding 350 km/h. It set a lap record at the Nürburgring Nordschleife with a time of 6:47.50 in 2010, making it one of the fastest cars to ever lap the circuit. Braking from 100 km/h to standstill takes just 29 meters.",
        "role_access": ["admin", "engineer", "viewer"],
        "source": "Performance Test Results"
    },
    {
        "content": "The braking system features Brembo carbon-ceramic disc brakes with 380 mm front and 355 mm rear rotors. The calipers are 6-piston units at the front and 4-piston at the rear, painted in the signature Pagani blue. The brake-by-wire system offers adjustable brake bias. The system withstands temperatures up to 1,000°C during sustained track use without fade.",
        "role_access": ["admin", "engineer"],
        "source": "Brake System Technical Manual"
    },
    {
        "content": "The suspension system uses a double-wishbone configuration on all four corners with pushrod-activated Öhlins TTX 4-way adjustable dampers. Anti-roll bars are adjustable front and rear. Ride height, camber, and toe are fully adjustable for circuit optimization. The suspension geometry is derived from Pagani's motorsport program.",
        "role_access": ["admin", "engineer"],
        "source": "Suspension Engineering Documentation"
    },
    {
        "content": "Production and exclusivity: Only 15 units of the Pagani Zonda R were ever produced. Each car is hand-built at the Pagani Atelier in San Cesario sul Panaro, near Modena, Italy. Production began in 2007 and all units were allocated before public announcement. Current estimated market value exceeds €6 million. Original MSRP was approximately €1.5 million.",
        "role_access": ["admin", "engineer", "viewer"],
        "source": "Production Registry"
    },
    {
        "content": "The Zonda R's interior features a minimalist, race-focused cockpit with exposed carbon fiber throughout. The dashboard houses a digital telemetry display, gear position indicator, and essential gauges only. The steering wheel is a removable unit with integrated shift paddles. Seats are fixed-back carbon fiber racing shells with 6-point harnesses. Interior weight was stripped to an absolute minimum — no air conditioning, no infotainment, no sound insulation.",
        "role_access": ["admin", "engineer", "viewer"],
        "source": "Interior Design Specifications"
    },
    {
        "content": "Financial overview: The Pagani Zonda R retailed at €1.5 million excluding local taxes and duties. Maintenance costs for the engine service alone exceed €25,000. A complete carbon-ceramic brake set replacement costs approximately €35,000. Annual insurance premiums range from €40,000 to €80,000 depending on jurisdiction. The Zonda R has appreciated in value by approximately 300% since its original sale, with recent auction prices exceeding €6 million.",
        "role_access": ["admin"],
        "source": "Financial & Ownership Report"
    },
    {
        "content": "The Zonda R uses Pirelli P Zero slick tires specifically developed for this car: 265/645 R19 front and 335/705 R20 rear. Magnesium APP forged wheels save 12 kg over aluminum equivalents. Tire operational temperature range is 80-110°C for optimal grip. The car features a central locking nut wheel design derived from Formula 1 technology.",
        "role_access": ["admin", "engineer"],
        "source": "Tire & Wheel Technical Sheet"
    },
    {
        "content": "The exhaust system is constructed entirely from Inconel 625 superalloy, the same material used in Formula 1 and aerospace applications. The quad-exit exhaust produces the Zonda R's iconic sound signature, measured at 120 dB at full throttle. The exhaust system weighs only 5.8 kg total. Headers are equal-length for optimal exhaust gas scavenging and power delivery.",
        "role_access": ["admin", "engineer", "viewer"],
        "source": "Exhaust System Engineering Report"
    },
]


class VectorStore:
    """FAISS-based vector store with Gemini embeddings and role-based filtering."""

    def __init__(self):
        self.documents = PAGANI_DOCUMENTS
        self.index: faiss.IndexFlatIP | None = None
        self.embeddings: np.ndarray | None = None
        self.dimension: int | None = None
        self._initialized = False

    def initialize(self):
        """Load from persistence or build fresh index."""
        if self._initialized:
            return

        if os.path.exists(INDEX_PATH) and os.path.exists(META_PATH):
            try:
                logger.info("Loading persisted FAISS index from disk...")
                self.index = faiss.read_index(INDEX_PATH)
                with open(META_PATH, "rb") as f:
                    meta = pickle.load(f)
                self.embeddings = meta["embeddings"]
                self.dimension = meta["dimension"]
                self.documents = meta["documents"]
                self._initialized = True
                logger.info(f"Loaded FAISS index: {self.index.ntotal} vectors, dim={self.dimension}")
                return
            except Exception as e:
                logger.warning(f"Failed to load persisted index, rebuilding: {e}")

        self._build_index()
        self._initialized = True

    def needs_pdf_ingestion(self) -> bool:
        """Check if PDFs have already been ingested into the documents."""
        if not self._initialized:
            # We can't know for sure without initializing, but if there's no persisted index,
            # we will build a fresh one from hardcoded docs, which means NO pdfs are in it.
            if not (os.path.exists(INDEX_PATH) and os.path.exists(META_PATH)):
                # If the PDF dataset folder isn't even present (e.g., on Render deployment),
                # do not attempt to ingest anything to save Gemini Quota and prevent crashes.
                pdf_dir = os.path.join(os.path.dirname(__file__), "..", "pagani_intelligence_rich_dataset_25_pdfs")
                if not os.path.exists(pdf_dir):
                    return False
                return True
            self.initialize()
            
        return not any(doc.get("is_pdf") for doc in self.documents)

    def ingest_pdf_chunks(self, chunks: list[dict]):
        """Add new PDF chunks to the vector store and rebuild the index."""
        if not chunks:
            return
            
        logger.info(f"Ingesting {len(chunks)} PDF chunks into vector store...")
        self.documents.extend(chunks)
        
        # We need to rebuild the entire index because adding to flat index dynamically
        # with new embeddings is possible, but _build_index() is cleaner and rebuilds embeddings
        # Wait, embedding everything every time is slow. Let's just embed the new chunks and add them.
        
        if self.embeddings is None or self.index is None:
            self._build_index()
        else:
            # Embed only the new chunks
            new_texts = [doc["content"] for doc in chunks]
            new_embeddings = self._embed_texts(new_texts)
            
            # Normalize new embeddings
            faiss.normalize_L2(new_embeddings)
            
            # Append to embeddings array
            self.embeddings = np.vstack((self.embeddings, new_embeddings))
            
            # Add to FAISS index
            self.index.add(new_embeddings)
            
            logger.info(f"FAISS index updated: {self.index.ntotal} vectors total")
            
            # Persist the updated state
            self._persist()

    def _embed_texts(self, texts: list[str]) -> np.ndarray:
        """Embed a list of texts using Gemini using batches to avoid rate limits."""
        all_embeddings = []
        batch_size = 20
        import time
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            try:
                logger.info(f"Embedding batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}...")
                result = genai.embed_content(
                    model=EMBEDDING_MODEL,
                    content=batch,
                    task_type="retrieval_document",
                )
                embeddings = np.array(result["embedding"], dtype=np.float32)
                if embeddings.ndim == 1:
                    embeddings = embeddings.reshape(1, -1)
                all_embeddings.append(embeddings)
                
                # Sleep to respect rate limits (e.g., Gemini Free Tier is 15 RPM)
                if i + batch_size < len(texts):
                    time.sleep(5)
            except Exception as e:
                logger.error(f"Embedding batch generation failed: {e}")
                # Try to sleep longer and retry once
                logger.info("Sleeping 30s and retrying batch...")
                time.sleep(30)
                try:
                    result = genai.embed_content(
                        model=EMBEDDING_MODEL,
                        content=batch,
                        task_type="retrieval_document",
                    )
                    embeddings = np.array(result["embedding"], dtype=np.float32)
                    if embeddings.ndim == 1:
                        embeddings = embeddings.reshape(1, -1)
                    all_embeddings.append(embeddings)
                except Exception as retry_e:
                    logger.error(f"Retry failed: {retry_e}")
                    raise RuntimeError(f"Failed to generate embeddings: {retry_e}")

        final_embeddings = np.vstack(all_embeddings) if all_embeddings else np.array([])
        logger.info(f"Embedded {len(texts)} total texts, shape: {final_embeddings.shape}")
        return final_embeddings

    def _embed_query(self, query: str) -> np.ndarray:
        """Embed a single query using Gemini text-embedding-004."""
        try:
            result = genai.embed_content(
                model=EMBEDDING_MODEL,
                content=query,
                task_type="retrieval_query",
            )
            embedding = np.array(result["embedding"], dtype=np.float32).reshape(1, -1)
            return embedding
        except Exception as e:
            logger.error(f"Query embedding failed: {e}")
            raise RuntimeError(f"Failed to embed query: {e}")

    def _build_index(self):
        """Build FAISS index from documents and persist to disk."""
        logger.info("Building FAISS index from scratch...")
        texts = [doc["content"] for doc in self.documents]
        self.embeddings = self._embed_texts(texts)

        # Dynamic dimension detection
        self.dimension = self.embeddings.shape[1]
        logger.info(f"Detected embedding dimension: {self.dimension}")

        # Normalize for cosine similarity
        faiss.normalize_L2(self.embeddings)

        # Build index
        self.index = faiss.IndexFlatIP(self.dimension)
        self.index.add(self.embeddings)
        logger.info(f"FAISS index built: {self.index.ntotal} vectors")

        # Persist
        self._persist()

    def _persist(self):
        """Save FAISS index and metadata to disk."""
        try:
            faiss.write_index(self.index, INDEX_PATH)
            with open(META_PATH, "wb") as f:
                pickle.dump({
                    "embeddings": self.embeddings,
                    "dimension": self.dimension,
                    "documents": self.documents,
                }, f)
            logger.info("FAISS index persisted to disk.")
        except Exception as e:
            logger.error(f"Failed to persist FAISS index: {e}")

    def _tokenize(self, text: str) -> list[str]:
        """Simple tokenizer for keyword search."""
        return [w.lower() for w in re.findall(r'\b\w+\b', text) if len(w) > 2]

    def _keyword_search(self, query: str, user_role: str, top_k: int) -> list[dict]:
        """Simple TF keyword search."""
        query_tokens = set(self._tokenize(query))
        if not query_tokens:
            return []
            
        results = []
        for i, doc in enumerate(self.documents):
            if user_role not in doc["role_access"]:
                continue
                
            doc_tokens = self._tokenize(doc["content"])
            # Calculate simple TF score based on token overlap
            score = 0
            for token in query_tokens:
                score += doc_tokens.count(token)
            
            if score > 0:
                results.append({"idx": i, "score": score, "doc": doc})
                
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _llm_rerank(self, query: str, candidates: list[dict], top_k: int) -> list[dict]:
        """Use Gemini to rerank candidates based on relevance to the query (0-100 score)."""
        if not candidates:
            return []
            
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            prompt = f"Given the user query: '{query}'\n\n"
            prompt += "Score each of the following document chunks on how accurately and completely it answers the query. "
            prompt += "Return a JSON array of objects, where each object has 'idx' (int) and 'relevance_score' (int from 0 to 100).\n\n"
            
            for i, cand in enumerate(candidates):
                content = cand['doc']['content'][:500].replace('\n', ' ')
                prompt += f"[Chunk {i}] Source: {cand['doc']['source']}\nContent: {content}...\n\n"
                
            response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            scores = json.loads(response.text)
            
            # Map scores back to candidates
            for cand, score_dict in zip(candidates, scores):
                cand['score'] = float(score_dict.get('relevance_score', 0))
                
            # Sort by new confidence score
            candidates.sort(key=lambda x: x['score'], reverse=True)
            return candidates[:top_k]
            
        except Exception as e:
            logger.error(f"LLM Reranking failed: {e}")
            # Fallback to RRF scores
            return candidates[:top_k]

    def search(self, query: str, top_k: int = 5, user_role: str = "viewer", filters: dict = None) -> list[dict]:
        """
        Semantic search with Gen-2 features: Role filtering, Metadata filters, and LLM Reranking.
        """
        if not self._initialized:
            self.initialize()
            
        search_k = min(20, self.index.ntotal)

        # --- 1. Semantic Search (FAISS) ---
        query_embedding = self._embed_query(query)
        faiss.normalize_L2(query_embedding)

        # Search more than top_k to allow for filtering
        search_k = min(top_k * 3, self.index.ntotal)
        scores, indices = self.index.search(query_embedding, search_k)

        semantic_results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            doc = self.documents[idx]
            
            # 1a. Filter by Role
            if user_role not in doc["role_access"]:
                continue
                
            # 1b. Filter by Metadata (if any)
            if filters:
                match = True
                for k, v in filters.items():
                    # Check if 'Zonda' is in source file name, for example
                    if k == "model" and v.lower() not in doc["source"].lower():
                        match = False
                if not match:
                    continue

            semantic_results.append({"idx": idx, "score": float(score), "doc": doc})

        # --- 2. Keyword Search ---
        keyword_results = self._keyword_search(query, user_role, search_k)
        
        # --- 3. Reciprocal Rank Fusion (RRF) ---
        # k = 60 is standard in RRF
        rrf_k = 60
        fused_scores = {}
        
        # Rank semantic results
        for rank, res in enumerate(semantic_results):
            fused_scores[res["idx"]] = fused_scores.get(res["idx"], 0) + 1.0 / (rrf_k + rank + 1)
            
        # Rank keyword results
        for rank, res in enumerate(keyword_results):
            fused_scores[res["idx"]] = fused_scores.get(res["idx"], 0) + 1.0 / (rrf_k + rank + 1)
            
        # Sort by fused score
        fused_results = sorted(list(fused_scores.items()), key=lambda x: x[1], reverse=True)
        
        # Build candidate list for reranking
        candidates = []
        for idx, _ in fused_results[:search_k]:
            candidates.append({"idx": idx, "doc": self.documents[idx], "score": 0.0})
            
        # --- 4. LLM Cross-Encoder Reranking ---
        reranked_results = self._llm_rerank(query, candidates, top_k=top_k)

        # Build final returning list
        final_results = []
        for res in reranked_results:
            doc = res["doc"]
            final_results.append({
                "content": doc["content"],
                "source": doc["source"],
                "score": res["score"],  # This is now an LLM confidence score (0-100)
            })

        logger.info(
            f"Gen-2 Hybrid search query='{query[:50]}...' role={user_role} "
            f"returned {len(final_results)} reranked results"
        )
        return final_results

    def search_with_debug(self, query: str, top_k: int = 5, user_role: str = "viewer", filters: dict = None) -> dict:
        """
        Debug-enhanced search that returns results + full pipeline trace.
        Does NOT modify the core search logic — wraps the same calls with timing.
        """
        import time as _time

        debug_info = {
            "pipeline_steps": [],
            "search_results": [],
            "retrieved_chunks": [],
            "timing": {},
            "router_decision": None,
        }

        t_start = _time.time()

        # Step 1: Embed query
        debug_info["pipeline_steps"].append({
            "step": "query_received", "label": "Query Received",
            "timestamp_ms": 0
        })

        t_embed = _time.time()
        if not self._initialized:
            self.initialize()

        query_embedding = self._embed_query(query)
        faiss.normalize_L2(query_embedding)
        embed_ms = int((_time.time() - t_embed) * 1000)

        debug_info["pipeline_steps"].append({
            "step": "query_embedded", "label": "Query Embedded",
            "timestamp_ms": int((_time.time() - t_start) * 1000)
        })
        debug_info["timing"]["embedding_ms"] = embed_ms

        # Step 2: FAISS + keyword search
        t_search = _time.time()
        search_k = min(top_k * 3, self.index.ntotal)
        scores, indices = self.index.search(query_embedding, search_k)

        semantic_results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            doc = self.documents[idx]
            if user_role not in doc["role_access"]:
                continue
            if filters:
                match = True
                for k, v in filters.items():
                    if k == "model" and v.lower() not in doc["source"].lower():
                        match = False
                if not match:
                    continue
            semantic_results.append({"idx": idx, "score": float(score), "doc": doc})

        keyword_results = self._keyword_search(query, user_role, search_k)
        search_ms = int((_time.time() - t_search) * 1000)

        debug_info["pipeline_steps"].append({
            "step": "vector_search", "label": "Vector Search Performed",
            "timestamp_ms": int((_time.time() - t_start) * 1000)
        })
        debug_info["timing"]["search_ms"] = search_ms

        # Collect raw search results for debug display
        for res in semantic_results[:10]:
            debug_info["search_results"].append({
                "source": res["doc"]["source"],
                "similarity": round(res["score"], 4),
                "chunk_preview": res["doc"]["content"][:150].replace("\n", " ")
            })

        # Step 3: RRF fusion
        rrf_k = 60
        fused_scores = {}
        for rank, res in enumerate(semantic_results):
            fused_scores[res["idx"]] = fused_scores.get(res["idx"], 0) + 1.0 / (rrf_k + rank + 1)
        for rank, res in enumerate(keyword_results):
            fused_scores[res["idx"]] = fused_scores.get(res["idx"], 0) + 1.0 / (rrf_k + rank + 1)

        fused_results = sorted(list(fused_scores.items()), key=lambda x: x[1], reverse=True)
        candidates = []
        for idx, _ in fused_results[:search_k]:
            candidates.append({"idx": idx, "doc": self.documents[idx], "score": 0.0})

        # Step 4: LLM reranking
        t_rerank = _time.time()
        reranked_results = self._llm_rerank(query, candidates, top_k=top_k)
        rerank_ms = int((_time.time() - t_rerank) * 1000)

        debug_info["pipeline_steps"].append({
            "step": "reranking", "label": "LLM Reranking",
            "timestamp_ms": int((_time.time() - t_start) * 1000)
        })
        debug_info["timing"]["reranking_ms"] = rerank_ms

        # Build final results + debug chunks
        final_results = []
        for res in reranked_results:
            doc = res["doc"]
            final_results.append({
                "content": doc["content"],
                "source": doc["source"],
                "score": res["score"],
            })
            debug_info["retrieved_chunks"].append({
                "source": doc["source"],
                "content": doc["content"][:600],
                "relevance_score": res["score"],
            })

        debug_info["pipeline_steps"].append({
            "step": "context_built", "label": "Context Constructed",
            "timestamp_ms": int((_time.time() - t_start) * 1000)
        })

        return {"results": final_results, "debug": debug_info, "_t_start": t_start}


# Singleton instance
vector_store = VectorStore()