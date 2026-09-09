import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getWorkspaceStatus } from "../api/api";
import DocumentCard from "../components/DocumentCard";

export default function HomePage() {
  const navigate = useNavigate();
  const [status, setStatus] = useState(null); // null while loading
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getWorkspaceStatus()
      .then(setStatus)
      .finally(() => setLoading(false));
  }, []);

  const hasDocument = !!status?.index;

  return (
    <div className="page">
      {/* --- Hero --- */}
      <div style={{ textAlign: "center", padding: "56px 0 48px" }}>
        <h1 style={{ fontSize: 36, fontWeight: 800, margin: "0 0 12px", letterSpacing: "-0.02em" }}>
          Turn your documents into answers.
        </h1>
        <p style={{ fontSize: 16, color: "var(--color-text-muted)", margin: "0 0 28px" }}>
          Upload a document, build its intelligence layer, and ask questions in natural language.
        </p>
        <button
          className="btn btn-primary"
          style={{ padding: "14px 28px", fontSize: 15 }}
          onClick={() => navigate("/workspace", { state: { fresh: true } })}
        >
          + Upload a Document
        </button>
        <div style={{ marginTop: 12, fontSize: 13, color: "var(--color-text-muted)" }}>
          PDF • DOCX • TXT • more coming soon
        </div>
      </div>

      {/* --- Workspace section --- */}
      <div>
        <h2 style={{ fontSize: 14, fontWeight: 700, letterSpacing: "0.06em", color: "var(--color-text-muted)", marginBottom: 16 }}>
          YOUR WORKSPACE
        </h2>

        {loading ? (
          <div className="card">Loading...</div>
        ) : hasDocument ? (
          <DocumentCard
            filename={status.index.title}
            indexed={!!status.index}
            knowledgeReady={status.okfFiles.length > 0}
          />
        ) : (
          <div className="card" style={{ textAlign: "center", padding: "40px 20px", color: "var(--color-text-muted)" }}>
            No documents yet — upload your first one to get started.
          </div>
        )}
      </div>

      {/* --- How it works --- */}
      <div style={{ marginTop: 56, textAlign: "center" }}>
        <h2 style={{ fontSize: 14, fontWeight: 700, letterSpacing: "0.06em", color: "var(--color-text-muted)", marginBottom: 20 }}>
          HOW NEXUSAI WORKS
        </h2>
        <div style={{ display: "flex", justifyContent: "center", gap: 8, fontSize: 15, fontWeight: 600, color: "var(--color-text-muted)" }}>
          <span>Upload</span><span>→</span><span>Index</span><span>→</span><span>Knowledge</span><span>→</span><span>Ask</span>
        </div>
      </div>
    </div>
  );
}
