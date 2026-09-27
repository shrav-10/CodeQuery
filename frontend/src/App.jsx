import { useState } from "react";
function App() {
  const [repositoryUrl, setRepositoryUrl] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [repositoryMessage, setRepositoryMessage] = useState("");
  return (
    <div className="app">

      {/* Navigation */}
      <nav className="navbar">
        <div className="logo">
          <div className="logo-icon">&lt;/&gt;</div>
          <span>CodeQuery</span>
        </div>

        <div className="nav-links">
          <a className="active" href="#home">Home</a>
          <a href="#features">Features</a>
          <a href="#how-it-works">How It Works</a>
          <a href="#about">About</a>
        </div>

<a href="#analyze" className="nav-button">          <span>⌘</span>
          Get Started
</a>      </nav>


      {/* Hero Section */}
      <main className="hero" id="home">

        {/* Left Side */}
        <section className="hero-content">

          <div className="badge">
            <span>✦</span>
            AI-Powered Codebase Assistant
          </div>

          <h1>
            Understand Any
            <br />
            Codebase
            <span className="gradient-text"> with AI</span>
          </h1>

          <p className="hero-description">
            CodeQuery helps you explore, analyze, and understand any
            codebase using the power of AI. Ask natural language questions,
            get accurate answers, and see exactly where the information
            comes from.
          </p>

          <div className="hero-buttons">
           <a href="#analyze" className="primary-button">
              <span>⌘</span>
              Get Started
              <span>→</span>
            </a>

            <button className="secondary-button">
              <span>▶</span>
              Watch Demo
            </button>
          </div>

        </section>


        {/* Right Side */}
        <section className="visual">

          {/* Repository Card */}
          <div className="floating-card repository-card">
            <div className="card-header">
              <span className="github-icon">●</span>
              <span>GitHub Repository</span>
            </div>

            <div className="file-tree">
              <div>▸ 📁 src/</div>
              <div>▸ 📁 components/</div>
              <div>▸ 📁 pages/</div>
              <div>▸ 📁 services/</div>
              <div>▸ 📁 models/</div>
            </div>
          </div>


          {/* CodeQuery Core */}
          <div className="core-container">

            <div className="core-glow"></div>

            <div className="code-cube">
              <div className="cube-symbol">
                &lt;/&gt;
              </div>
            </div>

            <div className="core-platform"></div>

          </div>


          {/* AI Answer Card */}
          <div className="floating-card answer-card">

            <div className="question">
              <div className="avatar">●</div>
              <span>
                How does the authentication
                system work?
              </span>
            </div>

            <div className="answer">
              <div className="avatar ai">✦</div>

              <div>
                <p>
                  Authentication is handled through
                  <strong> auth.py</strong> using JWT tokens...
                </p>

                <div className="source">
                  View source →
                  <span>auth.py:42</span>
                </div>
              </div>
            </div>

          </div>


          {/* Relationship Card */}
          <div className="floating-card relationship-card">

            <div className="card-header">
              <span>✦</span>
              Code Relationships
            </div>

            <div className="graph">
              <span className="node node-1"></span>
              <span className="node node-2"></span>
              <span className="node node-3"></span>
              <span className="node node-4"></span>
              <span className="node node-5"></span>

              <span className="line line-1"></span>
              <span className="line line-2"></span>
              <span className="line line-3"></span>
              <span className="line line-4"></span>
            </div>

          </div>


          {/* Code Card */}
          <div className="floating-card code-card">

            <div className="code-title">
              <span>auth.py</span>
              <span>● ● ●</span>
            </div>

            <pre>
{`42  def create_access_token(user_id):
43      payload = {
44          "user_id": user_id
45      }
46      return jwt.encode(
47          payload,
48          SECRET_KEY
49      )`}
            </pre>

          </div>

        </section>

      </main>

          {/* Repository Analyzer */}
      <section className="analyzer" id="analyze">

        <div className="analyzer-content">

          <div className="badge">
            <span>✦</span>
            Start Exploring
          </div>

          <h2>
            Understand your
            <span className="gradient-text"> repository</span>
          </h2>

          <p>
            Connect a public GitHub repository and let CodeQuery
            analyze its structure, relationships, and source code.
          </p>

          <div className="repository-input">

            <div className="github-input-icon">
              ●
            </div>

            <input
  type="text"
  placeholder="https://github.com/owner/repository"
  value={repositoryUrl}
  onChange={(e) => setRepositoryUrl(e.target.value)}
/>

            <button
  onClick={async () => {
  if (!repositoryUrl.trim()) {
    setRepositoryMessage("Please enter a GitHub repository URL.");
    return;
  }

  setAnalyzing(true);
  setRepositoryMessage("Connecting to CodeQuery...");

  try {
    const response = await fetch(
      "http://127.0.0.1:8000/analyze-repository",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          repository_url: repositoryUrl,
        }),
      }
    );

    const data = await response.json();

if (data.status === "success") {
  setRepositoryMessage(
    `${data.message} Files analyzed: ${data.files_analyzed}`
  );
} else {
  setRepositoryMessage(
    `Error: ${data.message} ${data.error ? `- ${data.error}` : ""}`
  );
}
  } catch (error) {
    setRepositoryMessage(
      "Could not connect to the CodeQuery backend."
    );
  }

  setAnalyzing(false);
}}
>
  {analyzing ? "Analyzing..." : "Analyze Repository →"}
</button>

          </div>

          <div className="analyzer-note">
            ✓ Public GitHub repositories &nbsp;&nbsp; • &nbsp;&nbsp;
            ✓ Python codebases &nbsp;&nbsp; • &nbsp;&nbsp;
            ✓ Source-grounded answers
          </div>
          {repositoryMessage && (
  <div className="repository-message">
    {repositoryMessage}
  </div>
)}

        </div>

      </section>
      {/* Feature Bar */}
      <section className="features" id="features">

        <div className="feature">
          <div className="feature-icon">⌘</div>
          <div>
            <h3>Works with Public Repos</h3>
            <p>Just a GitHub URL or archive</p>
          </div>
        </div>

        <div className="feature">
          <div className="feature-icon">✦</div>
          <div>
            <h3>Structure-Aware RAG</h3>
            <p>Understands code, not just text</p>
          </div>
        </div>

        <div className="feature">
          <div className="feature-icon">⌘</div>
          <div>
            <h3>Visualize Relationships</h3>
            <p>See how everything connects</p>
          </div>
        </div>

        <div className="feature">
          <div className="feature-icon">✓</div>
          <div>
            <h3>Grounded Answers</h3>
            <p>With exact file & line citations</p>
          </div>
        </div>

      </section>


      <div className="scroll-indicator">
        <span>↓</span>
        <p>Scroll to explore</p>
      </div>

    </div>
  );
}

export default App;