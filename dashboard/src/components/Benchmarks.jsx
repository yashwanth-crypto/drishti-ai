import { Fragment } from 'react'
import { IconBars } from './Icons.jsx'

function BarComparison({ metric, lowerBetter, models }) {
  const vals = models.map((m) => Math.abs(m.value))
  const max = Math.max(...vals, 0.0001)
  const min = Math.min(...vals)
  // When every model clusters near the same value (e.g. accuracy saturated ~99%),
  // a 0→max bar makes them look identical. Zoom the bar window to the actual spread
  // so real differences are visible, while the printed numbers keep it honest.
  const spread = max - min
  const saturated = !lowerBetter && spread > 0 && spread / max < 0.03
  const floor = saturated ? min - spread * 0.6 : 0
  const scale = (v) => Math.max(((Math.abs(v) - floor) / (max - floor)) * 100, 3)
  return (
    <div className="bench-bars">
      {models.map((m) => (
        <div className={`bench-row ${m.ours ? 'ours' : ''}`} key={m.name}>
          <div className="bench-name">
            {m.name}
            {m.note && <span className="bench-note">{m.note}</span>}
          </div>
          <div className="bench-track">
            <div className="bench-fill" style={{ width: `${scale(m.value)}%` }} />
          </div>
          <div className="bench-value">
            {m.value.toFixed(m.value < 10 ? 3 : 2)}
            {m.std != null && <span className="bench-std"> ± {m.std}</span>}
          </div>
        </div>
      ))}
      <div className="bench-metric-label">
        {metric}{lowerBetter ? '  (lower is better)' : '  (higher is better)'}
        {saturated && <span className="bench-satnote"> · bars zoomed to the {min.toFixed(1)}–{max.toFixed(1)} range; backbones are statistically tied, so parameter efficiency is the real differentiator</span>}
      </div>
    </div>
  )
}

function ConfusionMatrix({ labels, matrix }) {
  const total = matrix.flat().reduce((a, b) => a + b, 0)
  const max = Math.max(...matrix.flat())
  return (
    <div className="cm-wrap">
      <div className="cm-title">Confusion matrix (held-out test, n={total})</div>
      <div className="cm-grid">
        <div className="cm-corner" />
        {labels.map((l) => <div key={l} className="cm-collabel">pred {l}</div>)}
        {matrix.map((row, i) => (
          <Fragment key={`r${i}`}>
            <div className="cm-rowlabel">true {labels[i]}</div>
            {row.map((v, j) => {
              const diag = i === j
              const intensity = v / max
              return (
                <div
                  key={`${i}-${j}`}
                  className={`cm-cell ${diag ? 'diag' : 'off'}`}
                  style={{ '--a': diag ? intensity : Math.max(intensity, v > 0 ? 0.5 : 0) }}
                >
                  {v}
                </div>
              )
            })}
          </Fragment>
        ))}
      </div>
      <div className="cm-legend">Diagonal = correct · off-diagonal = errors (green=correct, red=errors)</div>
    </div>
  )
}

export default function Benchmarks({ benchmarks }) {
  const mods = [benchmarks.module1, benchmarks.module3, benchmarks.module4]
  return (
    <div>
      <div className="card">
        <h2 className="with-icon"><span className="ct-icon"><IconBars size={17} /></span>Model benchmarks vs. baselines</h2>
        <p className="card-sub">
          Every model is measured on a held-out split and compared against baselines — evidence the models
          genuinely learn, not just fit. Numbers are measured on public datasets (proof-of-concept), not a
          live factory.
        </p>
      </div>

      {mods.map((mod) => (
        <div className="card" key={mod.title}>
          <div className="tool-card-header">
            <h2>{mod.title}</h2>
          </div>
          <BarComparison metric={mod.metric} lowerBetter={mod.lower_better} models={mod.models} />
          {mod.confusion && <ConfusionMatrix labels={mod.confusion.labels} matrix={mod.confusion.matrix} />}
        </div>
      ))}
    </div>
  )
}
