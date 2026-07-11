import StatusBadge from './StatusBadge.jsx'
import ForecastChart from './ForecastChart.jsx'
import AnimatedNumber from './AnimatedNumber.jsx'
import { IconTrend } from './Icons.jsx'

function statusFor(wapePct) {
  if (wapePct < 30) return { cls: 'ok', label: 'RELIABLE' }
  if (wapePct < 70) return { cls: 'warning', label: 'MODERATE' }
  return { cls: 'critical', label: 'LOW CONFIDENCE' }
}

function fmtUnits(n) {
  if (Math.abs(n) >= 1000) return `${(n / 1000).toFixed(1)}K`
  return `${Math.round(n)}`
}

export default function InventoryForecast({ forecasting }) {
  const { model_metrics: metrics, cv, categories, categories_modeled, test_weeks, cutoff_date } = forecasting

  return (
    <div>
      <div className="card">
        <h2 className="with-icon"><span className="ct-icon"><IconTrend size={17} /></span>Demand forecasting</h2>
        <p className="card-sub">
          XGBoost regressor forecasting next-week order demand per product category (Module 4) — trained on
          the Kaggle historical product-demand dataset, aggregated from ~1.05M individual orders across 2,160
          products into weekly totals for {categories_modeled} categories with enough history to model. Evaluated
          on the {test_weeks} weeks after {cutoff_date}, which the model never trained on. Each forecast carries
          an 80% prediction interval (P10–P90) from paired quantile models.
        </p>
        <div className="stat-row" style={{ marginBottom: 0 }}>
          <div className="stat-tile">
            <div className="stat-label">Held-out WAPE</div>
            <div className="stat-value"><AnimatedNumber value={metrics.wape_pct} format={(v) => `${v.toFixed(1)}%`} /></div>
            <div className="stat-sub">weighted % error, future weeks</div>
          </div>
          <div className="stat-tile">
            <div className="stat-label">Cross-val WAPE</div>
            <div className="stat-value">
              {cv ? <AnimatedNumber value={cv.mean_wape_pct} format={(v) => `${v.toFixed(1)}%`} /> : '—'}
            </div>
            <div className="stat-sub">3-fold expanding window mean</div>
          </div>
          <div className="stat-tile">
            <div className="stat-label">R²</div>
            <div className="stat-value good"><AnimatedNumber value={metrics.r2} format={(v) => v.toFixed(3)} /></div>
            <div className="stat-sub">held-out weeks</div>
          </div>
          <div className="stat-tile">
            <div className="stat-label">Interval coverage</div>
            <div className="stat-value"><AnimatedNumber value={metrics.interval_coverage_pct} format={(v) => `${v.toFixed(0)}%`} /></div>
            <div className="stat-sub">actuals inside P10–P90 (ideal ~80%)</div>
          </div>
        </div>
        <p className="roi-caveat" style={{ marginTop: 16 }}>
          Accuracy varies a lot by category volume — see the WAPE badge on each card below. Low-volume
          categories (tens of units/week) are inherently harder to forecast than high-volume ones and are shown
          here deliberately, not hidden. The dataset's final recorded week also looks truncated across most
          categories (a sharp drop-off, not a real demand collapse), which can distort the first forecast point.
        </p>
      </div>

      {categories.map((cat) => {
        const status = statusFor(cat.wape_pct)
        const next = cat.forecast[0]
        return (
          <div className="card" key={cat.category}>
            <div className="tool-card-header">
              <div>
                <h2>{cat.category}</h2>
                <p className="card-sub" style={{ marginBottom: 0 }}>
                  ~{fmtUnits(cat.mean_weekly_demand)} units/week average · next-week forecast{' '}
                  <strong style={{ color: 'var(--text-primary)' }}>{fmtUnits(next.predicted_demand)}</strong>{' '}
                  (P10–P90 {fmtUnits(next.lower)}–{fmtUnits(next.upper)})
                </p>
              </div>
              <StatusBadge status={status.cls} label={`${status.label} · ${cat.wape_pct.toFixed(0)}% WAPE`} />
            </div>

            <div className="chart-frame">
              <div className="tool-chart-legend">
                <span className="legend-item"><span className="legend-swatch series-1" />Actual demand</span>
                <span className="legend-item"><span className="legend-swatch series-3" />Forecast</span>
                <span className="legend-item"><span className="legend-swatch band" />80% interval</span>
              </div>
              <ForecastChart history={cat.history} forecast={cat.forecast} />
            </div>
          </div>
        )
      })}
    </div>
  )
}
