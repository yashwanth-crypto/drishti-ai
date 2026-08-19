import { useState } from 'react'
import { sendFeedback } from '../api.js'
import { isDemoMode } from '../demo.js'

const OTHER = { ok_front: 'def_front', def_front: 'ok_front' }
const LABEL = { ok_front: 'good', def_front: 'defective' }

/**
 * Lets an operator confirm or correct the model's call. Two classes, so
 * "disagree" fully determines the true label -- the opposite of what the model
 * said -- and that label is what gets stored, ready for retraining.
 */
export default function FeedbackControl({ inspection, onRecorded }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(false)
  const demo = isDemoMode()

  async function record(verdict) {
    setBusy(true)
    setError(false)
    try {
      onRecorded(await sendFeedback(inspection.id, verdict))
    } catch {
      setError(true)
    } finally {
      setBusy(false)
    }
  }

  // Corrections are stored server-side, so there is nowhere to put them here.
  if (demo) return <span className="feedback-done demo">demo</span>

  if (inspection.operator_verdict) {
    const agreed = inspection.was_correct
    return (
      <span className={`feedback-done ${agreed ? 'agreed' : 'corrected'}`}
            title={inspection.feedback_by ? `Marked by ${inspection.feedback_by}` : undefined}>
        {agreed ? 'confirmed' : `corrected → ${LABEL[inspection.operator_verdict]}`}
      </span>
    )
  }

  const modelSaid = inspection.defect_type
  return (
    <span className="feedback-actions">
      <button
        className="feedback-btn agree"
        disabled={busy}
        title="The model got this right"
        onClick={() => record(modelSaid)}
      >
        correct
      </button>
      <button
        className="feedback-btn disagree"
        disabled={busy}
        title={`Actually ${LABEL[OTHER[modelSaid]] ?? 'the other class'}`}
        onClick={() => record(OTHER[modelSaid])}
      >
        wrong
      </button>
      {error && <span className="feedback-error">failed</span>}
    </span>
  )
}
