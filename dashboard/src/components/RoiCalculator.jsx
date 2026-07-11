import { useState } from 'react'
import { IconCalculator } from './Icons.jsx'

function formatInr(n) {
  return '₹' + Math.round(n).toLocaleString('en-IN')
}

export default function RoiCalculator() {
  const [baselineRejectPct, setBaselineRejectPct] = useState(8)
  const [projectedRejectPct, setProjectedRejectPct] = useState(6)
  const [partsPerMonth, setPartsPerMonth] = useState(10000)
  const [costPerReworkedPart, setCostPerReworkedPart] = useState(150)
  const [inspectorHoursSaved, setInspectorHoursSaved] = useState(80)
  const [inspectorHourlyCost, setInspectorHourlyCost] = useState(200)

  const rejectionDelta = Math.max(baselineRejectPct - projectedRejectPct, 0) / 100
  const monthlyReworkSavings = rejectionDelta * partsPerMonth * costPerReworkedPart
  const monthlyLaborSavings = inspectorHoursSaved * inspectorHourlyCost
  const totalMonthlySavings = monthlyReworkSavings + monthlyLaborSavings
  const annualSavings = totalMonthlySavings * 12

  return (
    <div>
      <div className="card">
        <h2 className="with-icon"><span className="ct-icon"><IconCalculator size={17} /></span>ROI calculator</h2>
        <p className="card-sub">
          A transparent, editable projection — not a measured result. Change any input and the totals
          recompute live so the number is never a black box.
        </p>

        <div className="roi-grid">
          <label className="roi-field">
            <span>Baseline rejection rate (%)</span>
            <input type="number" value={baselineRejectPct} min="0" max="100" step="0.5"
              onChange={(e) => setBaselineRejectPct(Number(e.target.value))} />
          </label>
          <label className="roi-field">
            <span>Projected rejection rate with Drishti-AI (%)</span>
            <input type="number" value={projectedRejectPct} min="0" max="100" step="0.5"
              onChange={(e) => setProjectedRejectPct(Number(e.target.value))} />
          </label>
          <label className="roi-field">
            <span>Parts produced per month</span>
            <input type="number" value={partsPerMonth} min="0" step="100"
              onChange={(e) => setPartsPerMonth(Number(e.target.value))} />
          </label>
          <label className="roi-field">
            <span>Cost per reworked/scrapped part (₹)</span>
            <input type="number" value={costPerReworkedPart} min="0" step="10"
              onChange={(e) => setCostPerReworkedPart(Number(e.target.value))} />
          </label>
          <label className="roi-field">
            <span>Manual inspection hours saved / month</span>
            <input type="number" value={inspectorHoursSaved} min="0" step="5"
              onChange={(e) => setInspectorHoursSaved(Number(e.target.value))} />
          </label>
          <label className="roi-field">
            <span>Inspector cost (₹ / hour)</span>
            <input type="number" value={inspectorHourlyCost} min="0" step="10"
              onChange={(e) => setInspectorHourlyCost(Number(e.target.value))} />
          </label>
        </div>
      </div>

      <div className="card">
        <h2>Projected savings</h2>
        <p className="card-sub">monthly_savings = (baseline − projected) × parts/month × cost/part + inspection hours saved × hourly cost</p>

        <div className="stat-row">
          <div className="stat-tile">
            <div className="stat-label">Rework/scrap savings</div>
            <div className="stat-value good">{formatInr(monthlyReworkSavings)}</div>
            <div className="stat-sub">per month</div>
          </div>
          <div className="stat-tile">
            <div className="stat-label">Manual inspection labor saved</div>
            <div className="stat-value good">{formatInr(monthlyLaborSavings)}</div>
            <div className="stat-sub">per month</div>
          </div>
          <div className="stat-tile">
            <div className="stat-label">Total monthly savings</div>
            <div className="stat-value good">{formatInr(totalMonthlySavings)}</div>
            <div className="stat-sub">rework + labor combined</div>
          </div>
          <div className="stat-tile">
            <div className="stat-label">Projected annual savings</div>
            <div className="stat-value good">{formatInr(annualSavings)}</div>
            <div className="stat-sub">12 × monthly total</div>
          </div>
        </div>

        <p className="roi-caveat">
          These figures are design-target projections based on the inputs above, not measured outcomes from
          a deployed installation — no real shop has run this system yet. The 20–30% rejection-rate reduction
          referenced in the project pitch is a target to validate in a real pilot, not a demonstrated result.
        </p>
      </div>
    </div>
  )
}
