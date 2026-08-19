/**
 * Demo mode: the dashboard served from a static host, with no backend behind it.
 *
 * The published build sits on GitHub Pages where nothing answers /api. Rather
 * than ship a second cut of the app, the same bundle probes for a backend once
 * at startup and falls back to the recorded results in events.json when there
 * isn't one. Everything a visitor sees is then real measured output -- just
 * recorded rather than computed on the spot, which the banner says plainly.
 */
import staticData from './data/events.json'

const BASE = import.meta.env.VITE_API_BASE ?? '/api'

let demoMode = null   // null = not probed yet

export function isDemoMode() {
  return demoMode === true
}

/**
 * A 401 is the *good* answer here: it means a backend is there and asking for
 * credentials. A network error, or a static host handing back its 404 page,
 * means there is nothing to log into.
 */
export async function probeBackend() {
  try {
    const response = await fetch(`${BASE}/kpis`, { method: 'GET' })
    demoMode = !(response.status === 401 || response.status === 403 || response.ok)
  } catch {
    demoMode = true
  }
  return demoMode
}

/** Shapes events.json into what loadDashboard() returns, so App.jsx sees no difference. */
export function demoDashboard() {
  const inspections = staticData.inspections.map((row, i) => ({
    id: i + 1,
    part_id: row.part_id,
    timestamp: row.timestamp,
    pass_fail: row.pass_fail,
    defect_type: row.defect_type,
    confidence: row.confidence ?? 0,
    inference_ms: row.inference_ms ?? 0,
    alert_hi: row.alert_hi,
    // The recorded thumbnails travel inside events.json, so they work with no
    // server to fetch them from.
    image_url: row.thumb_b64 ? `data:image/jpeg;base64,${row.thumb_b64}` : null,
    recognised: true,
    operator_verdict: null,
    was_correct: null,
    feedback_by: null,
  })).reverse()

  const tools = staticData.maintenance.tools

  return {
    inspections,
    maintenance: { tools },
    benchmarks: staticData.benchmarks,
    forecasting: staticData.forecasting,
    kpis: {
      ...staticData.kpis,
      review_count: 0,
      feedback_count: 0,
      agreement_rate: null,
    },
  }
}

/** A session object so the UI renders without a login it cannot perform. */
export const DEMO_SESSION = { username: 'demo', role: 'OPERATOR', token: null }
