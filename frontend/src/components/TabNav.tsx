import React from 'react'
import {
  UploadCloud,
  Split,
  PlayCircle,
  BarChart3,
  CheckCircle2,
} from 'lucide-react'

export type TabId = 'upload' | 'line' | 'run' | 'results' | 'eval'

interface TabNavProps {
  activeTab: TabId
  onSelectTab: (tab: TabId) => void
  hasVideo: boolean
  hasLine: boolean
  hasResults: boolean
}

export const TabNav: React.FC<TabNavProps> = ({
  activeTab,
  onSelectTab,
  hasVideo,
  hasLine,
  hasResults,
}) => {
  const tabs: { id: TabId; label: string; icon: React.ReactNode; disabled: boolean }[] = [
    {
      id: 'upload',
      label: '1. Upload Video',
      icon: <UploadCloud size={18} />,
      disabled: false,
    },
    {
      id: 'line',
      label: '2. Virtual Counting Line',
      icon: <Split size={18} />,
      disabled: !hasVideo,
    },
    {
      id: 'run',
      label: '3. Run Counter',
      icon: <PlayCircle size={18} />,
      disabled: !hasVideo || !hasLine,
    },
    {
      id: 'results',
      label: '4. View Results',
      icon: <BarChart3 size={18} />,
      disabled: !hasResults,
    },
    {
      id: 'eval',
      label: '5. Ground Truth Evaluation',
      icon: <CheckCircle2 size={18} />,
      disabled: !hasResults,
    },
  ]

  return (
    <nav className="tabs-nav" aria-label="Workflow Navigation">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          id={`tab-${tab.id}`}
          className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
          onClick={() => onSelectTab(tab.id)}
          disabled={tab.disabled}
          title={tab.disabled ? 'Complete earlier steps first' : tab.label}
        >
          {tab.icon}
          <span>{tab.label}</span>
        </button>
      ))}
    </nav>
  )
}
