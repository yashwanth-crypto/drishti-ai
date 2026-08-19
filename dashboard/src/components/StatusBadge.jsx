// "review" reuses the warning palette -- it is neither a clean pass nor a reject.
const CLASS_FOR = { review: 'warning' }

export default function StatusBadge({ status, label }) {
  return (
    <span className={`status-badge ${CLASS_FOR[status] ?? status}`}>
      <span className="status-dot" />
      {label}
    </span>
  )
}
