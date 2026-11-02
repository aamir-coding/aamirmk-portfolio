# Phase 2 Study Guide: Curated Knowledge Base, In-Process Hybrid RAG & Retrieval Evaluations

> **Purpose**: This guide provides the complete theoretical foundation, architectural rationale, line-by-line code connections, and placement interview preparation for everything built in Phase 2 (`phase-2-rag`). Use this document for technical revision and AI/backend engineering interviews.

---

## 1. Core Engineering Concepts & "Why"

### 1.1 The RAG Paradigm vs. Context Stuffing
In Phase 1, the assistant stuffed Aamir's entire plain-text résumé into the system prompt (`~1,380` tokens per request). While functional for a tiny MVP, context stuffing suffers from four severe production limitations:

1. **Token Bloat & Cost/Quota Drain**: Every user prompt incurs the full static context token overhead. On Groq's free tier (8,000 TPM / 200,000 TPD), stuffing 1,400 tokens per request caps the system at only ~5 requests per minute before throttling.
2. **Context Dilution & "Lost in the Middle"**: LLMs exhibit U-shaped attention curves (Liu et al., 2023). Facts placed in the middle of long static prompts suffer degraded retrieval attention compared to facts near the beginning or end.
3. **No Granular Source Attribution**: When the entire résumé is bundled into a single block, the model cannot cite precise sections, projects, or documents.
4. **Boundary & Privacy Leakage**: Context stuffing makes it impossible to cleanly separate public indexed knowledge from sensitive operational policies (such as salary deflections, unverified metric warnings, or the recruiter phone-sharing guardrail).

**Retrieval-Augmented Generation (RAG)** replaces static stuffing with dynamic, query-time context assembly:
1. Curate verified knowledge into granular, structured `FactChunk` documents.
2. At request time, index facts and retrieve only the top $k$ most relevant chunks ($k=4$).
3. Dynamically inject the retrieved chunks into a templated `{retrieved_context}` slot inside the system prompt.
4. The LLM answers strictly grounded in the retrieved facts and cites their source tags.

---

### 1.2 Chunking Strategy & Frontmatter Schema
Naïve RAG systems split text by arbitrary token or character counts (e.g., 500 characters with 50-character overlap). For technical portfolios, arbitrary sliding windows frequently slice code identifiers, split cause-and-effect debugging narratives mid-sentence, or divorce metrics from their caveats.

Instead, we designed a **domain-aligned semantic chunking strategy** stored as Markdown with YAML frontmatter (`---`) and YAML matrices:

```
backend/app/data/facts/
├── profile.yaml             # Identity, location, links, contact
├── education.md             # Degree, CGPA 9.77, coursework, top-10 ranking
├── experience/
│   └── algouniversity.md    # Role, built systems, cloud arch, Redis bug, concurrency
├── projects/
│   ├── entropy-oj.md        # Pitch, stack, design, 3 AI features, security, debug
│   ├── health-tracker.md    # Architecture, CI/CD, deployment status
│   ├── health-premium-predictor.md # XGBoost, Streamlit, R² 0.99 caveats
│   ├── ai-digital-assistant.md     # Architecture, RAG design, eval metrics
│   ├── secure-auction.md    # Django, PostgreSQL, ACID transactions
│   ├── browser-games.md     # Vanilla JS, HTML5 Canvas experiments
│   ├── keynone.md           # Voice dictation open-source contributions
│   └── vayusetu.md          # Google Cloud Hackathon 2nd Runner-Up
├── skills.yaml              # Skills matrix with honest levels & evidence
├── hr_answers.md            # ~30 behavioral Q&As in Aamir's voice
├── opinions.md              # 8 technical takes (FastAPI, RAG vs fine-tuning, etc.)
├── achievements.md          # Graph contest, Hackathon, CGPA
├── personal.md              # Background, hobbies, working values
└── boundaries.md            # Deflection policies (marked indexed: false, private: true)
```

#### Chunk Model (`FactChunk`):
- `id`: Globally unique identifier (e.g. `exp-algouniversity-hardest-bug`, `proj-entropy-oj-stack`).
- `type`: Category (`profile`, `education`, `experience`, `project`, `skill`, `hr`, `opinion`, `achievement`, `personal`, `boundary`).
- `title`: Human-readable summary heading.
- `source_section`: Exact section mapping back to the questionnaire (e.g. `X7, X8, J8`).
- `tags`: Semantic keywords for lexical and dense discovery.
- `draft`: Boolean flag indicating whether the fact is pending user verification.
- `private`: Boolean flag ensuring private policies (e.g. `boundaries.md`) are excluded from the public retrieval index.

---

### 1.3 Lexical Search: Okapi BM25 with Compound Tokenization

While vector search excels at conceptual similarities, it frequently fails at exact technical jargon. If a recruiter asks:
> *"How did Aamir fix the Redis ETIMEDOUT bug?"*

A pure dense vector model may retrieve general networking concepts or generic Redis definitions. An exact lexical index ensures that documents containing the exact tokens `ETIMEDOUT`, `BullMQ`, `Monaco Editor`, or `9.77` receive strong matching weight.

We implemented in-house **Okapi BM25** without heavy external dependencies.

#### Mathematical Formulation:
For a query $q$ containing terms $t_1, \dots, t_m$ and document $d$:

$$\text{Score}_{\text{BM25}}(q, d) = \sum_{i=1}^{m} \text{IDF}(t_i) \cdot \frac{f(t_i, d) \cdot (k_1 + 1)}{f(t_i, d) + k_1 \cdot \left(1 - b + b \cdot \frac{|d|}{\text{avgdl}}\right)}$$

Where:
- $f(t_i, d)$ is the term frequency of $t_i$ in document $d$.
- $|d|$ is document length in tokens, and $\text{avgdl}$ is average document length across the corpus.
- $k_1 = 1.5$: Term frequency saturation parameter. Controls how quickly repeated occurrences of a word reach diminishing returns.
- $b = 0.75$: Document length normalization parameter. Penalizes overly long documents to prevent verbose files from dominating results.

#### Non-Negative Robertson-Spärck Jones IDF:
Standard Robertson-Spärck Jones IDF is:

$$\text{IDF}(t) = \ln \left( \frac{N - n(t) + 0.5}{n(t) + 0.5} \right)$$

If a term appears in more than half of the corpus documents ($n(t) > N/2$), this formula yields a negative score, actively penalizing matching documents! To prevent this in a small, specialized corpus, we use the proven non-negative floored variant:

$$\text{IDF}(t) = \ln \left( \frac{N - n(t) + 0.5}{n(t) + 0.5} + 1.0 \right)$$

This guarantees $\text{IDF}(t) \ge 0$ for all terms, smoothly tapering common words (like "Aamir") to zero weight without negative penalties.

#### Specialized Technical Tokenization:
Standard regex tokenizers (`\w+`) destroy programming symbols, splitting `C++17` into `["C", "17"]`, `Node.js` into `["Node", "js"]`, and `9.77` into `["9", "77"]`.
Our tokenizer uses compound preservation rules:

```python
# Preserves compounds like 'c++17', 'c++', 'node.js', 'full-stack', '9.77'
COMPOUND_PATTERN = re.compile(
    r"[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)+|[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)+|[a-zA-Z0-9]+\+\+[0-9]*|[a-zA-Z0-9]+"
)
```
The tokenizer emits both the compound identifier (`node.js`) and its constituent sub-tokens (`node`, `js`), enabling both exact compound matches and partial keyword hits.

---

### 1.4 Dense Semantic Search: ONNX FastEmbed Runtime & Vector Geometry

Dense retrieval maps queries and documents into a continuous semantic vector space $\mathbb{R}^{384}$. Queries and documents with similar meanings align closely in cosine distance even when they share zero overlapping words (e.g. "college grades" $\leftrightarrow$ "CGPA 9.77").

```
                                    Dense Vector Space (384 Dimensions)
                                    ────────────────────────────────────
       "What did Aamir study?" ───► [ 0.12, -0.45,  0.88, ... ]
                                          │
                         Cosine Distance  │  θ ≈ 14° (cos θ = 0.97)
                                          ▼
   "Bachelor of Technology in CSE" ──► [ 0.14, -0.42,  0.89, ... ]
```

#### Why `fastembed` ONNX instead of PyTorch / SentenceTransformers?
- **The Memory Problem**: PyTorch + Hugging Face `transformers` requires `~800 MB – 1.5 GB` of RAM just to initialize the Python C-extensions and CUDA/CPU runtime. On Render's free tier with a strict **512 MB RAM limit**, a PyTorch backend will trigger an immediate Out-Of-Memory (OOM) kill (`SIGKILL 137`).
- **The ONNX Solution**: `fastembed` uses the Microsoft ONNX Runtime C++ engine directly.
  - Model: `BAAI/bge-small-en-v1.5` (~33M parameters, ~130 MB on disk).
  - RAM Overhead: Only ~123 MB during model load, and ~26 MB for the entire 75-document embedding matrix.
  - Total process memory: **227.75 MB** (under 50% of the 512 MB cap, leaving >284 MB of headroom).
  - CPU Inference Speed: Single-query embedding takes **~6.8 ms** on standard CPU.

#### Vector Normalization & Cosine Similarity:
Vectors $\mathbf{u}, \mathbf{v} \in \mathbb{R}^d$ are $L_2$-normalized upon creation:

$$\hat{\mathbf{v}} = \frac{\mathbf{v}}{\max(\|\mathbf{v}\|_2, 10^{-9})}, \quad \text{where } \|\mathbf{v}\|_2 = \sqrt{\sum_{i=1}^{d} v_i^2}$$

Because all document vectors are pre-normalized, the cosine similarity simplifies from:

$$\text{sim}(\mathbf{q}, \mathbf{d}) = \frac{\mathbf{q} \cdot \mathbf{d}}{\|\mathbf{q}\|_2 \|\mathbf{d}\|_2} \implies \hat{\mathbf{q}} \cdot \hat{\mathbf{d}} = \sum_{i=1}^{d} \hat{q}_i \hat{d}_i$$

Querying 75 documents reduces to a single, lightning-fast BLAS matrix-vector dot product in NumPy: `scores = np.dot(matrix, query_vector)`.

---

### 1.5 Reciprocal Rank Fusion (RRF)

A classic challenge in hybrid retrieval is **score calibration**:
- BM25 scores are unbounded positive real numbers ($\text{score} \in [0, \infty)$), highly sensitive to document length and query length.
- Dense cosine similarities are bounded between $[-1.0, 1.0]$ (typically $[0.5, 0.9]$ for language models).

Naïvely combining them via weighted linear combination ($\alpha S_{\text{dense}} + (1-\alpha) S_{\text{BM25}}$) requires artificial min-max normalization, which breaks whenever an outlier document or rare keyword produces a massive BM25 spike.

We solve this using **Cormack's Reciprocal Rank Fusion (RRF)** (*Cormack et al., SIGIR 2009*). RRF discards raw scores entirely and operates purely on the **ordinal ranks** assigned by each retrieval method:

$$RRF\_score(d) = \sum_{m \in \{\text{BM25}, \text{Dense}\}} \frac{1}{k + \text{rank}_m(d)}$$

Where:
- $\text{rank}_m(d)$ is the 1-based rank of document $d$ in system $m$.
- $k = 60$: The smoothing constant empirically validated by Cormack et al. It prevents top-ranked documents from completely dominating and stabilizes rank distributions.

#### Why RRF Excels:
1. **Scale-Invariant**: Requires zero normalization, scaling parameters, or cross-validation tuning.
2. **Overlap Boost**: A document appearing at rank 3 in BM25 and rank 7 in Dense receives:
   $$\frac{1}{60 + 3} + \frac{1}{60 + 7} = 0.01587 + 0.01492 = 0.03079$$
   This naturally outranks a document appearing only in BM25 at rank 1 ($1/(60+1) = 0.01639$). RRF strongly favors consensus between keyword precision and semantic intent.
3. **Deep Candidate Pool**: `HybridRetriever` fetches a candidate pool of $4 \times \text{top\_k}$ (minimum 20) candidates from both BM25 and Dense before fusion, ensuring rich intersection.

---

### 1.6 Architectural Protocol Seam & Async Event Loop Offloading

Following *codebase-design* principles, we built a **deep module with a narrow interface**:

```
┌────────────────────────────────────────────────────────┐
│            FastAPI Endpoints (/chat, /chat/stream)     │
└───────────────────────────┬────────────────────────────┘
                            │ Depends(get_retriever)
                            ▼
┌────────────────────────────────────────────────────────┐
│               Retriever (Protocol Seam)                │
│       async def retrieve(query, top_k) -> list         │
└───────────────┬────────────────────────┬───────────────┘
                │                        │
         Production                      Test
                ▼                        ▼
┌───────────────────────────────┐ ┌──────────────────────┐
│        HybridRetriever        │ │    FakeRetriever     │
│  - BM25Index                  │ │  - In-memory static  │
│  - DenseIndex (FastEmbed ONNX)│ │  - Instant (0.01ms)  │
│  - Reciprocal Rank Fusion     │ │  - Deterministic     │
│  - asyncio.to_thread()        │ │  - Zero ONNX loads   │
└───────────────────────────────┘ └──────────────────────┘
```

#### Event-Loop Protection via `asyncio.to_thread`:
FastAPI runs on a single-threaded `asyncio` event loop. Both BM25 tokenization and ONNX embedding matrix multiplication are CPU-bound operations. If executed directly inside `async def retrieve()`, they would block the main thread for 10ms, preventing incoming SSE packets or health checks from progressing.

`HybridRetriever` wraps the synchronous search in `asyncio.to_thread`:
```python
async def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
    return await asyncio.to_thread(self._sync_retrieve, query, top_k)
```
The CPU-bound work runs in a background worker thread from Python's standard `ThreadPoolExecutor`, immediately yielding control back to the event loop.

---

## 2. Line-by-Line Codebase Connections

### 2.1 Pydantic Fact Models
📁 [`backend/app/retrieval/models.py`](file:///d:/AI_Engineer/aamirmkh-portfolio/backend/app/retrieval/models.py)
- `FactChunk`: Frozen Pydantic model (`frozen=True`) representing an immutable knowledge atom. Contains `id`, `type`, `title`, `source_section`, `tags`, `content`, `draft`, and `private`.
- `RetrievedChunk`: Pairs a `FactChunk` with its runtime `score: float`, `rank: int`, and `retrieval_method: str` (`"hybrid_rrf"`, `"bm25"`, `"dense"`).

### 2.2 Fact Loader & Parser
📁 [`backend/app/retrieval/loader.py`](file:///d:/AI_Engineer/aamirmkh-portfolio/backend/app/retrieval/loader.py)
- `FactLoader.load_all()`: Scans `backend/app/data/facts/` recursively.
- Splits multi-chunk Markdown files by `---` delimiters.
- Extracts YAML frontmatter via `yaml.safe_load`.
- Filters out chunks where `private=True` or `draft=True` when indexing for public retrieval.
- Detects and raises `ValueError` on duplicate chunk IDs.

### 2.3 Okapi BM25 Index
📁 [`backend/app/retrieval/bm25.py`](file:///d:/AI_Engineer/aamirmkh-portfolio/backend/app/retrieval/bm25.py)
- `tokenize(text)`: Lowercases, extracts compounds (`node.js`, `c++17`, `9.77`) and sub-tokens.
- `BM25Index.__init__()`: Computes document frequencies $\text{df}(t)$, average document length $\text{avgdl}$, and inverted index frequencies.
- `BM25Index.search(query, top_k)`: Implements floored Robertson-Spärck Jones IDF and length-normalized term frequency scoring.

### 2.4 Dense Semantic Index
📁 [`backend/app/retrieval/dense.py`](file:///d:/AI_Engineer/aamirmkh-portfolio/backend/app/retrieval/dense.py)
- `DenseIndex._get_model()`: Lazy-loads `fastembed.TextEmbedding("BAAI/bge-small-en-v1.5")`.
- `DenseIndex.index(chunks)`: Embeds `f"{chunk.title} {' '.join(chunk.tags)} {chunk.content}"` into a 2D float32 NumPy array and applies $L_2$-normalization.
- `DenseIndex.search(query, top_k)`: Normalizes query embedding and performs `np.dot(matrix, query_vec)` for cosine similarities.

### 2.5 Hybrid Fusion & Retriever Protocol
📁 [`backend/app/retrieval/hybrid.py`](file:///d:/AI_Engineer/aamirmkh-portfolio/backend/app/retrieval/hybrid.py)
- `reciprocal_rank_fusion(ranked_lists, rrf_k=60)`: Aggregates $1 / (k + \text{rank})$ across methods and re-ranks results.
- `HybridRetriever._sync_retrieve(query, top_k)`: Dispatches to BM25 and Dense with `candidate_k = max(top_k * 4, 20)` and fuses via RRF.
- `HybridRetriever.retrieve()`: Wraps sync search in `asyncio.to_thread`.

📁 [`backend/app/retrieval/retriever.py`](file:///d:/AI_Engineer/aamirmkh-portfolio/backend/app/retrieval/retriever.py)
- `@runtime_checkable class Retriever(Protocol)`: Defines `async def retrieve(query: str, top_k: int = 5) -> list[RetrievedChunk]`.
- `FakeRetriever`: Deterministic in-memory fake with canned results and call recording.
- `get_retriever()` / `set_retriever()`: FastAPI dependency injection provider.

### 2.6 Chat Endpoint Augmentation
📁 [`backend/app/prompt_loader.py`](file:///d:/AI_Engineer/aamirmkh-portfolio/backend/app/prompt_loader.py)
- `format_retrieved_context(chunks)`: Serializes retrieved chunks into Markdown blocks with Source tags, Section IDs, and Titles.
- `build_system_prompt(chunks)`: Injects formatted context into `{retrieved_context}` slot in `system.txt`.

📁 [`backend/app/api/chat.py`](file:///d:/AI_Engineer/aamirmkh-portfolio/backend/app/api/chat.py)
- Injects `retriever: Retriever = Depends(get_retriever)`.
- Calls `await retriever.retrieve(request.message, top_k=4)`.
- Passes dynamically constructed system prompt to `LLMClient.complete()` or `LLMClient.stream()`.

### 2.7 Automated Retrieval Evals & Latency Benchmarks
📁 [`evals/test_retrieval.py`](file:///d:/AI_Engineer/aamirmkh-portfolio/evals/test_retrieval.py)
- Parameterized over 45 labeled queries from `evals/seed_questions.yaml`.
- Measures and asserts Hit Rate@5, MRR, CPU latency distribution, and adversarial ground truth corrections.

---

## 3. Placement & SDE Interview Preparation Q&A

### Q1: Why did you build a hybrid retriever (BM25 + Dense) rather than relying solely on vector embeddings?
**Answer**:
Vector embeddings capture semantic similarity in continuous vector space, but they frequently struggle with **exact keyword precision** on specialized technical identifiers. For example, if a recruiter asks: *"What was the Redis ETIMEDOUT bug?"* or *"What is Aamir's CGPA?"*, dense models might match general Redis tutorials or general academic discussions.

Okapi BM25 provides exact keyword recall by computing Robertson-Spärck Jones Inverse Document Frequency (IDF) and term frequency saturation. By combining BM25 with `BAAI/bge-small-en-v1.5` embeddings via Reciprocal Rank Fusion (RRF), our system gets the best of both worlds: BM25 guarantees that rare technical tokens (`ETIMEDOUT`, `BullMQ`, `Monaco Editor`, `9.77`) are immediately retrieved, while Dense embeddings resolve synonymous or conceptual inquiries (*"Where did Aamir intern?"* $\leftrightarrow$ *"AlgoUniversity SDE Extern"*). On our 45-query evaluation benchmark, this hybrid approach achieved **100.0% Hit Rate@5** and **0.8778 MRR**.

---

### Q2: What is Reciprocal Rank Fusion (RRF) and why did you choose it over weighted linear score combination?
**Answer**:
Weighted linear score combination ($\text{Score} = \alpha S_{\text{dense}} + (1-\alpha) S_{\text{BM25}}$) requires both score distributions to be calibrated to the same scale. However, BM25 scores are unbounded $[0, \infty)$ and heavily influenced by document length, while cosine similarities are bounded $[-1, 1]$ (typically $[0.6, 0.9]$ for text embeddings). Attempting to normalize BM25 via min-max scaling is brittle: a single document with multiple keyword matches creates an extreme outlier that compresses all other BM25 scores to near-zero.

Reciprocal Rank Fusion (*Cormack et al., 2009*) solves this by ignoring raw scores entirely and operating purely on **ordinal ranks**:
$$RRF\_score(d) = \sum_{m} \frac{1}{k + \text{rank}_m(d)}$$
With smoothing constant $k=60$:
1. It is **scale-invariant**: no score normalization or distribution assumptions are required.
2. It naturally rewards **cross-method consensus**: a document appearing at rank 2 in BM25 and rank 6 in Dense gets $\frac{1}{62} + \frac{1}{66} \approx 0.0312$, outranking a document that is rank 1 in only one method ($\frac{1}{61} \approx 0.0164$).
3. It has zero hyperparameters to tune at runtime.

---

### Q3: How did you run in-process vector embeddings inside Render's 512 MB RAM free-tier limit without triggering OOM kills?
**Answer**:
Standard Python embedding stacks (PyTorch + Hugging Face `transformers` or `sentence-transformers`) load massive CUDA/C++ runtimes and PyTorch tensor overhead, consuming between 800 MB and 1.5 GB of RAM at idle. In Render's 512 MB container, this triggers an immediate Linux kernel Out-Of-Memory kill (`SIGKILL 137`).

We engineered around this by using **FastEmbed with Microsoft ONNX Runtime**:
1. FastEmbed uses the C++ ONNX Runtime directly without PyTorch or Transformers dependencies.
2. We selected `BAAI/bge-small-en-v1.5` (384 dimensions, ~33M parameters), which is only ~130 MB on disk.
3. We executed a strict **Memory Gate**:
   - Baseline backend imports: 77.27 MB
   - Model loaded into memory: 200.82 MB (+123.55 MB)
   - All 75 knowledge chunks embedded and indexed: 227.75 MB (+26.93 MB, the 75x384 float32 matrix is only 111 KB).
4. Total WorkingSet is **227.75 MB**, which is under 45% of Render's 512 MB limit, leaving over 284 MB of headroom for FastAPI request handling and garbage collection.

---

### Q4: In an asynchronous framework like FastAPI/ASGI, how do you prevent CPU-bound retrieval from blocking the event loop?
**Answer**:
FastAPI executes request handlers on a single-threaded `asyncio` event loop. While I/O operations (like waiting for Groq API network packets) yield control via `await`, CPU-bound computations (such as tokenizing strings with regex, calculating BM25 term frequencies, and running ONNX model inference) do NOT yield control. If executed directly on the event loop, they would block the main thread for 10ms, freezing all concurrent requests, health checks, and SSE streams.

To prevent event-loop starvation, our `HybridRetriever` implements the `async def retrieve()` seam by offloading the synchronous search to a thread pool via `asyncio.to_thread`:
```python
async def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
    return await asyncio.to_thread(self._sync_retrieve, query, top_k)
```
`asyncio.to_thread` delegates the CPU execution to Python's default `concurrent.futures.ThreadPoolExecutor`. The event loop yields immediately, remains fully responsive to other requests, and resumes the coroutine as soon as the worker thread finishes.

---

### Q5: How do you mathematically evaluate retrieval quality? What are Hit Rate@k and Mean Reciprocal Rank (MRR)?
**Answer**:
We measure retrieval quality using two standard Information Retrieval metrics across our 45 labeled test queries in `evals/seed_questions.yaml`:

1. **Hit Rate@k**: Measures the proportion of queries where at least one ground-truth expected chunk appears in the top $k$ retrieved results:
   $$\text{Hit Rate@k} = \frac{1}{Q} \sum_{q=1}^{Q} \mathbb{I}(\text{rank}(q) \le k)$$
   Where $\mathbb{I}$ is the indicator function. On our test set with $k=5$, our system achieved **45/45 = 100.0%** (target was $\ge 90\%$).

2. **Mean Reciprocal Rank (MRR)**: Evaluates where the *first* correct chunk appears in the ranked results, penalizing systems that place relevant documents further down the list:
   $$\text{MRR} = \frac{1}{Q} \sum_{q=1}^{Q} \frac{1}{\text{rank}_1(q)}$$
   - If the first relevant document is at rank 1, reciprocal rank is $1/1 = 1.0$.
   - If at rank 2, it is $1/2 = 0.5$.
   - If not in top $k$, it is $0.0$.
   Our system achieved an MRR of **0.8778** (target was $\ge 0.80$), proving that relevant context is placed at rank 1 or 2 in the overwhelming majority of inquiries.

---

### Q6: How does the retrieval architecture prevent hallucinating or leaking unverified/sensitive information?
**Answer**:
We enforce strict **Boundary and Grounding Controls**:
1. **Private vs. Public Chunk Segregation**: Boundary policies (`boundaries.md`) are tagged `private: true` and `indexed: false`. The `FactLoader` strips them during index building, ensuring private policies (e.g., salary deflection rules, private contact data) can never be retrieved or quoted out of context.
2. **Explicit Abstention and Premise Correction**: For adversarial questions (e.g., *"Did Aamir reduce API latency by 35%?"* or *"Aamir worked at Google, correct?"*), our knowledge base contains explicit clarification chunks (`exp-algouniversity-hardest-bug`, `skill-not-claimed`). The retriever pulls these chunks, allowing the assistant to cite them and directly correct the false premise.
3. **Role-Based Contact Disclosure (B1 Policy)**: Aamir's phone number is withheld by default. However, when a recruiter explicitly requests contact to schedule a professional call or WhatsApp message (`eval-39`), the retriever returns `profile-contact` at rank 1, allowing the assistant to provide the verified phone number while refusing home address disclosure.
4. **Draft Item Auditing**: All unverified metrics and placeholders are tracked in `docs/knowledge-todo.md` and excluded from production claims.

---

## 4. Key Metrics Summary (Phase 2 Done)

| Metric | Target | Actual Measured Output | Status |
|---|---|---|---|
| **Hit Rate@5** | $\ge 90.0\%$ | **100.00%** (45/45 queries) | ✅ Passed |
| **MRR (Mean Reciprocal Rank)** | $\ge 0.8000$ | **0.8778** | ✅ Passed |
| **Retrieval Latency (Mean)** | $< 25.0$ ms | **9.39 ms** on CPU (p95: 11.01 ms) | ✅ Passed |
| **Memory Footprint (WorkingSet)**| $< 512$ MB | **227.75 MB** (>284 MB headroom) | ✅ Passed |
| **Automated Test Suite** | 100% green | **175 tests passed** (127 backend + 48 evals) | ✅ Passed |
| **Ruff Linter & Formatter** | Clean | **0 errors, 0 warnings** | ✅ Clean |

---

## 5. Official References & Further Reading

- **Okapi BM25 & Robertson-Spärck Jones IDF**:
  - Robertson, S. E., & Zaragoza, H. (2009). *The Probabilistic Relevance Framework: BM25 and Beyond*. Foundations and Trends in Information Retrieval.
  - Spärck Jones, K. (1972). *A statistical interpretation of term specificity and its application in retrieval*. Journal of Documentation.
- **Reciprocal Rank Fusion**:
  - Cormack, G. V., Clarke, C. L., & Buettcher, S. (2009). *Reciprocal rank fusion outperforms out-of-the-box methods for information retrieval*. SIGIR '09.
- **FastEmbed & BGE Embeddings**:
  - Qdrant FastEmbed Documentation: [https://github.com/qdrant/fastembed](https://github.com/qdrant/fastembed)
  - Xiao et al. (2023). *C-Pack: Packaged Resources to Advance General Chinese and English Embedding*. BAAI BGE Models.
- **Codebase Architecture & Clean Seams**:
  - Ousterhout, John. (2018). *A Philosophy of Software Design*. Yaknyam Press.
  - Feathers, Michael. (2004). *Working Effectively with Legacy Code*. Prentice Hall.
