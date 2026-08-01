/**
 * Session handling. The token lives in localStorage so a reload doesn't force a
 * new login; the backend is the only thing that trusts it, and it expires on its
 * own after 12 hours.
 */
const KEY = 'drishti.session'

let session = null
try {
  session = JSON.parse(localStorage.getItem(KEY) ?? 'null')
} catch {
  session = null
}

const listeners = new Set()

export function getSession() {
  return session
}

export function onSessionChange(fn) {
  listeners.add(fn)
  return () => listeners.delete(fn)
}

function setSession(next) {
  session = next
  if (next) localStorage.setItem(KEY, JSON.stringify(next))
  else localStorage.removeItem(KEY)
  listeners.forEach((fn) => fn(next))
}

export function authHeader() {
  return session?.token ? { Authorization: `Bearer ${session.token}` } : {}
}

export function isOwner() {
  return session?.role === 'OWNER'
}

export async function login(username, password) {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(body.error ?? 'Could not sign in')

  setSession({ token: body.token, username: body.username, role: body.role })
  return body
}

export function logout() {
  setSession(null)
}

/** Called when the API rejects our token, so the UI drops back to the login screen. */
export function sessionExpired() {
  if (session) setSession(null)
}
