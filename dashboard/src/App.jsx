import { useState } from 'react'
import eventsData from './data/events.json'
import Overview from './components/Overview.jsx'
import InspectionLog from './components/InspectionLog.jsx'
import MaintenancePanel from './components/MaintenancePanel.jsx'
import InventoryForecast from './components/InventoryForecast.jsx'
import Benchmarks from './components/Benchmarks.jsx'
import RoiCalculator from './components/RoiCalculator.jsx'
import {
  IconOverview, IconScan, IconWrench, IconTrend, IconBars, IconCalculator,
} from './components/Icons.jsx'
import './App.css'

const TABS = [
  { id: 'overview', label: 'Overview', icon: IconOverview, title: 'Overview', sub: 'Unified view across quality, uptime and inventory' },
  { id: 'inspection', label: 'Quality Inspection', icon: IconScan, title: 'Quality Inspection', sub: 'CV defect detection (Module 1) → Hindi alerts (Module 2)' },
  { id: 'maintenance', label: 'Predictive Maintenance', icon: IconWrench, title: 'Predictive Maintenance', sub: 'Tool-wear remaining-life prediction (Module 3)' },
  { id: 'forecast', label: 'Demand Forecasting', icon: IconTrend, title: 'Demand Forecasting', sub: 'Weekly per-category demand with intervals (Module 4)' },
  { id: 'benchmarks', label: 'Benchmarks', icon: IconBars, title: 'Model Benchmarks', sub: 'Every model measured against baselines' },
  { id: 'roi', label: 'ROI Calculator', icon: IconCalculator, title: 'ROI Calculator', sub: 'Transparent, editable savings projection' },
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
  const active = TABS.find((t) => t.id === activeTab)

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
          {activeTab === 'overview' && <Overview data={eventsData} />}
          {activeTab === 'inspection' && <InspectionLog inspections={eventsData.inspections} />}
          {activeTab === 'maintenance' && <MaintenancePanel tools={eventsData.maintenance.tools} />}
          {activeTab === 'forecast' && <InventoryForecast forecasting={eventsData.forecasting} />}
          {activeTab === 'benchmarks' && <Benchmarks benchmarks={eventsData.benchmarks} />}
          {activeTab === 'roi' && <RoiCalculator />}
        </main>
      </div>
    </div>
  )
}
