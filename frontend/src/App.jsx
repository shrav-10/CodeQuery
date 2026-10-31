import { useState, useEffect } from "react";
import "./App.css";

const BACKEND_URL = "http://127.0.0.1:8000";

function App() {
  const [activeTab, setActiveTab] = useState("chat");
  const [repositoryUrl, setRepositoryUrl] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeResult, setAnalyzeResult] = useState(null);
  const [repositories, setRepositories] = useState([]);
  const [selectedRepo, setSelectedRepo] = useState("requests");

  // Chat State
  const [chatMessages, setChatMessages] = useState([
    {
      sender: "ai",
      text: "👋 Welcome to **CodeQuery**! I am your structure-aware AI codebase assistant. Select an indexed repository above or ingest a new public GitHub repo, then ask natural language questions grounded in the source code with exact file:line citations.",
      citations: [],
      graphContext: null,
      timings: null
    }
  ]);
  const [inputQuestion, setInputQuestion] = useState("");
  const [isQuerying, setIsQuerying] = useState(false);
  const [expandedGraphId, setExpandedGraphId] = useState(null);

  // Code Viewer Modal State
  const [codeModal, setCodeModal] = useState({
    isOpen: false,
    file: "",
    startLine: 1,
    endLine: 1,
    content: "",
    isLoading: false
  });

  // Graph Explorer State
  const [graphData, setGraphData] = useState(null);
  const [graphFilter, setGraphFilter] = useState("all");
  const [graphSearch, setGraphSearch] = useState("");
  const [isLoadingGraph, setIsLoadingGraph] = useState(false);

  // Evaluation Benchmark State
  const [evalResults, setEvalResults] = useState(null);
  const [isEvaluating, setIsEvaluating] = useState(false);

  // Fetch available repositories on load
  const loadRepositories = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/repositories`);
      if (res.ok) {
        const data = await res.json();
        const repos = data.repositories || [];
        setRepositories(repos);
        if (repos.length > 0 && !repos.find((r) => r.name === selectedRepo)) {
          setSelectedRepo(repos[0].name);
        }
      }
    } catch (e) {
      console.warn("Could not fetch repositories:", e);
    }
  };

  useEffect(() => {
    loadRepositories();
  }, []);

  // Fetch graph data when switching to graph tab
  const loadGraphData = async (repoName) => {
    setIsLoadingGraph(true);
    try {
      const res = await fetch(`${BACKEND_URL}/repository/${repoName || selectedRepo}/graph?max_nodes=120`);
      if (res.ok) {
        const data = await res.json();
        setGraphData(data);
      }
    } catch (e) {
      console.warn("Failed to load graph:", e);
    }
    setIsLoadingGraph(false);
  };

  useEffect(() => {
    if (activeTab === "graph" && selectedRepo) {
      loadGraphData(selectedRepo);
    }
  }, [activeTab, selectedRepo]);

  // Open Citation / Code Inspector
  const openCodeModal = async (citation) => {
    setCodeModal({
      isOpen: true,
      file: citation.file,
      startLine: citation.start_line,
      endLine: citation.end_line,
      content: citation.snippet || "Loading code from repository...",
      isLoading: true
    });

    try {
      const res = await fetch(
        `${BACKEND_URL}/repository/${selectedRepo}/file?file_path=${encodeURIComponent(
          citation.file
        )}&start_line=${citation.start_line}&end_line=${citation.end_line}`
      );
      if (res.ok) {
        const data = await res.json();
        setCodeModal((prev) => ({
          ...prev,
          content: data.content || data.full_content || citation.snippet,
          isLoading: false
        }));
      } else {
        setCodeModal((prev) => ({ ...prev, isLoading: false }));
      }
    } catch (e) {
      setCodeModal((prev) => ({ ...prev, isLoading: false }));
    }
  };

  // Submit Q&A Query
  const handleSendQuery = async (queryText) => {
    const question = (queryText || inputQuestion).trim();
    if (!question || isQuerying) return;

    const userMessage = { sender: "user", text: question };
    setChatMessages((prev) => [...prev, userMessage]);
    setInputQuestion("");
    setIsQuerying(true);

    try {
      const res = await fetch(`${BACKEND_URL}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: question,
          repository: selectedRepo,
          top_k: 4
        })
      });

      if (!res.ok) throw new Error("Backend query failed");
      const data = await res.json();

      const aiMessage = {
        sender: "ai",
        text: data.answer || "No response received.",
        citations: data.citations || [],
        graphContext: data.graph_context || null,
        timings: data.timings || null,
        provider: data.provider || "ollama"
      };

      setChatMessages((prev) => [...prev, aiMessage]);
    } catch (err) {
      setChatMessages((prev) => [
        ...prev,
        {
          sender: "ai",
          text: `⚠️ Error processing question: ${err.message}. Please check if the repository is analyzed and the backend is running.`,
          citations: []
        }
      ]);
    }

    setIsQuerying(false);
  };

  // Ingest & Analyze Repository
  const handleAnalyzeRepository = async () => {
    if (!repositoryUrl.trim()) return;
    setAnalyzing(true);
    setAnalyzeResult(null);

    try {
      const res = await fetch(`${BACKEND_URL}/analyze-repository`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          repository_url: repositoryUrl.trim()
        })
      });

      const data = await res.json();
      setAnalyzeResult(data);
      if (data.status === "success") {
        await loadRepositories();
        if (data.repository_name) {
          setSelectedRepo(data.repository_name);
        }
      }
    } catch (e) {
      setAnalyzeResult({
        status: "error",
        message: "Failed to connect to CodeQuery backend."
      });
    }

    setAnalyzing(false);
  };

  // Run Objective 5 Benchmark Evaluation
  const handleRunEvaluation = async () => {
    setIsEvaluating(true);
    setEvalResults(null);

    try {
      const res = await fetch(`${BACKEND_URL}/evaluate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          repository: selectedRepo
        })
      });

      if (res.ok) {
        const data = await res.json();
        setEvalResults(data);
      }
    } catch (e) {
      console.warn("Evaluation failed:", e);
    }

    setIsEvaluating(false);
  };

  const sampleQuestions = [
    "How does Session handle requests and connection pooling?",
    "What classes inherit from BaseAdapter or SessionRedirectMixin?",
    "Explain the error handling and retry mechanism in HTTPAdapter",
    "Trace the call hierarchy of prepare_request"
  ];

  const filteredGraphNodes = graphData?.nodes?.filter((n) => {
    const matchesType = graphFilter === "all" || n.type === graphFilter;
    const matchesSearch =
      !graphSearch ||
      n.label.toLowerCase().includes(graphSearch.toLowerCase()) ||
      (n.file && n.file.toLowerCase().includes(graphSearch.toLowerCase()));
    return matchesType && matchesSearch;
  }) || [];

  return (
    <div className="app">
      {/* Navigation Header */}
      <nav className="navbar">
        <div className="logo">
          <div className="logo-icon">&lt;/&gt;</div>
          <span>CodeQuery</span>
        </div>

        {/* Active Repository Selector */}
        <div className="repo-select-container">
          <span>Active Repo:</span>
          <select
            className="repo-select"
            value={selectedRepo}
            onChange={(e) => setSelectedRepo(e.target.value)}
          >
            {repositories.map((r) => (
              <option key={r.name} value={r.name}>
                📁 {r.name} {r.is_indexed ? "✓" : ""}
              </option>
            ))}
            {repositories.length === 0 && <option value="requests">requests</option>}
          </select>
        </div>

        <div className="nav-links">
          <a
            href="#chat"
            className={activeTab === "chat" ? "active" : ""}
            onClick={() => setActiveTab("chat")}
          >
            Q&A Assistant
          </a>
          <a
            href="#graph"
            className={activeTab === "graph" ? "active" : ""}
            onClick={() => setActiveTab("graph")}
          >
            Structural Graph
          </a>
          <a
            href="#analyze"
            className={activeTab === "analyze" ? "active" : ""}
            onClick={() => setActiveTab("analyze")}
          >
            Ingest Repo
          </a>
          <a
            href="#eval"
            className={activeTab === "eval" ? "active" : ""}
            onClick={() => setActiveTab("eval")}
          >
            Benchmark
          </a>
        </div>
      </nav>

      {/* Tab Switcher Bar */}
      <div className="workspace-tabs">
        <button
          className={`tab-btn ${activeTab === "chat" ? "active" : ""}`}
          onClick={() => setActiveTab("chat")}
        >
          💬 Natural Language Q&A
        </button>
        <button
          className={`tab-btn ${activeTab === "graph" ? "active" : ""}`}
          onClick={() => setActiveTab("graph")}
        >
          🕸️ Call & Inheritance Graph
        </button>
        <button
          className={`tab-btn ${activeTab === "analyze" ? "active" : ""}`}
          onClick={() => setActiveTab("analyze")}
        >
          📥 Ingest / Index Repository
        </button>
        <button
          className={`tab-btn ${activeTab === "eval" ? "active" : ""}`}
          onClick={() => setActiveTab("eval")}
        >
          📊 System Evaluation
        </button>
      </div>

      {/* TAB 1: Q&A Chat Assistant */}
      {activeTab === "chat" && (
        <section className="chat-section" id="chat">
          <div className="chat-card">
            <div className="chat-header">
              <div className="chat-header-title">
                <span>✦</span>
                <span>CodeQuery Structure-Aware Assistant</span>
              </div>
              <div className="chat-active-badge">
                Repository: <strong>{selectedRepo}</strong>
              </div>
            </div>

            <div className="chat-messages">
              {chatMessages.map((msg, idx) => (
                <div key={idx} className={`chat-msg ${msg.sender}`}>
                  <div className={`msg-avatar ${msg.sender === "user" ? "user-av" : "ai-av"}`}>
                    {msg.sender === "user" ? "👤" : "✦"}
                  </div>

                  <div className="msg-bubble">
                    <div style={{ whiteSpace: "pre-wrap" }}>{msg.text}</div>

                    {/* Grounded Citations */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="citations-wrapper">
                        <div className="citations-title">
                          <span>📌 Grounded Source Citations:</span>
                        </div>
                        <div className="citations-list">
                          {msg.citations.map((cit, cIdx) => (
                            <button
                              key={cIdx}
                              className="citation-pill"
                              title="Click to view exact source lines"
                              onClick={() => openCodeModal(cit)}
                            >
                              <span>📄 {cit.citation}</span>
                              {cit.name && <small style={{ color: "#818cf8" }}>({cit.name})</small>}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Structural Graph Expansion Context */}
                    {msg.graphContext && msg.graphContext.relationships && msg.graphContext.relationships.length > 0 && (
                      <div className="graph-context-box">
                        <div
                          className="graph-context-header"
                          onClick={() => setExpandedGraphId(expandedGraphId === idx ? null : idx)}
                        >
                          <span>
                            🕸️ Structural Graph Expansion ({msg.graphContext.relationships.length} connections)
                          </span>
                          <span>{expandedGraphId === idx ? "▲" : "▼"}</span>
                        </div>

                        {expandedGraphId === idx && (
                          <div className="graph-context-content">
                            {msg.graphContext.relationships.map((rel, rIdx) => (
                              <div key={rIdx} className="graph-rel-item">
                                <span className="graph-rel-dot"></span>
                                <span>{rel}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Telemetry Footer */}
                    {msg.timings && (
                      <div className="msg-telemetry">
                        <span className="telemetry-item">
                          ⚡ Vector: {msg.timings.vector_search}s
                        </span>
                        <span className="telemetry-item">
                          🕸️ Graph: {msg.timings.graph_expansion}s
                        </span>
                        <span className="telemetry-item">
                          🤖 LLM: {msg.timings.llm_generation}s
                        </span>
                        <span className="telemetry-item">
                          ({msg.provider})
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {isQuerying && (
                <div className="chat-msg ai">
                  <div className="msg-avatar ai-av">✦</div>
                  <div className="msg-bubble" style={{ color: "#94a3b8" }}>
                    <span>Retrieving relevant chunks & expanding structural call graph...</span>
                  </div>
                </div>
              )}

              {chatMessages.length === 1 && (
                <div className="empty-chat">
                  <div className="empty-icon">💡</div>
                  <h4>Explore {selectedRepo} with Natural Language</h4>
                  <p style={{ fontSize: "13px", marginTop: "6px" }}>
                    Try asking one of these suggested queries:
                  </p>
                  <div className="empty-suggestions">
                    {sampleQuestions.map((q, i) => (
                      <button
                        key={i}
                        className="suggestion-pill"
                        onClick={() => handleSendQuery(q)}
                      >
                        → {q}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Input Form */}
            <form
              className="chat-input-bar"
              onSubmit={(e) => {
                e.preventDefault();
                handleSendQuery();
              }}
            >
              <input
                type="text"
                className="chat-input"
                placeholder={`Ask any question about ${selectedRepo}... (e.g. How does error handling work?)`}
                value={inputQuestion}
                onChange={(e) => setInputQuestion(e.target.value)}
                disabled={isQuerying}
              />
              <button
                type="submit"
                className="chat-send-btn"
                disabled={isQuerying || !inputQuestion.trim()}
              >
                {isQuerying ? "Thinking..." : "Ask →"}
              </button>
            </form>
          </div>
        </section>
      )}

      {/* TAB 2: Structural Relationship Graph */}
      {activeTab === "graph" && (
        <section className="graph-section" id="graph">
          <div className="graph-container">
            <div className="graph-toolbar">
              <div>
                <h3 style={{ fontSize: "18px", fontWeight: "700" }}>
                  Structural Codebase Graph ({selectedRepo})
                </h3>
                <p style={{ fontSize: "12px", color: "#94a3b8", marginTop: "4px" }}>
                  Total Nodes: {graphData?.stats?.total_nodes || 0} • Total Edges: {graphData?.stats?.total_edges || 0} (Capturing Calls, Inheritance, Containment)
                </p>
              </div>

              <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
                <div className="graph-filter-chips">
                  {["all", "function", "method", "class", "module"].map((t) => (
                    <button
                      key={t}
                      className={`filter-chip ${graphFilter === t ? "active" : ""}`}
                      onClick={() => setGraphFilter(t)}
                    >
                      {t.toUpperCase()}
                    </button>
                  ))}
                </div>

                <input
                  type="text"
                  placeholder="Filter symbols..."
                  className="graph-search-input"
                  value={graphSearch}
                  onChange={(e) => setGraphSearch(e.target.value)}
                />
              </div>
            </div>

            {isLoadingGraph ? (
              <div style={{ padding: "60px", textAlign: "center", color: "#94a3b8" }}>
                Loading structural graph from NetworkX...
              </div>
            ) : (
              <div className="graph-svg-wrapper">
                <div className="graph-node-grid">
                  {filteredGraphNodes.slice(0, 48).map((node) => (
                    <div
                      key={node.id}
                      className="node-card"
                      onClick={() =>
                        openCodeModal({
                          file: node.file,
                          start_line: node.line || 1,
                          end_line: (node.line || 1) + 20,
                          name: node.label,
                          snippet: node.docstring || "No docstring available."
                        })
                      }
                    >
                      <div className="node-card-header">
                        <span className={`node-type-badge type-${node.type}`}>
                          {node.type}
                        </span>
                        <span style={{ fontSize: "11px", color: "#64748b" }}>
                          Line {node.line}
                        </span>
                      </div>
                      <div className="node-name">{node.label}</div>
                      <div className="node-file">📄 {node.file}</div>
                      {node.docstring && (
                        <div className="node-doc">{node.docstring}</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      {/* TAB 3: Ingest / Index Repository */}
      {activeTab === "analyze" && (
        <section className="analyzer" id="analyze">
          <div className="analyzer-content">
            <div className="badge">
              <span>✦</span> Ingestion & Parallel Indexing
            </div>
            <h2>
              Understand any <span className="gradient-text">repository</span>
            </h2>
            <p>
              Connect a public GitHub repository URL or local codebase folder. CodeQuery parses structural AST boundaries, builds a NetworkX call/inheritance graph, and indexes code embeddings in ChromaDB.
            </p>

            <div className="repository-input">
              <div className="github-input-icon">●</div>
              <input
                type="text"
                placeholder="https://github.com/owner/repository OR local folder name"
                value={repositoryUrl}
                onChange={(e) => setRepositoryUrl(e.target.value)}
              />
              <button onClick={handleAnalyzeRepository} disabled={analyzing}>
                {analyzing ? "Indexing..." : "Analyze Repository →"}
              </button>
            </div>

            <div className="analyzer-note">
              ✓ Fast Parallel AST Parsing &nbsp;•&nbsp; ✓ NetworkX Graph &nbsp;•&nbsp; ✓ FastEmbed 200+ chunks/s
            </div>

            {analyzeResult && (
              <div
                className="repository-message"
                style={{
                  background: analyzeResult.status === "success" ? "rgba(34, 197, 94, 0.1)" : "rgba(239, 68, 68, 0.1)",
                  border: `1px solid ${analyzeResult.status === "success" ? "rgba(34, 197, 94, 0.3)" : "rgba(239, 68, 68, 0.3)"}`,
                  padding: "16px",
                  borderRadius: "12px",
                  marginTop: "20px"
                }}
              >
                <strong>{analyzeResult.status === "success" ? "✓ Analysis Complete" : "⚠️ Analysis Error"}:</strong>
                <p style={{ marginTop: "6px" }}>{analyzeResult.message || analyzeResult.error}</p>
                {analyzeResult.status === "success" && (
                  <div style={{ display: "flex", gap: "16px", marginTop: "10px", fontSize: "12px" }}>
                    <span>📁 Files: {analyzeResult.files_analyzed}</span>
                    <span>🧩 Chunks: {analyzeResult.chunks_indexed}</span>
                    <span>🕸️ Graph Nodes: {analyzeResult.graph_nodes}</span>
                    <span>⏱️ Total Time: {analyzeResult.total_time_seconds}s</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </section>
      )}

      {/* TAB 4: Evaluation Benchmark Suite (Objective 5) */}
      {activeTab === "eval" && (
        <section className="eval-section" id="eval">
          <div className="chat-card" style={{ padding: "28px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <h3 style={{ fontSize: "20px", fontWeight: "700" }}>
                  System Evaluation Benchmark (Objective 5)
                </h3>
                <p style={{ fontSize: "13px", color: "#94a3b8", marginTop: "4px" }}>
                  Evaluate Answer Accuracy, Exact File:Line Citation Correctness, and Retrieval Latency.
                </p>
              </div>

              <button
                className="chat-send-btn"
                onClick={handleRunEvaluation}
                disabled={isEvaluating}
              >
                {isEvaluating ? "Evaluating..." : "Run Benchmark →"}
              </button>
            </div>

            {evalResults && (
              <div style={{ marginTop: "24px" }}>
                <div className="eval-stats-grid">
                  <div className="eval-stat-card">
                    <div className="eval-stat-label">Citation Coverage</div>
                    <div className="eval-stat-val" style={{ color: "#34d399" }}>
                      {evalResults.citation_coverage_rate}
                    </div>
                  </div>
                  <div className="eval-stat-card">
                    <div className="eval-stat-label">Average Latency</div>
                    <div className="eval-stat-val" style={{ color: "#38bdf8" }}>
                      {evalResults.average_query_latency_seconds}s
                    </div>
                  </div>
                  <div className="eval-stat-card">
                    <div className="eval-stat-label">Total Citations</div>
                    <div className="eval-stat-val" style={{ color: "#a78bfa" }}>
                      {evalResults.total_citations_generated}
                    </div>
                  </div>
                </div>

                <table className="eval-table">
                  <thead>
                    <tr>
                      <th>Evaluated Query</th>
                      <th>Citations Grounded</th>
                      <th>Graph Expansion</th>
                      <th>Latency</th>
                    </tr>
                  </thead>
                  <tbody>
                    {evalResults.evaluations.map((ev, i) => (
                      <tr key={i}>
                        <td style={{ fontWeight: "500" }}>{ev.query}</td>
                        <td>
                          {ev.citations.map((c, idx) => (
                            <span key={idx} className="citation-pill" style={{ display: "inline-block", margin: "2px" }}>
                              {c}
                            </span>
                          ))}
                        </td>
                        <td>
                          <span style={{ color: ev.has_graph_expansion ? "#34d399" : "#f87171" }}>
                            {ev.has_graph_expansion ? `✓ ${ev.graph_relationships_count} edges` : "✗"}
                          </span>
                        </td>
                        <td>{ev.duration_seconds}s</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </section>
      )}

      {/* Code Viewer Modal for Exact Citation Inspection */}
      {codeModal.isOpen && (
        <div className="code-modal-overlay" onClick={() => setCodeModal((prev) => ({ ...prev, isOpen: false }))}>
          <div className="code-modal" onClick={(e) => e.stopPropagation()}>
            <div className="code-modal-header">
              <div className="code-modal-title">
                <span>📄</span>
                <span>{codeModal.file}</span>
                <span style={{ color: "#94a3b8" }}>
                  (Lines {codeModal.startLine} - {codeModal.endLine})
                </span>
              </div>
              <button
                className="code-modal-close"
                onClick={() => setCodeModal((prev) => ({ ...prev, isOpen: false }))}
              >
                ✕
              </button>
            </div>

            <div className="code-modal-body">
              {codeModal.isLoading ? (
                <div style={{ color: "#94a3b8", padding: "20px" }}>Loading file content...</div>
              ) : (
                codeModal.content.split("\n").map((line, idx) => {
                  const currentLineNum = codeModal.startLine + idx;
                  return (
                    <div key={idx} className="code-line highlight">
                      <span className="line-num">{currentLineNum}</span>
                      <span className="line-text">{line}</span>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;