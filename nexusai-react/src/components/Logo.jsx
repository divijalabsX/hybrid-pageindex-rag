export default function Logo({ size = 28 }) {
  // A geometric "N" traced through connected nodes rather than a
  // literal letterform or a robot-head AI icon.
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none">
      <line x1="6" y1="26" x2="6" y2="6" className="node-line" />
      <line x1="6" y1="6" x2="26" y2="26" className="node-line" />
      <line x1="26" y1="26" x2="26" y2="6" className="node-line" />
      <circle cx="6" cy="6" r="3" className="node-dot" />
      <circle cx="6" cy="26" r="3" className="node-dot" />
      <circle cx="26" cy="6" r="3" className="node-dot" />
      <circle cx="26" cy="26" r="3" className="node-dot" />
    </svg>
  );
}
