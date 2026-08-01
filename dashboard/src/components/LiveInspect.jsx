import { useRef, useState } from 'react'
import StatusBadge from './StatusBadge.jsx'
import { IconScan } from './Icons.jsx'
import { inspectImage } from '../api.js'

export default function LiveInspect({ onInspected }) {
  const [dragging, setDragging] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [preview, setPreview] = useState(null)
  const [partId, setPartId] = useState('')
  const fileInput = useRef(null)

  async function run(file) {
    if (!file) return
    setBusy(true)
    setError(null)
    setResult(null)
    setPreview((old) => {
      if (old) URL.revokeObjectURL(old)
      return URL.createObjectURL(file)
    })

    try {
      const inspection = await inspectImage(file, partId.trim())
      setResult(inspection)
      onInspected?.(inspection)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  function onDrop(event) {
    event.preventDefault()
    setDragging(false)
    run(event.dataTransfer.files?.[0])
  }

  return (
    <div>
      <div className="card">
        <h2 className="with-icon">
          <span className="ct-icon"><IconScan size={17} /></span>Inspect a part
        </h2>
        <p className="card-sub">
          Drop a casting photo in and it runs through the trained MobileNetV2 classifier (Module 1),
          generates the Hindi operator alert (Module 2), and stores the result. This is a real
          prediction from the model, not a canned response.
        </p>

        <div className="inspect-controls">
          <label className="inspect-field">
            <span>Part ID (optional)</span>
            <input
              type="text"
              value={partId}
              placeholder="P-1042"
              onChange={(e) => setPartId(e.target.value)}
            />
          </label>
        </div>

        <div
          className={`dropzone ${dragging ? 'dragging' : ''} ${busy ? 'busy' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => fileInput.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && fileInput.current?.click()}
        >
          <input
            ref={fileInput}
            type="file"
            accept="image/*"
            hidden
            onChange={(e) => run(e.target.files?.[0])}
          />
          {busy ? (
            <span className="dropzone-text">Running the model…</span>
          ) : (
            <>
              <span className="dropzone-text">Drop a part image here, or click to choose one</span>
              <span className="dropzone-hint">
                Try any file from module1_cv_defect/data/casting/test/
              </span>
            </>
          )}
        </div>

        {error && <p className="inspect-error">{error}</p>}
      </div>

      {result && (
        <div className="card">
          <div className="tool-card-header">
            <div>
              <h2>{result.part_id}</h2>
              <p className="card-sub" style={{ marginBottom: 0 }}>
                Classified as <strong>{result.defect_type}</strong> in {result.inference_ms.toFixed(0)}ms
              </p>
            </div>
            <StatusBadge status={result.pass_fail} label={result.pass_fail.toUpperCase()} />
          </div>

          <div className="inspect-result">
            {preview && <img className="inspect-preview" src={preview} alt={result.part_id} />}
            <div className="inspect-detail">
              <div className="inspect-metric">
                <span className="stat-label">Confidence</span>
                <span className="stat-value">{(result.confidence * 100).toFixed(2)}%</span>
              </div>
              <div className="inspect-metric">
                <span className="stat-label">Inference time</span>
                <span className="stat-value">{result.inference_ms.toFixed(1)}ms</span>
              </div>
              <div className="inspect-alert-box">
                <span className="stat-label">Operator alert (Hindi)</span>
                <p>{result.alert_hi}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
