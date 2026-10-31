# CodeQuery
> **A Retrieval-Augmented AI Assistant for Codebase Understanding**  
> *Final Year Major Project*

CodeQuery is a structure-aware Retrieval-Augmented Generation (RAG) assistant that allows developers to point the system at any public code repository and ask natural-language questions, receiving accurate answers grounded in and cited from actual source code with exact file and line references.

---

## 🌟 Key Features & Architecture

### 1. Structure-Aware AST Parsing (`app/services/code_parser.py`)
- Splits source files along logical structural boundaries (functions, classes, methods) rather than naive fixed-size text windows.
- Preserves metadata including file paths, start and end line numbers, argument lists, and docstrings.
- **Speed Optimization**: High-throughput parallel AST parsing using `ThreadPoolExecutor` across CPU cores.

### 2. Structural Relationship Graph with NetworkX (`app/services/graph_service.py`)
- Directed relationship graph (`nx.DiGraph`) capturing:
  - **Function Calls**: Caller -> Callee (`CALLS` with call site lines).
  - **Class Hierarchies**: Subclass -> Base Class (`INHERITS_FROM`).
  - **Containment**: Module -> Class/Function, Class -> Method (`CONTAINS`).
  - **Import Dependencies**: Module -> Imported Module/Symbol (`IMPORTS`).
- Serialized to fast JSON node-link format in `backend/data/graphs/<repo>.json` with zero-overhead in-memory LRU caching.

### 3. High-Speed Vector Embedding & Partitioned Storage (`app/services/embedding_service.py`, `app/services/vector_store.py`)
- In-process ONNX Runtime embeddings using `FastEmbed` (`BAAI/bge-small-en-v1.5`) generating over **200+ code chunks/second** on CPU.
- Persistent ChromaDB storage partitioned by repository with batch upserts.

### 4. Query-Time Retrieval & Structural Graph Expansion (`app/services/rag_service.py`)
- **Semantic Retrieval**: Queries vector store for the top most relevant code chunks.
- **Graph Expansion**: Dynamically expands context using 1-hop / 2-hop graph traversal to locate caller functions, callees, and parent class definitions.
- **Grounded Answer Generation**: Strictly requires the LLM to ground answers in the code and cite exact file and line numbers: `[path/file.py:start-end]`.
- **Automated Citation Parser**: Extracts cited source ranges and provides verified code snippet previews.

### 5. Multi-Provider LLM Engine (`app/services/llm_service.py`)
- Supports **Anthropic Claude API** (as specified in Synopsis), **Google Gemini API**, and local **Ollama** (`qwen2.5-coder:1.5b` / `qwen2.5-coder:3b`).
- **Speed Optimizations**: Tuned multi-threading options (`num_thread`), token generation limits, and instant in-memory LRU query cache (repeat queries execute in **< 1ms**).

### 6. Interactive React Frontend (`frontend/src/App.jsx`)
- Modern dark-mode interface with gradient accents.
- **Q&A Chat Assistant**: Conversational thread with suggested queries, markdown formatting, and clickable citation pills.
- **Code & Citation Inspector Modal**: Click any citation to view the exact source file with highlighted line numbers.
- **Structural Graph Visualizer**: Explore repository symbols, callers, callees, and inheritance trees.
- **Repository Ingestion & Indexer**: Ingest any public GitHub URL or local repo with real-time indexing metrics.
- **System Evaluation Suite**: Live execution of the Objective 5 evaluation benchmark.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- (Optional for offline local LLM) [Ollama](https://ollama.com/) with `qwen2.5-coder:1.5b`

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
# Windows:
..\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```
API Documentation will be available at: `http://127.0.0.1:8000/docs`

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install node modules
npm install

# Start Vite dev server
npm run dev
```
Open your browser at `http://localhost:5173`.

---

## 🧪 Testing & Evaluation

### Run Unit & Integration Tests
```bash
python -m pytest tests/test_codequery.py -v
```

### Run Benchmark Evaluation (Objective 5)
```bash
python evaluate_project.py
```
Outputs citation coverage rates, retrieval latencies, and structural graph expansion statistics.
