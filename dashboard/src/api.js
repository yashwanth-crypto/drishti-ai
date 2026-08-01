/**
 * Talks to the Spring Boot backend and reshapes its responses into the field
 * names the existing components already read, so the UI didn't have to be
 * rewritten when the data stopped being a static JSON import.
 *
 * Published model metrics (benchmarks, WAPE, test accuracy) stay static: they
 * are measured results from the paper, not runtime state.
 */
import staticData from './data/events.json'

const BASE = import.meta.env.VITE_API_BASE ?? '/api'

async function get(path) {
  const response = await fetch(`${BASE}${path}`)
  if (!response.ok) throw new Error(`GET ${path} failed (${response.status})`)
  return response.json()
}

export function imageUrl(id) {
  return `${BASE}/inspections/${id}/image`
}

function adaptInspection(row) {
  return {
    id: row.id,
    part_id: row.partId ?? `#${row.id}`,
    timestamp: row.timestamp,
    pass_fail: row.passFail,
    defect_type: row.defectType,
    confidence: row.confidence ?? 0,
    inference_ms: row.inferenceMs ?? 0,
    alert_hi: row.alertHi,
    // Seeded rows carry no stored file; the log falls back to a placeholder.
    image_url: row.imagePath ? imageUrl(row.id) : null,
  }
}

function adaptTool({ tool, history }) {
  return {
    tool_id: tool.toolRef,
    status: tool.status,
    seen_during_training: tool.seenDuringTraining,
    total_cycles: tool.totalCycles,
    current_cycle: tool.currentCycle,
    predicted_rul_fraction: tool.predictedRulFraction,
    actual_rul_fraction: tool.actualRulFraction,
    history: history.map((h) => ({
      cycle: h.cycle,
      predicted_rul: h.predictedRul,
      actual_rul: h.actualRul,
    })),
  }
}

function adaptCategory(cat) {
  const history = cat.history.map((p) => ({ week: p.week, actual_demand: p.actualDemand }))
  const mean = history.length
    ? history.reduce((a, p) => a + p.actual_demand, 0) / history.length
    : 0
  return {
    category: cat.category,
    wape_pct: cat.wapePct ?? 0,
    mean_weekly_demand: mean,
    history,
    forecast: cat.forecast.map((p) => ({
      week: p.week,
      predicted_demand: p.predictedDemand,
      lower: p.lowerP10,
      upper: p.upperP90,
    })),
  }
}

/** Everything the dashboard renders, in one round of requests. */
export async function loadDashboard() {
  const [inspectionRows, kpis, toolRows, categoryRows] = await Promise.all([
    get('/inspections'),
    get('/kpis'),
    get('/maintenance/tools'),
    get('/forecast/categories'),
  ])

  const inspections = inspectionRows.map(adaptInspection).reverse()
  const tools = toolRows.map(adaptTool)
  const categories = categoryRows.map(adaptCategory).filter((c) => c.forecast.length > 0)
  const staticForecasting = staticData.forecasting

  return {
    inspections,
    maintenance: { tools },
    benchmarks: staticData.benchmarks,
    forecasting: {
      ...staticForecasting,
      categories,
    },
    kpis: {
      total_inspections: kpis.totalInspections,
      pass_count: kpis.passCount,
      fail_count: kpis.failCount,
      pass_rate: kpis.passRate,
      avg_inference_ms: kpis.avgInferenceMs,
      tools_monitored: tools.length,
      active_maintenance_alerts: tools.filter((t) => t.status !== 'ok').length,
      // Measured once on the held-out sets, not recomputed per request.
      module1_test_accuracy: staticData.kpis.module1_test_accuracy,
      demand_forecast_wape_pct: staticData.kpis.demand_forecast_wape_pct,
    },
  }
}

/** Runs one image through the live model and stores the result. */
export async function inspectImage(file, partId) {
  const body = new FormData()
  body.append('image', file)
  const query = partId ? `?partId=${encodeURIComponent(partId)}` : ''

  const response = await fetch(`${BASE}/inspections${query}`, { method: 'POST', body })
  if (!response.ok) {
    const detail = await response.text().catch(() => '')
    throw new Error(detail || `Inspection failed (${response.status})`)
  }
  return adaptInspection(await response.json())
}
