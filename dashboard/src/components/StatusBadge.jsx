export default function StatusBadge({ status, label }) {
  return (
    <span className={`status-badge ${status}`}>
      <span className="status-dot" />
      {label}
    </span>
  )
}
