import { useEffect, useState } from 'react'
import { getSettings, saveSettings } from '../api.js'
import { isOwner } from '../auth.js'
import { isDemoMode } from '../demo.js'
import { IconTarget } from './Icons.jsx'

export default function SettingsPanel() {
  const [defectThreshold, setDefectThreshold] = useState(0.5)
  const [rulAlertThreshold, setRulAlertThreshold] = useState(0.2)
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const demo = isDemoMode()
  const owner = !demo && isOwner()

  useEffect(() => {
    if (demo) return          // no backend to read them from
    getSettings()
      .then((s) => {
        setDefectThreshold(s.defectThreshold)
        setRulAlertThreshold(s.rulAlertThreshold)
      })
      .catch((err) => setError(err.message))
  }, [demo])

  async function submit(event) {
    event.preventDefault()
    setBusy(true)
    setStatus(null)
    setError(null)
    try {
      await saveSettings(Number(defectThreshold), Number(rulAlertThreshold))
      setStatus('Saved')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="card" onSubmit={submit}>
      <h2 className="with-icon">
        <span className="ct-icon"><IconTarget size={17} /></span>Thresholds
      </h2>
      <p className="card-sub">
        How strict the system is. Raising the defect threshold means fewer parts get
        flagged but more real defects slip through — the trade-off behind limitation L4
        in the project write-up. The RUL threshold sets when a tool raises a maintenance alert.
      </p>

      <div className="settings-grid">
        <label className="inspect-field">
          <span>Defect confidence threshold — {Number(defectThreshold).toFixed(2)}</span>
          <input
            type="range" min="0" max="1" step="0.01"
            value={defectThreshold}
            disabled={!owner}
            onChange={(e) => setDefectThreshold(e.target.value)}
          />
        </label>

        <label className="inspect-field">
          <span>Tool-wear alert threshold — {Number(rulAlertThreshold).toFixed(2)}</span>
          <input
            type="range" min="0" max="1" step="0.01"
            value={rulAlertThreshold}
            disabled={!owner}
            onChange={(e) => setRulAlertThreshold(e.target.value)}
          />
        </label>
      </div>

      {error && <p className="inspect-error">{error}</p>}
      {status && <p className="settings-status">{status}</p>}

      {owner ? (
        <button className="login-submit" type="submit" disabled={busy} style={{ maxWidth: 200 }}>
          {busy ? 'Saving…' : 'Save thresholds'}
        </button>
      ) : (
        <p className="roi-caveat">
          {demo
            ? 'These are the shipped defaults. In the running system an owner moves these sliders and the change takes effect on the next inspection.'
            : 'You are signed in as an operator, so these are read-only. Ask an owner to change them.'}
        </p>
      )}
    </form>
  )
}
