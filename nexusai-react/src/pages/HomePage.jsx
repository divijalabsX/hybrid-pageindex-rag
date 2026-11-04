import { useNavigate } from "react-router-dom";

export default function HomePage() {
  const navigate = useNavigate();

  return (
    <div className="page">
      {/* Hero Section */}
      <div
        style={{
          textAlign: "center",
          padding: "80px 0 60px",
        }}
      >
        <h1
          style={{
            fontSize: 36,
            fontWeight: 800,
            margin: "0 0 12px",
            letterSpacing: "-0.02em",
          }}
        >
          Turn your documents into answers.
        </h1>

        <p
          style={{
            fontSize: 16,
            color: "var(--color-text-muted)",
            margin: "0 0 28px",
          }}
        >
          Upload a document, build its intelligence layer,
          and ask questions in natural language.
        </p>

        <button
          className="btn btn-primary"
          style={{
            padding: "14px 28px",
            fontSize: 15,
          }}
          onClick={() =>
            navigate("/workspace", {
              state: { fresh: true },
            })
          }
        >
          + Upload a Document
        </button>

        <div
          style={{
            marginTop: 12,
            fontSize: 13,
            color: "var(--color-text-muted)",
          }}
        >
          PDF • DOCX • TXT • More coming soon
        </div>
      </div>

      {/* How It Works */}
      <div
        style={{
          marginTop: 60,
          textAlign: "center",
        }}
      >
        <h2
          style={{
            fontSize: 14,
            fontWeight: 700,
            letterSpacing: "0.06em",
            color: "var(--color-text-muted)",
            marginBottom: 20,
          }}
        >
          HOW NEXUSAI WORKS
        </h2>

        <div
          style={{
            display: "flex",
            justifyContent: "center",
            gap: 10,
            fontSize: 15,
            fontWeight: 600,
            color: "var(--color-text-muted)",
            flexWrap: "wrap",
          }}
        >
          <span>Upload</span>
          <span>→</span>
          <span>Index</span>
          <span>→</span>
          <span>Knowledge</span>
          <span>→</span>
          <span>Ask</span>
        </div>
      </div>
    </div>
  );
}