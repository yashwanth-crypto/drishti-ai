import { useRef, useState, useId } from 'react'

const W = 720
const H = 180
const margin = { top: 14, right: 18, bottom: 26, left: 60 }
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

function fmt(y) {
  const a = Math.abs(y)
  if (a >= 1_000_000) return `${(y / 1_000_000).toFixed(1)}M`
  if (a >= 1_000) return `${(y / 1_000).toFixed(0)}K`
  return `${Math.round(y)}`
}

export default function ForecastChart({ history, forecast }) {
  const gid = useId().replace(/:/g, '')
  const wrapRef = useRef(null)
  const [hover, setHover] = useState(null)

  const points = [
    ...history.map((h, i) => ({ x: i, y: h.actual_demand, week: h.week, kind: 'actual' })),
    ...forecast.map((f, i) => ({
      x: history.length + i, y: f.predicted_demand, lower: f.lower, upper: f.upper,
      week: f.week, kind: 'forecast',
    })),
  ]
  const xMax = points.length - 1
  const allY = [...points.map((p) => p.y), ...forecast.flatMap((f) => [f.lower, f.upper])]
  const yMin = Math.min(0, ...allY)
  const yMax = Math.max(...allY) * 1.08 || 1

  const xScale = (x) => margin.left + (x / Math.max(xMax, 1)) * plotW
  const yScale = (y) => margin.top + plotH - ((y - yMin) / Math.max(yMax - yMin, 1)) * plotH

  const histPx = points.filter((p) => p.kind === 'actual').map((p) => ({ x: xScale(p.x), y: yScale(p.y) }))
  const lastHist = histPx[histPx.length - 1]
  const fcPx = points.filter((p) => p.kind === 'forecast').map((p) => ({ x: xScale(p.x), y: yScale(p.y) }))
  const fcLine = lastHist ? [lastHist, ...fcPx] : fcPx

  const upperPx = [lastHist, ...forecast.map((f, i) => ({ x: xScale(history.length + i), y: yScale(f.upper) }))]
  const lowerPx = [lastHist, ...forecast.map((f, i) => ({ x: xScale(history.length + i), y: yScale(f.lower) }))]
  const bandPath = `${smoothPath(upperPx)} L ${lowerPx[lowerPx.length - 1].x} ${lowerPx[lowerPx.length - 1].y} ${smoothPath([...lowerPx].reverse()).replace(/^M/, 'L')} Z`

  const areaPath = `${smoothPath(histPx)} L ${lastHist.x} ${yScale(yMin)} L ${histPx[0].x} ${yScale(yMin)} Z`

  const onMove = (e) => {
    const rect = wrapRef.current.getBoundingClientRect()
    const frac = ((e.clientX - rect.left) / rect.width * W - margin.left) / plotW
    const idx = Math.max(0, Math.min(xMax, Math.round(frac * xMax)))
    setHover(idx)
  }

  const hp = hover != null ? points[hover] : null

  return (
    <div className="chart-wrap" ref={wrapRef} onMouseMove={onMove} onMouseLeave={() => setHover(null)}>
      {hp && (
        <div className="chart-tooltip" style={{ left: `${(xScale(hp.x) / W) * 100}%`, top: `${(yScale(hp.y) / H) * 100}%` }}>
          <div className="tt-label">{hp.week}{hp.kind === 'forecast' ? ' · forecast' : ''}</div>
          <div>{fmt(hp.y)} units</div>
          {hp.kind === 'forecast' && <div className="tt-label">P10–P90: {fmt(hp.lower)}–{fmt(hp.upper)}</div>}
        </div>
      )}
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ display: 'block' }}>
        <defs>
          <linearGradient id={`area${gid}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="var(--series-1)" stopOpacity="0.28" />
            <stop offset="1" stopColor="var(--series-1)" stopOpacity="0.01" />
          </linearGradient>
        </defs>

        {[0, 0.25, 0.5, 0.75, 1].map((f) => (
          <line key={f} x1={margin.left} y1={margin.top + plotH * f} x2={margin.left + plotW} y2={margin.top + plotH * f}
            stroke="var(--gridline)" strokeWidth="1" />
        ))}
        <text x={margin.left - 10} y={yScale(yMax) + 4} textAnchor="end" fontSize="10" fill="var(--text-muted)">{fmt(yMax)}</text>
        <text x={margin.left - 10} y={yScale(yMin) + 4} textAnchor="end" fontSize="10" fill="var(--text-muted)">{fmt(yMin)}</text>

        {/* forecast region shading + confidence band */}
        <rect x={lastHist.x} y={margin.top} width={margin.left + plotW - lastHist.x} height={plotH}
          fill="var(--series-3)" opacity="0.06" />
        <path d={bandPath} fill="var(--series-3)" opacity="0.16" stroke="none" />

        {/* history area + line */}
        <path d={areaPath} fill={`url(#area${gid})`} stroke="none" />
        <path d={smoothPath(histPx)} fill="none" stroke="var(--series-1)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />

        {/* forecast line */}
        <path d={smoothPath(fcLine)} fill="none" stroke="var(--series-3)" strokeWidth="2.4" strokeDasharray="6,5" strokeLinecap="round" strokeLinejoin="round" />
        {fcPx.map((p, i) => (
          <circle key={i} cx={p.x} cy={p.y} r="3.5" fill="var(--series-3)" stroke="var(--surface-1)" strokeWidth="1.5" />
        ))}

        {/* hover guide */}
        {hp && (
          <>
            <line x1={xScale(hp.x)} y1={margin.top} x2={xScale(hp.x)} y2={margin.top + plotH} stroke="var(--baseline)" strokeWidth="1" strokeDasharray="3,3" />
            <circle cx={xScale(hp.x)} cy={yScale(hp.y)} r="4.5" fill={hp.kind === 'forecast' ? 'var(--series-3)' : 'var(--series-1)'} stroke="var(--surface-1)" strokeWidth="2" />
          </>
        )}

        <line x1={margin.left} y1={margin.top + plotH} x2={margin.left + plotW} y2={margin.top + plotH} stroke="var(--baseline)" strokeWidth="1" />
        <text x={margin.left} y={H - 4} fontSize="10" fill="var(--text-muted)">{history[0]?.week}</text>
        <text x={margin.left + plotW} y={H - 4} textAnchor="end" fontSize="10" fill="var(--text-muted)">{forecast[forecast.length - 1]?.week} (forecast)</text>
      </svg>
    </div>
  )
}
