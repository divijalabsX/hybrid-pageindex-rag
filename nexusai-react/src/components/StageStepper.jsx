const STAGES = [
  { key: "upload", label: "Upload" },
  { key: "index", label: "Build Index" },
  { key: "knowledge", label: "Knowledge" },
  { key: "ask", label: "Ask" },
];

/**
 * `completed` is the highest stage key the user has finished; `active` is
 * the one currently shown. Stages before `active` render as done (check),
 * the active one is highlighted, later ones are dimmed.
 */
export default function StageStepper({ active, completed = [] }) {
  return (
    <div className="stepper">
      {STAGES.map((stage, i) => {
        const isDone = completed.includes(stage.key);
        const isActive = stage.key === active;
        return (
          <div key={stage.key} style={{ display: "flex", alignItems: "center" }}>
            <div className={`stepper-step ${isDone ? "done" : ""} ${isActive ? "active" : ""}`}>
              <span className="stepper-dot">{isDone ? "✓" : i + 1}</span>
              <span>{stage.label}</span>
            </div>
            {i < STAGES.length - 1 && (
              <div className={`stepper-line ${isDone ? "done" : ""}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}
