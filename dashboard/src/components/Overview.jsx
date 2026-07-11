import StatusBadge from './StatusBadge.jsx'
import AnimatedNumber from './AnimatedNumber.jsx'
import { IconLayers, IconTarget, IconBolt, IconAlert, IconActivity, IconScan, IconWrench } from './Icons.jsx'

function formatTime(iso) {
  return new Date(iso).toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

export default function Overview({ data }) {
  const { kpis, inspections, maintenance, forecasting } = data
  const recentInspections = [...inspections].slice(-5).reverse()
  const alertTools = maintenance.tools.filter((t) => t.status !== 'ok')

  return (
    <div>
      <div className="stat-row">
        <div className="stat-tile">
          <div className="stat-tophead">
            <span className="stat-label">Total inspections</span>
            <span className="stat-icon"><IconLayers size={17} /></span>
          </div>
          <div className="stat-value"><AnimatedNumber value={kpis.total_inspections} /></div>
          <div className="stat-sub">{kpis.fail_count} flagged, {kpis.pass_count} passed</div>
        </div>
        <div className="stat-tile">
          <div className="stat-tophead">
            <span className="stat-label">Module 1 test accuracy</span>
            <span className="stat-icon good"><IconTarget size={17} /></span>
          </div>
          <div className="stat-value good">
            <AnimatedNumber value={kpis.module1_test_accuracy * 100} format={(v) => `${v.toFixed(1)}%`} />
          </div>
          <div className="stat-sub">held-out casting test set</div>
        </div>
        <div className="stat-tile">
          <div className="stat-tophead">
            <span className="stat-label">Avg inference time</span>
            <span className="stat-icon"><IconBolt size={17} /></span>
          </div>
          <div className="stat-value">
            <AnimatedNumber value={kpis.avg_inference_ms} format={(v) => `${v.toFixed(0)}ms`} />
          </div>
          <div className="stat-sub">camera-to-alert, target was &lt;2s</div>
        </div>
        <div className="stat-tile">
          <div className="stat-tophead">
            <span className="stat-label">Active maintenance alerts</span>
            <span className={`stat-icon ${kpis.active_maintenance_alerts > 0 ? 'warn' : 'good'}`}><IconAlert size={17} /></span>
          </div>
          <div className={`stat-value ${kpis.active_maintenance_alerts > 0 ? '' : 'good'}`}>
            <AnimatedNumber value={kpis.active_maintenance_alerts} /> / {kpis.tools_monitored}
          </div>
          <div className="stat-sub">tools monitored, wear-based RUL model</div>
        </div>
        <div className="stat-tile">
          <div className="stat-tophead">
            <span className="stat-label">Demand forecast WAPE</span>
            <span className="stat-icon"><IconActivity size={17} /></span>
          </div>
          <div className="stat-value">
            <AnimatedNumber value={kpis.demand_forecast_wape_pct} format={(v) => `${v.toFixed(1)}%`} />
          </div>
          <div className="stat-sub">{forecasting.categories_modeled} categories, held-out weeks</div>
        </div>
      </div>

      <div className="card">
        <h2 className="with-icon"><span className="ct-icon"><IconScan size={17} /></span>Recent inspections</h2>
        <p className="card-sub">Module 1 (CV defect detection) → Module 2 (Hindi alert), most recent first</p>
        <div className="overview-list">
          {recentInspections.map((insp) => (
            <div className="overview-row" key={insp.part_id}>
              <span className="overview-time">{formatTime(insp.timestamp)}</span>
              <span className="overview-part">{insp.part_id}</span>
              <StatusBadge status={insp.pass_fail} label={insp.pass_fail.toUpperCase()} />
              <span className="overview-conf">{(insp.confidence * 100).toFixed(1)}%</span>
              <span className="overview-alert">{insp.alert_hi}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <h2 className="with-icon"><span className="ct-icon"><IconWrench size={17} /></span>Tool wear status</h2>
        <p className="card-sub">Module 3 (predictive maintenance) — {alertTools.length} of {maintenance.tools.length} tools need attention</p>
        <div className="overview-list">
          {maintenance.tools.map((tool) => (
            <div className="tool-status-row" key={tool.tool_id}>
              <span className="overview-part">Tool {tool.tool_id}</span>
              <StatusBadge
                status={tool.status}
                label={tool.status === 'ok' ? 'HEALTHY' : tool.status.toUpperCase()}
              />
              <span className="overview-conf">
                cycle {tool.current_cycle} of ~{tool.total_cycles}
              </span>
              <span className="overview-alert">
                Predicted RUL: {(tool.predicted_rul_fraction * 100).toFixed(0)}%
                {!tool.seen_during_training && ' · unseen tool (held-out test)'}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
