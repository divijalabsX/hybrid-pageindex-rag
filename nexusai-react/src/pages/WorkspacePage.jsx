import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import {
  uploadDocument,
  buildIndex,
  generateOKF,
  askQuestion,
  getWorkspaceStatus,
} from "../api/api";
import StageStepper from "../components/StageStepper";

const SUGGESTED_QUESTIONS = [
  "What is this document about?",
  "Summarize the key points",
  "What are the main sections?",
  "List any important details",
];

const INDEXING_MESSAGES = [
  "Reading document...",
  "Detecting sections...",
  "Mapping hierarchy...",
  "Building PageIndex...",
];

export default function WorkspacePage() {
  const location = useLocation();

  const [stage, setStage] = useState("upload");
  const [completed, setCompleted] = useState([]);

  const [docInfo, setDocInfo] = useState(null); // { filename, totalPages, totalWords }
  const [pendingFile, setPendingFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const [indexing, setIndexing] = useState(false);
  const [indexTree, setIndexTree] = useState(null);
  const [indexingMessage, setIndexingMessage] = useState(INDEXING_MESSAGES[0]);

  const [generatingOKF, setGeneratingOKF] = useState(false);
  const [okfFiles, setOkfFiles] = useState([]);
  const [selectedOKF, setSelectedOKF] = useState(null);

  const [qaHistory, setQaHistory] = useState([]);
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);

  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);

  // On mount, restore progress if the backend already has a document in
  // flight (e.g. the user navigated away and came back). Skip this if we
  // arrived here via "+ New Document" (fresh start).
  useEffect(() => {
    if (location.state?.fresh) return;
    getWorkspaceStatus().then(({ index, okfFiles }) => {
      if (index) {
        setIndexTree(index);
        setDocInfo({ filename: index.title });
        setCompleted((c) => [...new Set([...c, "upload", "index"])]);
        setStage(okfFiles.length > 0 ? "ask" : "knowledge");
      }
      if (okfFiles.length > 0) {
        setOkfFiles(okfFiles);
        setCompleted((c) => [...new Set([...c, "knowledge"])]);
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Rotate the indexing message while waiting for /build-index.
  useEffect(() => {
    if (!indexing) return;
    let i = 0;
    const id = setInterval(() => {
      i = (i + 1) % INDEXING_MESSAGES.length;
      setIndexingMessage(INDEXING_MESSAGES[i]);
    }, 900);
    return () => clearInterval(id);
  }, [indexing]);

  function pickFile(fileList) {
    const f = fileList?.[0];
    if (f) {
      setPendingFile(f);
      setError(null);
    }
  }

  async function handleUploadContinue() {
    if (!pendingFile) return;
    setUploading(true);
    setError(null);
    try {
      const result = await uploadDocument(pendingFile, setUploadProgress);
      setDocInfo({
        filename: result.filename ?? pendingFile.name,
        totalPages: result.total_pages,
        totalWords: result.total_words,
      });
      setCompleted((c) => [...new Set([...c, "upload"])]);
      setStage("index");
    } catch (err) {
      console.error(err);
      setError(err?.response?.data?.detail ?? "Upload failed. Is the FastAPI server running?");
    } finally {
      setUploading(false);
    }
  }

  async function handleBuildIndex() {
    setIndexing(true);
    setError(null);
    try {
      await buildIndex();
      const { index } = await getWorkspaceStatus();
      setIndexTree(index);
      setCompleted((c) => [...new Set([...c, "index"])]);
      setStage("knowledge");
    } catch (err) {
      console.error(err);
      setError(err?.response?.data?.detail ?? "Building the index failed.");
    } finally {
      setIndexing(false);
    }
  }

  async function handleGenerateOKF() {
    setGeneratingOKF(true);
    setError(null);
    try {
      await generateOKF({});
      const { okfFiles } = await getWorkspaceStatus();
      setOkfFiles(okfFiles);
      setCompleted((c) => [...new Set([...c, "knowledge"])]);
    } catch (err) {
      console.error(err);
      setError(err?.response?.data?.detail ?? "OKF generation failed.");
    } finally {
      setGeneratingOKF(false);
    }
  }

  async function handleAsk(q) {
    const text = (q ?? question).trim();
    if (!text || asking) return;
    setAsking(true);
    setError(null);
    try {
      const result = await askQuestion(text);
      const answer = result?.answer ?? result?.error ?? "No answer returned.";
      setQaHistory((h) => [{ question: text, answer }, ...h]);
      setQuestion("");
    } catch (err) {
      console.error(err);
      setError("Could not reach the assistant.");
    } finally {
      setAsking(false);
    }
  }

  return (
    <div className="page">
      <StageStepper active={stage} completed={completed} />

      {error && (
        <div className="card" style={{ borderColor: "var(--color-danger)", color: "var(--color-danger)", marginBottom: 20 }}>
          {error}
        </div>
      )}

      {stage === "upload" && (
        <UploadStage
          pendingFile={pendingFile}
          dragOver={dragOver}
          setDragOver={setDragOver}
          onPick={pickFile}
          onContinue={handleUploadContinue}
          uploading={uploading}
          uploadProgress={uploadProgress}
        />
      )}

      {stage === "index" && (
        <IndexStage
          docInfo={docInfo}
          indexing={indexing}
          indexingMessage={indexingMessage}
          indexTree={indexTree}
          onBuild={handleBuildIndex}
          onContinue={() => setStage("knowledge")}
        />
      )}

      {stage === "knowledge" && (
        <KnowledgeStage
          indexTree={indexTree}
          generating={generatingOKF}
          okfFiles={okfFiles}
          selected={selectedOKF}
          setSelected={setSelectedOKF}
          onGenerate={handleGenerateOKF}
          onContinue={() => setStage("ask")}
        />
      )}

      {stage === "ask" && (
        <AskStage
          question={question}
          setQuestion={setQuestion}
          onAsk={handleAsk}
          asking={asking}
          qaHistory={qaHistory}
        />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------
// Stage 1: Upload
// ---------------------------------------------------------------------
function UploadStage({ pendingFile, dragOver, setDragOver, onPick, onContinue, uploading, uploadProgress }) {
  const inputRef = useRef(null);
  return (
    <div>
      <div style={{ textAlign: "center", marginBottom: 8 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, margin: "0 0 6px" }}>Upload your document</h1>
        <p style={{ color: "var(--color-text-muted)", fontSize: 14, margin: 0 }}>
          NexusAI will read it, index its structure, and get ready for your questions.
        </p>
      </div>

      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => { e.preventDefault(); setDragOver(false); onPick(e.dataTransfer.files); }}
        className="card"
        style={{
          margin: "28px auto 0",
          maxWidth: 480,
          textAlign: "center",
          padding: "48px 24px",
          border: dragOver ? "2px dashed var(--color-primary)" : "2px dashed var(--color-border)",
          background: dragOver ? "var(--color-primary-light)" : "var(--color-surface)",
        }}
      >
        <p style={{ marginBottom: 16, fontSize: 15 }}>
          {pendingFile ? <strong>{pendingFile.name}</strong> : "↑ Drop file here"}
        </p>
        <button className="btn btn-secondary" onClick={() => inputRef.current?.click()}>
          Browse Files
        </button>
        <input
          ref={inputRef}
          type="file"
          style={{ display: "none" }}
          accept=".pdf,.docx,.doc,.txt,.md,.csv,.xlsx,.xls,.pptx,.ppt,.html,.json,.rtf,.odt"
          onChange={(e) => onPick(e.target.files)}
        />
        <div style={{ marginTop: 14, fontSize: 12, color: "var(--color-text-muted)" }}>
          PDF • DOCX • TXT • more
        </div>
      </div>

      {pendingFile && (
        <div style={{ textAlign: "center", marginTop: 20 }}>
          <button className="btn btn-primary" onClick={onContinue} disabled={uploading}>
            {uploading ? `Uploading ${uploadProgress}%` : "Continue"}
          </button>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------
// Stage 2: Build Index
// ---------------------------------------------------------------------
function IndexStage({ docInfo, indexing, indexingMessage, indexTree, onBuild, onContinue }) {
  if (indexTree) {
    return (
      <div>
        <h1 style={{ fontSize: 20, fontWeight: 700, marginBottom: 4 }}>Your document structure is ready</h1>
        <p style={{ color: "var(--color-text-muted)", fontSize: 14, marginBottom: 24 }}>
          NexusAI mapped the hierarchy of your document.
        </p>
        <div className="card">
          <TreeNode node={indexTree} depth={0} />
        </div>
        <div style={{ textAlign: "center", marginTop: 24 }}>
          <button className="btn btn-primary" onClick={onContinue}>Continue to Knowledge Layer</button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 480, margin: "0 auto", textAlign: "center" }}>
      <h1 style={{ fontSize: 20, fontWeight: 700, marginBottom: 4 }}>Build your document index</h1>
      <p style={{ color: "var(--color-text-muted)", fontSize: 14, marginBottom: 24 }}>
        NexusAI will analyze the structure of <strong>{docInfo?.filename}</strong> and create a
        hierarchical representation for intelligent retrieval.
      </p>

      {indexing ? (
        <div className="card">
          <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>{indexingMessage}</div>
          <div style={{ height: 6, borderRadius: 999, background: "var(--color-border)", overflow: "hidden" }}>
            <div
              style={{
                height: "100%",
                width: "60%",
                background: "var(--color-primary)",
                animation: "pulse-slide 1.4s ease-in-out infinite",
              }}
            />
          </div>
          <style>{`
            @keyframes pulse-slide {
              0% { transform: translateX(-60%); }
              100% { transform: translateX(160%); }
            }
          `}</style>
        </div>
      ) : (
        <button className="btn btn-primary" onClick={onBuild}>Build Index</button>
      )}
    </div>
  );
}

function TreeNode({ node, depth }) {
  const [expanded, setExpanded] = useState(depth < 1);
  const hasChildren = node.nodes && node.nodes.length > 0;
  return (
    <div style={{ marginLeft: depth * 20 }}>
      <div
        onClick={() => hasChildren && setExpanded((e) => !e)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          padding: "8px 0",
          cursor: hasChildren ? "pointer" : "default",
          borderBottom: depth === 0 ? "1px solid var(--color-border)" : "none",
        }}
      >
        {hasChildren && <span style={{ fontSize: 12, color: "var(--color-text-muted)" }}>{expanded ? "▾" : "▸"}</span>}
        <strong style={{ fontSize: depth === 0 ? 16 : 14 }}>{node.title}</strong>
        <span style={{ fontSize: 12, color: "var(--color-text-muted)" }}>p.{node.start_index}–{node.end_index}</span>
      </div>
      {node.summary && (
        <p style={{ fontSize: 13, color: "var(--color-text-muted)", margin: "0 0 8px" }}>{node.summary}</p>
      )}
      {hasChildren && expanded && node.nodes.map((child) => (
        <TreeNode key={child.node_id} node={child} depth={depth + 1} />
      ))}
    </div>
  );
}

function countNodes(node) {
  if (!node) return 0;
  const children = node.nodes ?? [];
  return 1 + children.reduce((sum, child) => sum + countNodes(child), 0);
}

// ---------------------------------------------------------------------
// Stage 3: Knowledge (OKF)
// ---------------------------------------------------------------------
function KnowledgeStage({ indexTree, generating, okfFiles, selected, setSelected, onGenerate, onContinue }) {
  return (
    <div>
      <h1 style={{ fontSize: 20, fontWeight: 700, marginBottom: 4 }}>Knowledge Layer</h1>
      <p style={{ color: "var(--color-text-muted)", fontSize: 14, marginBottom: 24 }}>
        NexusAI transforms your document structure into a machine-readable knowledge representation (OKF).
      </p>

      {okfFiles.length === 0 ? (
        <div style={{ textAlign: "center" }}>
          <button className="btn btn-primary" onClick={onGenerate} disabled={generating}>
            {generating ? "Generating..." : "Generate Knowledge Bundle"}
          </button>
        </div>
      ) : (
        <>
          <div className="card" style={{ display: "flex", gap: 32, marginBottom: 20 }}>
            <Stat label="Sections" value={countNodes(indexTree) - 1} />
            <Stat label="OKF files" value={okfFiles.length} />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "240px 1fr", gap: 20 }}>
            <div className="card" style={{ padding: 0, overflow: "hidden" }}>
              {okfFiles.map((f, i) => (
                <div
                  key={f.filename ?? i}
                  onClick={() => setSelected(f)}
                  style={{
                    padding: "12px 16px",
                    fontSize: 13,
                    cursor: "pointer",
                    borderBottom: "1px solid var(--color-border)",
                    background: selected === f ? "var(--color-primary-light)" : "transparent",
                  }}
                >
                  {f.filename}
                </div>
              ))}
            </div>
            <div className="card">
              {selected ? (
                <pre style={{ whiteSpace: "pre-wrap", fontSize: 13, margin: 0, fontFamily: "inherit" }}>
                  {selected.content}
                </pre>
              ) : (
                <p style={{ color: "var(--color-text-muted)", fontSize: 14 }}>Select a file to preview it.</p>
              )}
            </div>
          </div>

          <div style={{ textAlign: "center", marginTop: 24 }}>
            <button className="btn btn-primary" onClick={onContinue}>Continue to Ask Nexus</button>
          </div>
        </>
      )}
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div>
      <div style={{ fontSize: 26, fontWeight: 800 }}>{value}</div>
      <div style={{ fontSize: 12, color: "var(--color-text-muted)", fontWeight: 600 }}>{label}</div>
    </div>
  );
}

// ---------------------------------------------------------------------
// Stage 4: Ask Nexus
// ---------------------------------------------------------------------
function AskStage({ question, setQuestion, onAsk, asking, qaHistory }) {
  return (
    <div>
      <div style={{ textAlign: "center", marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>Ask anything about your document</h1>
      </div>

      <div
        className="card"
        style={{ maxWidth: 640, margin: "0 auto", display: "flex", gap: 10, padding: 10, borderRadius: "var(--radius-lg)" }}
      >
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && onAsk()}
          placeholder="What methodology does the paper use?"
          style={{ flex: 1, border: "none", outline: "none", fontSize: 14, fontFamily: "inherit", padding: "8px 12px" }}
        />
        <button className="btn btn-primary" onClick={() => onAsk()} disabled={asking}>
          {asking ? "Asking..." : "Ask Nexus"}
        </button>
      </div>

      <div style={{ maxWidth: 640, margin: "16px auto 0", display: "flex", flexWrap: "wrap", gap: 8, justifyContent: "center" }}>
        {SUGGESTED_QUESTIONS.map((q) => (
          <button key={q} className="btn btn-ghost" style={{ fontSize: 13, padding: "8px 14px" }} onClick={() => onAsk(q)}>
            {q}
          </button>
        ))}
      </div>

      <div style={{ maxWidth: 640, margin: "32px auto 0", display: "flex", flexDirection: "column", gap: 16 }}>
        {qaHistory.map((turn, i) => (
          <div key={i}>
            <div style={{ fontWeight: 600, marginBottom: 8, fontSize: 14 }}>{turn.question}</div>
            <div className="card">
              <div style={{ fontSize: 12, fontWeight: 700, color: "var(--color-primary)", marginBottom: 6 }}>NexusAI</div>
              <div style={{ fontSize: 14, whiteSpace: "pre-wrap" }}>{turn.answer}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
