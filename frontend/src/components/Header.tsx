import React from 'react'
import { Car, Cpu } from 'lucide-react'
import type { SystemInfo } from '../types'

interface HeaderProps {
  systemInfo: SystemInfo | null
  currentJobStatus?: string
}

export const Header: React.FC<HeaderProps> = ({ systemInfo, currentJobStatus }) => {
  const isCuda = systemInfo?.device_badge.includes('CUDA')
  const isMps = systemInfo?.device_badge.includes('MPS')

  return (
    <header className="app-header">
      <div className="brand-section">
        <div className="brand-logo-glow">
          <Car size={26} color="#ffffff" strokeWidth={2.2} />
        </div>
        <div>
          <h1 className="brand-title">Traffic Vision AI</h1>
          <p className="brand-subtitle">
            Autonomous Vehicle Counting & Directional Analytics
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {currentJobStatus && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 14px',
              background: 'rgba(255, 255, 255, 0.04)',
              borderRadius: '20px',
              fontSize: '0.8125rem',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <span
              className={`live-indicator ${
                currentJobStatus === 'running'
                  ? ''
                  : currentJobStatus === 'completed'
                  ? 'done'
                  : 'idle'
              }`}
            />
            <span style={{ textTransform: 'capitalize', fontWeight: 500 }}>
              {currentJobStatus === 'running' ? 'Pipeline Active' : currentJobStatus}
            </span>
          </div>
        )}

        <div
          className={`badge ${
            isCuda ? 'badge-cuda' : isMps ? 'badge-mps' : 'badge-cpu'
          }`}
        >
          <Cpu size={14} />
          {systemInfo?.device_badge || 'Detecting Engine...'}
        </div>
      </div>
    </header>
  )
}
