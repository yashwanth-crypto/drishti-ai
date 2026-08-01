import { useState } from 'react'
import { login } from '../auth.js'

function Logo() {
  return (
    <svg viewBox="0 0 40 40" width="46" height="46" aria-hidden="true">
      <defs>
        <linearGradient id="loginGrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="var(--brand)" />
          <stop offset="1" stopColor="var(--accent)" />
        </linearGradient>
      </defs>
      <rect x="1" y="1" width="38" height="38" rx="11" fill="url(#loginGrad)" />
      <path d="M8 20c3.6-6 8-9 12-9s8.4 3 12 9c-3.6 6-8 9-12 9s-8.4-3-12-9Z"
        fill="none" stroke="#fff" strokeWidth="2.1" strokeLinejoin="round" opacity="0.95" />
      <circle cx="20" cy="20" r="4" fill="#fff" />
    </svg>
  )
}

export default function Login({ onSignedIn }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  async function submit(event) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await login(username, password)
      onSignedIn()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="login-shell">
      <form className="login-card" onSubmit={submit}>
        <div className="login-brand">
          <Logo />
          <div>
            <h1>Drishti&#8288;-&#8288;AI</h1>
            <p>MSME Manufacturing AI</p>
          </div>
        </div>

        <label className="inspect-field">
          <span>Username</span>
          <input
            type="text"
            value={username}
            autoComplete="username"
            autoFocus
            onChange={(e) => setUsername(e.target.value)}
          />
        </label>

        <label className="inspect-field">
          <span>Password</span>
          <input
            type="password"
            value={password}
            autoComplete="current-password"
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>

        {error && <p className="inspect-error">{error}</p>}

        <button className="login-submit" type="submit" disabled={busy || !username || !password}>
          {busy ? 'Signing in…' : 'Sign in'}
        </button>

        <p className="login-hint">
          Development accounts: <code>owner</code> / <code>operator</code>.
          An operator can inspect parts and read everything; only an owner can
          change thresholds or recompute forecasts.
        </p>
      </form>
    </div>
  )
}
