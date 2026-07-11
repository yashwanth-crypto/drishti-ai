import StatusBadge from './StatusBadge.jsx'
import RulChart from './RulChart.jsx'
import { IconWrench } from './Icons.jsx'

export default function MaintenancePanel({ tools }) {
  return (
    <div>
      <div className="card">
        <h2 className="with-icon"><span className="ct-icon"><IconWrench size={17} /></span>Predictive maintenance</h2>
        <p className="card-sub">
          XGBoost regressor predicting remaining tool life from vibration + current sensor features
          (Module 3) — trained on the Piecuch &amp; Żabiński 2025 CNC milling dataset, split by physical
          tool so unseen-tool numbers below reflect real generalization, not memorized history. Each
          tool's chart is a <strong>simulated replay</strong> of its recorded sensor readings, not a live feed.
        </p>
      </div>

      {tools.map((tool) => (
        <div className="card" key={tool.tool_id}>
          <div className="tool-card-header">
            <div>
              <h2>Tool {tool.tool_id}</h2>
              <p className="card-sub" style={{ marginBottom: 0 }}>
                Cycle {tool.current_cycle} of ~{tool.total_cycles} total lifetime cycles
                {!tool.seen_during_training && ' · held out from training (unseen tool)'}
              </p>
            </div>
            <StatusBadge
              status={tool.status}
              label={tool.status === 'ok' ? 'HEALTHY' : tool.status === 'warning' ? 'MONITOR' : 'REPLACE SOON'}
            />
          </div>

          <div className="chart-frame">
            <div className="tool-chart-legend">
              <span className="legend-item"><span className="legend-swatch series-2" />Actual RUL</span>
              <span className="legend-item"><span className="legend-swatch series-1" />Predicted RUL</span>
            </div>
            <RulChart history={tool.history} />
          </div>
        </div>
      ))}
    </div>
  )
}
