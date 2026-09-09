import { useEffect, useState } from "react";
import { getWorkspaceStatus } from "../api/api";
import DocumentCard from "../components/DocumentCard";

/**
 * The backend currently tracks a single "current document" via in-memory
 * globals (no persisted multi-document history yet). So for now this page
 * shows that one document. When the team adds real document persistence
 * (the new Document/DocumentChunk models look like a step in that
 * direction), this is the page to wire up to a real list endpoint.
 */
export default function DocumentsPage() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getWorkspaceStatus().then(setStatus).finally(() => setLoading(false));
  }, []);

  const hasDocument = !!status?.index;

  return (
    <div className="page">
      <div className="page-header" style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, margin: "0 0 4px" }}>Your Documents</h1>
        <p style={{ color: "var(--color-text-muted)", fontSize: 14, margin: 0 }}>
          Everything you've uploaded and processed.
        </p>
      </div>

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
          No documents yet.
        </div>
      )}
    </div>
  );
}
