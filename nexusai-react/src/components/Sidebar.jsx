import { NavLink, useNavigate } from "react-router-dom";
import Logo from "./Logo";

const links = [
  { to: "/", label: "Home", end: true },
  { to: "/workspace", label: "Workspace" },
  { to: "/documents", label: "Documents" },
];

export default function Sidebar() {
  const navigate = useNavigate();

  return (
    <aside
      style={{
        width: 232,
        borderRight: "1px solid var(--color-border)",
        background: "var(--color-surface)",
        padding: "22px 16px",
        display: "flex",
        flexDirection: "column",
        gap: 4,
        position: "sticky",
        top: 0,
        height: "100vh",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "0 8px 24px" }}>
        <Logo size={24} />
        <span style={{ fontWeight: 800, fontSize: 17 }}>NexusAI</span>
      </div>

      <button
        className="btn btn-primary"
        style={{ marginBottom: 20, justifyContent: "flex-start" }}
        onClick={() => navigate("/workspace", { state: { fresh: true } })}
      >
        + New Document
      </button>

      {links.map((link) => (
        <NavLink
          key={link.to}
          to={link.to}
          end={link.end}
          style={({ isActive }) => ({
            display: "flex",
            alignItems: "center",
            padding: "10px 12px",
            borderRadius: "var(--radius-sm)",
            fontSize: 14,
            fontWeight: 600,
            color: isActive ? "var(--color-primary-dark)" : "var(--color-text-muted)",
            background: isActive ? "var(--color-primary-light)" : "transparent",
          })}
        >
          {link.label}
        </NavLink>
      ))}
    </aside>
  );
}
