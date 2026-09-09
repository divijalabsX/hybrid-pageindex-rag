import { useState } from "react";
import Logo from "../components/Logo";

/**
 * UI-only placeholder. The FastAPI backend doesn't have a working
 * login/session endpoint wired up yet (User model exists now, but no
 * /login route). Wire this up once that's ready.
 */
export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  function handleSubmit(e) {
    e.preventDefault();
    alert("Backend auth isn't wired up yet — this is a UI placeholder.");
  }

  return (
    <div className="page" style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "80vh" }}>
      <div className="card" style={{ maxWidth: 380, width: "100%", textAlign: "center" }}>
        <div style={{ display: "flex", justifyContent: "center", marginBottom: 12 }}>
          <Logo size={32} />
        </div>
        <h1 style={{ fontSize: 20, fontWeight: 700, margin: "0 0 4px" }}>Welcome to NexusAI</h1>
        <p style={{ fontSize: 13, color: "var(--color-text-muted)", margin: "0 0 24px" }}>
          Your documents. One intelligent workspace.
        </p>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 12, textAlign: "left" }}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={inputStyle}
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={inputStyle}
          />
          <button type="submit" className="btn btn-primary" style={{ marginTop: 4 }}>
            Continue
          </button>
        </form>
      </div>
    </div>
  );
}

const inputStyle = {
  width: "100%",
  padding: "11px 14px",
  borderRadius: "var(--radius-sm)",
  border: "1px solid var(--color-border)",
  fontFamily: "inherit",
  fontSize: 14,
  outline: "none",
};
