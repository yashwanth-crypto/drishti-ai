import { useRef, useState, useId } from 'react'

const WEAR_ALERT_THRESHOLD = 0.2
const W = 720
const H = 175
const margin = { top: 12, right: 18, bottom: 26, left: 40 }
const plotW = W - margin.left - margin.right
const plotH = H - margin.top - margin.bottom

function smoothPath(points) {
  if (points.length < 2) return points.map((p, i) => `${i ? 'L' : 'M'} ${p.x} ${p.y}`).join(' ')
  let d = `M ${points[0].x} ${points[0].y}`
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[i - 1] || points[i]
    const p1 = points[i]
    const p2 = points[i + 1]
    const p3 = points[i + 2] || p2
    const c1x = p1.x + (p2.x - p0.x) / 6
    const c1y = p1.y + (p2.y - p0.y) / 6
    const c2x = p2.x - (p3.x - p1.x) / 6
    const c2y = p2.y - (p3.y - p1.y) / 6
    d += ` C ${c1x} ${c1y} ${c2x} ${c2y} ${p2.x} ${p2.y}`
  }
  return d
}

export default function RulChart({ history }) {
  const gid = useId().replace(/:/g, '')
  const wrapRef = useRef(null)
  const [hover, setHover] = useState(null)

  const cycles = history.map((h) => h.cycle)
  const xMin = Math.min(...cycles)
  const xMax = Math.max(...cycles)
  const xScale = (x) => margin.left + ((x - xMin) / Math.max(xMax - xMin, 1)) * plotW
  const yScale = (y) => margin.top + plotH - y * plotH

  const actualPx = history.map((h) => ({ x: xScale(h.cycle), y: yScale(h.actual_rul) }))
  const predPx = history.map((h) => ({ x: xScale(h.cycle), y: yScale(h.predicted_rul) }))
  const areaPath = `${smoothPath(actualPx)} L ${actualPx[actualPx.length - 1].x} ${yScale(0)} L ${actualPx[0].x} ${yScale(0)} Z`

  const thresholdY = yScale(WEAR_ALERT_THRESHOLD)

  const onMove = (e) => {
    const rect = wrapRef.current.getBoundingClientRect()
    const frac = ((e.clientX - rect.left) / rect.width * W - margin.left) / plotW
    const idx = Math.max(0, Math.min(history.length - 1, Math.round(frac * (history.length - 1))))
    setHover(idx)
  }

  const hp = hover != null ? history[hover] : null

  return (
    <div className="chart-wrap" ref={wrapRef} onMouseMove={onMove} onMouseLeave={() => setHover(null)}>
      {hp && (
        <div className="chart-tooltip" style={{ left: `${(xScale(hp.cycle) / W) * 100}%`, top: `${(yScale(Math.max(hp.actual_rul, hp.predicted_rul)) / H) * 100}%` }}>
          <div className="tt-label">cycle {hp.cycle}</div>
          <div>actual {(hp.actual_rul * 100).toFixed(0)}% · pred {(hp.predicted_rul * 100).toFixed(0)}%</div>
        </div>
      )}
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ display: 'block' }}>
        <defs>
          <linearGradient id={`rul${gid}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="var(--series-2)" stopOpacity="0.26" />
            <stop offset="1" stopColor="var(--series-2)" stopOpacity="0.01" />
          </linearGradient>
        </defs>

        {[0, 0.25, 0.5, 0.75, 1].map((frac) => (
          <line key={frac} x1={margin.left} y1={yScale(frac)} x2={margin.left + plotW} y2={yScale(frac)} stroke="var(--gridline)" strokeWidth="1" />
        ))}
        <text x={margin.left - 8} y={yScale(1) + 4} textAnchor="end" fontSize="10" fill="var(--text-muted)">100%</text>
        <text x={margin.left - 8} y={yScale(0) + 4} textAnchor="end" fontSize="10" fill="var(--text-muted)">0%</text>

        <line x1={margin.left} y1={thresholdY} x2={margin.left + plotW} y2={thresholdY} stroke="var(--critical)" strokeWidth="1" strokeDasharray="3,3" opacity="0.6" />
        <text x={margin.left + plotW} y={thresholdY - 5} textAnchor="end" fontSize="9.5" fill="var(--critical)">alert threshold</text>

        <path d={areaPath} fill={`url(#rul${gid})`} stroke="none" />
        <path d={smoothPath(actualPx)} fill="none" stroke="var(--series-2)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
        <path d={smoothPath(predPx)} fill="none" stroke="var(--series-1)" strokeWidth="2.4" strokeDasharray="6,4" strokeLinecap="round" strokeLinejoin="round" />

        {hp && (
          <>
            <line x1={xScale(hp.cycle)} y1={margin.top} x2={xScale(hp.cycle)} y2={margin.top + plotH} stroke="var(--baseline)" strokeWidth="1" strokeDasharray="3,3" />
            <circle cx={xScale(hp.cycle)} cy={yScale(hp.predicted_rul)} r="4" fill="var(--series-1)" stroke="var(--surface-1)" strokeWidth="2" />
            <circle cx={xScale(hp.cycle)} cy={yScale(hp.actual_rul)} r="4" fill="var(--series-2)" stroke="var(--surface-1)" strokeWidth="2" />
          </>
        )}

        <line x1={margin.left} y1={margin.top + plotH} x2={margin.left + plotW} y2={margin.top + plotH} stroke="var(--baseline)" strokeWidth="1" />
        <text x={margin.left} y={H - 4} fontSize="10" fill="var(--text-muted)">cycle {xMin}</text>
        <text x={margin.left + plotW} y={H - 4} textAnchor="end" fontSize="10" fill="var(--text-muted)">cycle {xMax} (now)</text>
      </svg>
    </div>
  )
}
