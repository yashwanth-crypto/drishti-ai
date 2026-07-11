import { useState } from 'react'
import StatusBadge from './StatusBadge.jsx'
import { IconScan } from './Icons.jsx'

function formatTime(iso) {
  return new Date(iso).toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

const FILTERS = [
  { id: 'all', label: 'All' },
  { id: 'fail', label: 'Failed' },
  { id: 'pass', label: 'Passed' },
]

export default function InspectionLog({ inspections }) {
  const [filter, setFilter] = useState('all')
  const passCount = inspections.filter((i) => i.pass_fail === 'pass').length
  const failCount = inspections.length - passCount
  const avgConf = inspections.reduce((a, i) => a + i.confidence, 0) / inspections.length

  const sorted = [...inspections].reverse()
    .filter((i) => filter === 'all' || i.pass_fail === filter)

  return (
    <div className="card">
      <h2 className="with-icon"><span className="ct-icon"><IconScan size={17} /></span>Quality inspection log</h2>
      <p className="card-sub">
        Every row is a real prediction from the trained MobileNetV2 classifier (Module 1), paired with the
        Hindi alert generated for it (Module 2) — run on held-out casting test images, not live camera capture.
      </p>

      <div className="insp-toolbar">
        <div className="insp-summary">
          <span><strong>{inspections.length}</strong> parts</span>
          <span className="dot-sep" />
          <span className="good-text"><strong>{passCount}</strong> passed</span>
          <span className="dot-sep" />
          <span className="crit-text"><strong>{failCount}</strong> flagged</span>
          <span className="dot-sep" />
          <span><strong>{(avgConf * 100).toFixed(1)}%</strong> avg confidence</span>
        </div>
        <div className="insp-filters">
          {FILTERS.map((f) => (
            <button
              key={f.id}
              className={`filter-chip ${filter === f.id ? 'active' : ''}`}
              onClick={() => setFilter(f.id)}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      <div className="insp-table">
        <div className="insp-header">
          <span>Time</span>
          <span></span>
          <span>Part</span>
          <span>Result</span>
          <span>Confidence</span>
          <span>Latency</span>
          <span>Alert (Hindi)</span>
        </div>
        {sorted.map((insp) => (
          <div className="insp-row" key={insp.part_id}>
            <span className="insp-time">{formatTime(insp.timestamp)}</span>
            <span className="insp-thumb">
              {insp.thumb_b64 ? (
                <img src={`data:image/jpeg;base64,${insp.thumb_b64}`} alt={insp.part_id} />
              ) : (
                <span className="insp-thumb-placeholder" />
              )}
            </span>
            <span className="insp-part">{insp.part_id}</span>
            <StatusBadge status={insp.pass_fail} label={insp.pass_fail.toUpperCase()} />
            <span className="insp-conf">{(insp.confidence * 100).toFixed(1)}%</span>
            <span className="insp-latency">{insp.inference_ms.toFixed(0)}ms</span>
            <span className="insp-alert">{insp.alert_hi}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
