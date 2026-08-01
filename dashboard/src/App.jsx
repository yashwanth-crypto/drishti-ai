import { useCallback, useEffect, useState } from 'react'
import { loadDashboard } from './api.js'
import { getSession, logout, onSessionChange } from './auth.js'
import Login from './components/Login.jsx'
import Overview from './components/Overview.jsx'
import InspectionLog from './components/InspectionLog.jsx'
import LiveInspect from './components/LiveInspect.jsx'
import MaintenancePanel from './components/MaintenancePanel.jsx'
import InventoryForecast from './components/InventoryForecast.jsx'
import Benchmarks from './components/Benchmarks.jsx'
import RoiCalculator from './components/RoiCalculator.jsx'
import SettingsPanel from './components/SettingsPanel.jsx'
import {
  IconOverview, IconScan, IconWrench, IconTrend, IconBars, IconCalculator, IconTarget,
} from './components/Icons.jsx'
import './App.css'

const TABS = [
  { id: 'overview', label: 'Overview', icon: IconOverview, title: 'Overview', sub: 'Unified view across quality, uptime and inventory' },
  { id: 'inspect', label: 'Inspect a Part', icon: IconScan, title: 'Inspect a Part', sub: 'Upload a casting photo and run it through the live model' },
  { id: 'inspection', label: 'Quality Inspection', icon: IconScan, title: 'Quality Inspection', sub: 'CV defect detection (Module 1) → Hindi alerts (Module 2)' },
  { id: 'maintenance', label: 'Predictive Maintenance', icon: IconWrench, title: 'Predictive Maintenance', sub: 'Tool-wear remaining-life prediction (Module 3)' },
  { id: 'forecast', label: 'Demand Forecasting', icon: IconTrend, title: 'Demand Forecasting', sub: 'Weekly per-category demand with intervals (Module 4)' },
  { id: 'benchmarks', label: 'Benchmarks', icon: IconBars, title: 'Model Benchmarks', sub: 'Every model measured against baselines' },
  { id: 'roi', label: 'ROI Calculator', icon: IconCalculator, title: 'ROI Calculator', sub: 'Transparent, editable savings projection' },
  // Visible to everyone, but only an owner can change anything here.
  { id: 'settings', label: 'Settings', icon: IconTarget, title: 'Settings', sub: 'Detection and maintenance thresholds' },
]

function Logo() {
  return (
    <svg className="logo-mark" viewBox="0 0 40 40" width="38" height="38" aria-hidden="true">
      <defs>
        <linearGradient id="logoGrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="var(--brand)" />
          <stop offset="1" stopColor="var(--accent)" />
        </linearGradient>
      </defs>
      <rect x="1" y="1" width="38" height="38" rx="11" fill="url(#logoGrad)" />
      <path d="M8 20c3.6-6 8-9 12-9s8.4 3 12 9c-3.6 6-8 9-12 9s-8.4-3-12-9Z"
        fill="none" stroke="#fff" strokeWidth="2.1" strokeLinejoin="round" opacity="0.95" />
      <circle cx="20" cy="20" r="4" fill="#fff" />
    </svg>
  )
}

export default function App() {
  const [activeTab, setActiveTab] = useState('overview')
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [session, setSession] = useState(getSession)
  const active = TABS.find((t) => t.id === activeTab)

  const refresh = useCallback(() => {
    setError(null)
    loadDashboard().then(setData).catch((err) => setError(err.message))
  }, [])

  // An expired token clears the session from inside api.js, which drops the UI
  // back to the login screen wherever the user happened to be.
  useEffect(() => onSessionChange(setSession), [])

  useEffect(() => {
    if (session) refresh()
    else setData(null)
  }, [session, refresh])

  if (!session) return <Login onSignedIn={() => setSession(getSession())} />

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <Logo />
          <div className="brand-text">
            <span className="brand-name">Drishti&#8288;-&#8288;AI</span>
            <span className="brand-tag">MSME Manufacturing AI</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          {TABS.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                className={`nav-item ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <Icon size={18} />
                <span>{tab.label}</span>
              </button>
            )
          })}
        </nav>

        <div className="sidebar-user">
          <div className="sidebar-user-id">
            <span className="sidebar-username">{session.username}</span>
            <span className={`role-chip ${session.role === 'OWNER' ? 'owner' : ''}`}>{session.role}</span>
          </div>
          <button className="signout-btn" onClick={logout}>Sign out</button>
        </div>

        <div className="sidebar-foot">
          <span className="live-dot" />
          <span>Proof-of-concept · real model output on public datasets</span>
        </div>
      </aside>

      <div className="main-col">
        <header className="topbar">
          <div>
            <h1>{active.title}</h1>
            <p className="topbar-sub">{active.sub}</p>
          </div>
          <div className="header-meta">
            <span className="live-dot" />
            Live dashboard
          </div>
        </header>

        <main className="app-content">
          {error && (
            <div className="card">
              <h2>Something went wrong</h2>
              <p className="card-sub">{error}</p>
              <p className="card-sub">
                If the backend isn&rsquo;t running, start it with <code>mvn spring-boot:run</code> in{' '}
                <code>app/backend</code>, and make sure the inference service is up on port 8000.
              </p>
            </div>
          )}
          {!error && !data && <div className="card"><p className="card-sub">Loading live data…</p></div>}

          {data && (
            <>
              {activeTab === 'overview' && <Overview data={data} />}
              {activeTab === 'inspect' && <LiveInspect onInspected={refresh} />}
              {activeTab === 'inspection' && (
                <InspectionLog inspections={data.inspections} onFeedback={refresh} />
              )}
              {activeTab === 'maintenance' && <MaintenancePanel tools={data.maintenance.tools} />}
              {activeTab === 'forecast' && <InventoryForecast forecasting={data.forecasting} />}
              {activeTab === 'benchmarks' && <Benchmarks benchmarks={data.benchmarks} />}
              {activeTab === 'roi' && <RoiCalculator />}
              {activeTab === 'settings' && <SettingsPanel />}
            </>
          )}
        </main>
      </div>
    </div>
  )
}
