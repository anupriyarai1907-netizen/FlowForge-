import { useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:5000";

function App() {
  const [files, setFiles] = useState([]);
  const [sqlFile, setSqlFile] = useState(null);
  const [question, setQuestion] = useState(
    "Generate a data flow diagram for the uploaded source code and database."
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [diagramVersion, setDiagramVersion] = useState(0);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setResult(null);

    if (files.length === 0) {
      setError("Please select at least one source-code file.");
      return;
    }

    const formData = new FormData();

    files.forEach((file) => {
      formData.append("code_files", file);
    });

    if (sqlFile) {
      formData.append("sql_file", sqlFile);
    }

    formData.append("question", question);

    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/generate-dfd`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.error || "DFD generation failed. Please try again."
        );
      }

      setResult(data);
      setDiagramVersion(Date.now());
    
} catch (err) {
  if (err instanceof TypeError) {
    setError(
      "Unable to connect to the backend. Please ensure the Flask server is running on port 5000."
    );
  } else {
    setError(
      err.message || "An unexpected error occurred. Please try again."
    );
  }
}
 finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header className="navbar">
        <a className="brand" href="#home">
          <span className="brand-icon">◇</span>
          Flow<span className="brand-highlight">Forge</span>
        </a>

        <nav>
          <a href="#home">Home</a>
          <a href="#generator">Generator</a>
          <a href="#about">About</a>
        </nav>

        <span className="status-badge">
          <span className="status-dot"></span>
          AI Powered
        </span>
      </header>

      <main id="home">
        <section className="hero-section">
          <div className="hero-content">
            <span className="eyebrow">
              INTELLIGENT DATA FLOW ANALYSIS
            </span>

            <h1>
              Turn your code into
              <br />
              <span>clear data flow diagrams.</span>
            </h1>

            <p className="hero-description">
              Upload your source code, analyze how data moves through
              your application, and generate a structured Data Flow
              Diagram with AI.
            </p>

            <a href="#generator" className="primary-button">
              Generate your DFD <span>→</span>
            </a>

            <div className="feature-pills">
              <span>✓ Multi-language support</span>
              <span>✓ AI-assisted analysis</span>
              <span>✓ Visual diagrams</span>
            </div>
          </div>

          <div className="flow-preview">
            <div className="preview-header">
              <span className="window-dots">
                <i></i><i></i><i></i>
              </span>
              <span>DATA FLOW OVERVIEW</span>
              <span className="preview-live">LIVE PREVIEW</span>
            </div>

            <div className="flow-canvas">
              <div className="flow-node source-node">
                <span className="node-icon">{"</>"}</span>
                <strong>Source Code</strong>
                <small>Python · Java · C++</small>
              </div>

              <div className="flow-arrow">↓</div>

              <div className="flow-node process-node">
                <span className="node-icon">✳</span>
                <strong>AI Processing</strong>
                <small>Parsing & analysis</small>
              </div>

              <div className="flow-arrow">↓</div>

              <div className="flow-node output-node">
                <span className="node-icon">▧</span>
                <strong>DFD Diagram</strong>
                <small>Structured visualization</small>
              </div>
            </div>

            <div className="preview-footer">
              <span>● Analysis pipeline</span>
              <span>JSON + Diagram output</span>
            </div>
          </div>
        </section>

        <section className="stats-row">
          <div>
            <strong>06+</strong>
            <span>Supported source extensions</span>
          </div>
          <div>
            <strong>AI</strong>
            <span>Intelligent code analysis</span>
          </div>
          <div>
            <strong>DFD</strong>
            <span>Automated diagram generation</span>
          </div>
        </section>

        <section id="generator" className="generator-section">
          <div className="section-heading">
            <span className="eyebrow">YOUR WORKSPACE</span>
            <h2>Generate your diagram</h2>
            <p>
              Upload source files, add an optional SQL schema, and let
              the analyzer build your DFD.
            </p>
          </div>

          <div className="workspace">
            <form className="upload-card" onSubmit={handleSubmit}>
              <div className="card-heading">
                <div>
                  <span className="step-label">STEP 01</span>
                  <h3>Upload source code</h3>
                </div>
                <span className="heading-icon">{"</>"}</span>
              </div>

              <label className="field-label" htmlFor="code-files">
                Source files <span className="required">*</span>
              </label>

              <label className="file-drop" htmlFor="code-files">
                <span className="upload-icon">↑</span>
                <strong>Click to select files</strong>
                <span>or choose multiple files from your computer</span>
                <small>.py .java .c .cpp .h .hpp .js</small>
              </label>

              <input
                id="code-files"
                className="hidden-input"
                type="file"
                accept=".py,.java,.c,.cpp,.h,.hpp,.js"
                multiple
                onChange={(event) =>
                  setFiles(Array.from(event.target.files || []))
                }
              />

              {files.length > 0 && (
                <div className="selected-files">
                  <div className="selected-heading">
                    <strong>{files.length} file(s) selected</strong>
                    <button
                      type="button"
                      className="text-button"
                      onClick={() => {
                        setFiles([]);
                        document.getElementById("code-files").value = "";
                      }}
                    >
                      Clear
                    </button>
                  </div>

                  {files.map((file, index) => (
                    <div className="file-item" key={`${file.name}-${index}`}>
                      <span className="file-symbol">▤</span>
                      <span className="file-name">{file.name}</span>
                      <span className="file-size">
                        {(file.size / 1024).toFixed(1)} KB
                      </span>
                    </div>
                  ))}
                </div>
              )}

              <div className="field-divider"></div>

              <div className="card-heading sql-heading">
                <div>
                  <span className="step-label">STEP 02</span>
                  <h3>Database schema</h3>
                </div>
                <span className="optional-label">OPTIONAL</span>
              </div>

              <label className="sql-upload" htmlFor="sql-file">
                <span className="database-icon">▤</span>
                <span>
                  <strong>
                    {sqlFile ? sqlFile.name : "Choose SQL file"}
                  </strong>
                  <small>
                    {sqlFile
                      ? "SQL file selected"
                      : "Upload a .sql schema to include data stores"}
                  </small>
                </span>
                <span className="browse-button">Browse</span>
              </label>

              <input
                id="sql-file"
                className="hidden-input"
                type="file"
                accept=".sql"
                onChange={(event) =>
                  setSqlFile(event.target.files?.[0] || null)
                }
              />

              {sqlFile && (
                <button
                  type="button"
                  className="text-button remove-sql"
                  onClick={() => {
                    setSqlFile(null);
                    document.getElementById("sql-file").value = "";
                  }}
                >
                  Remove SQL file
                </button>
              )}

              <div className="field-divider"></div>

              <label className="field-label" htmlFor="question">
                Instructions for AI
              </label>

              <textarea
                id="question"
                className="question-input"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                rows={3}
                placeholder="Describe the DFD you want to generate..."
              />

              {error && (
                <div className="error-message" role="alert">
                  <strong>Something went wrong</strong>
                  <p>{error}</p>
                </div>
              )}

              <button
                type="submit"
                className="generate-button"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <span className="spinner"></span>
                    Generating diagram...
                  </>
                ) : (
                  <>Generate DFD <span>→</span></>
                )}
              </button>

              <p className="privacy-note">
                Your selected files are sent to your configured backend
                for analysis.
              </p>
            </form>

            <div className="results-column">
              <div className="result-card">
                <div className="result-header">
                  <div>
                    <span className="step-label">OUTPUT 01</span>
                    <h3>DFD Visualization</h3>
                  </div>
                  {result && (
                    <span className="success-badge">Generated</span>
                  )}
                </div>

                {result?.diagram_url ? (
                  <div className="diagram-container">
                    <img
                      className="diagram-image"
                      src={`${API_URL}${result.diagram_url}?v=${diagramVersion}`}
                      alt="Generated Data Flow Diagram"
                    />
                    <a
                      className="download-link"
                      href={`${API_URL}${result.diagram_url}?v=${diagramVersion}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Open diagram in new tab ↗
                    </a>
                  </div>
                ) : (
                  <div className="empty-state">
                    <div className="empty-diagram">
                      <div className="mini-node">Input</div>
                      <span>→</span>
                      <div className="mini-node">Process</div>
                      <span>→</span>
                      <div className="mini-node">Output</div>
                    </div>
                    <h4>Your diagram will appear here</h4>
                    <p>
                      Upload your code and click Generate DFD to see
                      the generated visualization.
                    </p>
                  </div>
                )}
              </div>

              <div className="result-card json-card">
                <div className="result-header">
                  <div>
                    <span className="step-label">OUTPUT 02</span>
                    <h3>Structured DFD Data</h3>
                  </div>
                  <span className="json-label">JSON</span>
                </div>

                {result ? (
                  <>
                    <pre className="json-output">
                      {JSON.stringify(result.dfd ?? result, null, 2)}
                    </pre>
                    <button
                      type="button"
                      className="copy-button"
                      onClick={() =>
                        navigator.clipboard
                          .writeText(
                            JSON.stringify(result.dfd ?? result, null, 2)
                          )
                          .catch(() =>
                            setError("Could not copy JSON to clipboard.")
                          )
                      }
                    >
                      Copy JSON
                    </button>
                  </>
                ) : (
                  <div className="json-placeholder">
                    <span>{"{ }"}</span>
                    <p>Structured nodes, connections and analysis data will appear here.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>

        <section id="about" className="about-section">
          <span className="eyebrow">HOW IT WORKS</span>
          <h2>From source code to insights</h2>

          <div className="steps-grid">
            <article className="step-card">
              <span>01</span>
              <h3>Upload</h3>
              <p>Choose source files and optionally add your SQL schema.</p>
            </article>
            <article className="step-card">
              <span>02</span>
              <h3>Analyze</h3>
              <p>The backend chunks code, retrieves context and processes it with AI.</p>
            </article>
            <article className="step-card">
              <span>03</span>
              <h3>Visualize</h3>
              <p>Review the generated DFD diagram and its structured JSON.</p>
            </article>
          </div>
        </section>
      </main>

      <footer className="footer">
        <a className="brand" href="#home">
          <span className="brand-icon">◇</span>
          Flow<span className="brand-highlight">Forge</span>
        </a>
        <p>AI-Based Data Flow Diagram Generator · Minor Project</p>
      </footer>
    </div>
  );
}

export default App;