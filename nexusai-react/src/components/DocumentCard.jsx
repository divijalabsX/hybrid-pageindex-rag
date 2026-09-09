import { useNavigate } from "react-router-dom";

export default function DocumentCard({ filename, totalPages, totalWords, indexed, knowledgeReady }) {
  const navigate = useNavigate();

  return (
    <div className="card" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 22 }}>📄</span>
          <strong style={{ fontSize: 16 }}>{filename}</strong>
        </div>
      </div>

      <div style={{ fontSize: 13, color: "var(--color-text-muted)" }}>
        {totalPages != null && `${totalPages} pages`}
        {totalPages != null && totalWords != null && " • "}
        {totalWords != null && `${totalWords.toLocaleString()} words`}
      </div>

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <span className={`status-pill ${indexed ? "done" : "idle"}`}>
          {indexed ? "● Indexed" : "○ Not indexed"}
        </span>
        <span className={`status-pill ${knowledgeReady ? "done" : "idle"}`}>
          {knowledgeReady ? "● Knowledge ready" : "○ Knowledge pending"}
        </span>
      </div>

      <button className="btn btn-primary" style={{ alignSelf: "flex-start" }} onClick={() => navigate("/workspace")}>
        Open Workspace
      </button>
    </div>
  );
}
