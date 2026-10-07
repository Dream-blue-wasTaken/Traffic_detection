import React, { useState, useEffect } from 'react'
import {
  Download,
  Film,
  FileSpreadsheet,
  FileText,
  Archive,
  BarChart2,
  TrendingUp,
  Search,
} from 'lucide-react'
import type { RunResults } from '../types'

interface Step4ResultsProps {
  jobId: string
  onProceedToEval: () => void
}

export const Step4Results: React.FC<Step4ResultsProps> = ({
  jobId,
  onProceedToEval,
}) => {
  const [results, setResults] = useState<RunResults | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedDirection, setSelectedDirection] = useState<string>('all')

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const resp = await fetch(`/api/results/${jobId}`)
        if (!resp.ok) {
          throw new Error('Failed to load results')
        }
        const data = await resp.json()
        setResults(data)
      } catch (err: any) {
        setError(err.message || 'Error fetching results')
      } finally {
        setLoading(false)
      }
    }

    fetchResults()
  }, [jobId])

  if (loading) {
    return (
      <div className="glass-panel" style={{ padding: '48px', textAlign: 'center' }}>
        <p style={{ color: 'var(--text-secondary)' }}>Loading analytics and results...</p>
      </div>
    )
  }

  if (error || !results) {
    return (
      <div className="glass-panel" style={{ padding: '36px', textAlign: 'center' }}>
        <p style={{ color: 'var(--danger)' }}>{error || 'No results found for this run.'}</p>
      </div>
    )
  }

  // Direction totals
  const dirNames = Object.keys(results.totals || {})
  const dir1 = dirNames[0] || 'entry'
  const dir2 = dirNames[1] || 'exit'

  const cntDir1 = Object.values(results.totals?.[dir1] || {}).reduce((a, b) => a + b, 0)
  const cntDir2 = Object.values(results.totals?.[dir2] || {}).reduce((a, b) => a + b, 0)

  // Filter events
  const filteredEvents = (results.events || []).filter((e) => {
    const matchesSearch =
      e.class_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      String(e.track_id).includes(searchTerm)
    const matchesDir =
      selectedDirection === 'all' || e.direction === selectedDirection
    return matchesSearch && matchesDir
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Metrics Row */}
      <div className="metrics-grid">
        <div className="metric-card glass-panel">
          <span className="metric-title">
            <TrendingUp size={14} /> Total Vehicles
          </span>
          <span className="metric-value">{results.total_vehicles}</span>
        </div>

        <div className="metric-card glass-panel">
          <span className="metric-title">
            Direction: {dir1.toUpperCase()}
          </span>
          <span className="metric-value" style={{ color: '#10b981' }}>
            {cntDir1}
          </span>
        </div>

        <div className="metric-card glass-panel">
          <span className="metric-title">
            Direction: {dir2.toUpperCase()}
          </span>
          <span className="metric-value" style={{ color: '#06b6d4' }}>
            {cntDir2}
          </span>
        </div>

        <div className="metric-card glass-panel">
          <span className="metric-title">
            Processing Speed
          </span>
          <span className="metric-value" style={{ fontSize: '1.6rem' }}>
            {results.summary?.average_fps?.toFixed(1) || '0.0'}{' '}
            <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>FPS</span>
          </span>
        </div>
      </div>

      {/* Interval Chart & Analytics */}
      {results.intervals && results.intervals.length > 0 && (
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3
            style={{
              fontSize: '1.1rem',
              fontWeight: 700,
              marginBottom: '16px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <BarChart2 size={18} color="var(--accent-primary)" /> Counts by Time Interval
          </h3>

          <div
            style={{
              display: 'flex',
              alignItems: 'flex-end',
              gap: '12px',
              height: '180px',
              padding: '16px 8px 8px',
              borderBottom: '1px solid var(--border-subtle)',
              marginBottom: '16px',
              overflowX: 'auto',
            }}
          >
            {results.intervals.map((inv, idx) => {
              const maxVal = Math.max(
                1,
                ...results.intervals.map((i) => i.total || 1)
              )
              const heightPct = Math.max(12, ((inv.total || 0) / maxVal) * 100)
              return (
                <div
                  key={idx}
                  style={{
                    flex: '0 0 70px',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '6px',
                    height: '100%',
                    justifyContent: 'flex-end',
                  }}
                >
                  <span
                    style={{
                      fontSize: '0.75rem',
                      fontFamily: 'var(--font-mono)',
                      color: 'var(--accent-cyan)',
                      fontWeight: 600,
                    }}
                  >
                    {inv.total || 0}
                  </span>
                  <div
                    style={{
                      width: '38px',
                      height: `${heightPct}%`,
                      background: 'linear-gradient(180deg, #6366f1, #3b82f6)',
                      borderRadius: '6px 6px 0 0',
                      transition: 'height 0.4s ease',
                      boxShadow: '0 0 10px rgba(99, 102, 241, 0.3)',
                    }}
                  />
                  <span
                    style={{
                      fontSize: '0.6875rem',
                      color: 'var(--text-muted)',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {inv.interval_start}
                  </span>
                </div>
              )
            })}
          </div>

          {/* Interval Data Table */}
          <div style={{ overflowX: 'auto', maxHeight: '220px' }}>
            <table
              style={{
                width: '100%',
                borderCollapse: 'collapse',
                fontSize: '0.8125rem',
                textAlign: 'left',
              }}
            >
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)' }}>
                  {Object.keys(results.intervals[0] || {}).map((col) => (
                    <th key={col} style={{ padding: '8px 12px', fontWeight: 600 }}>
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {results.intervals.map((row, rIdx) => (
                  <tr
                    key={rIdx}
                    style={{
                      borderBottom: '1px solid rgba(255, 255, 255, 0.03)',
                    }}
                  >
                    {Object.values(row).map((val: any, cIdx) => (
                      <td
                        key={cIdx}
                        style={{
                          padding: '8px 12px',
                          fontFamily: typeof val === 'number' ? 'var(--font-mono)' : 'inherit',
                        }}
                      >
                        {String(val)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Video & Events Split View */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 1fr', gap: '24px' }}>
        {/* Annotated Video Player */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3
            style={{
              fontSize: '1.1rem',
              fontWeight: 700,
              marginBottom: '16px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <Film size={18} color="var(--accent-cyan)" /> Annotated Video Output
          </h3>

          {results.annotated_video_available && results.video_url ? (
            <div
              style={{
                borderRadius: 'var(--radius-md)',
                overflow: 'hidden',
                background: '#000',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <video
                src={results.video_url}
                controls
                style={{ width: '100%', display: 'block', maxHeight: '420px' }}
              />
            </div>
          ) : (
            <div style={{ padding: '36px', textAlign: 'center', color: 'var(--text-muted)' }}>
              No annotated video was generated for this run.
            </div>
          )}
        </div>

        {/* Crossing Events Table */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '14px',
            }}
          >
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>
              Crossing Events ({filteredEvents.length})
            </h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Total: {results.events?.length || 0}
            </span>
          </div>

          {/* Search & Filter */}
          <div style={{ display: 'flex', gap: '10px', marginBottom: '14px' }}>
            <div style={{ position: 'relative', flex: 1 }}>
              <input
                type="text"
                placeholder="Search class or track ID..."
                className="input-field"
                style={{ paddingLeft: '32px' }}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
              <Search
                size={14}
                style={{ position: 'absolute', left: '10px', top: '13px', color: 'var(--text-muted)' }}
              />
            </div>
            <select
              className="select-field"
              style={{ width: '120px' }}
              value={selectedDirection}
              onChange={(e) => setSelectedDirection(e.target.value)}
            >
              <option value="all">All Dirs</option>
              {dirNames.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>

          {/* Events Table Container */}
          <div style={{ flex: 1, overflowY: 'auto', maxHeight: '330px' }}>
            <table
              style={{
                width: '100%',
                borderCollapse: 'collapse',
                fontSize: '0.8125rem',
                textAlign: 'left',
              }}
            >
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '6px 8px' }}>Track ID</th>
                  <th style={{ padding: '6px 8px' }}>Class</th>
                  <th style={{ padding: '6px 8px' }}>Direction</th>
                  <th style={{ padding: '6px 8px' }}>Time (s)</th>
                </tr>
              </thead>
              <tbody>
                {filteredEvents.map((evt, idx) => (
                  <tr
                    key={idx}
                    style={{
                      borderBottom: '1px solid rgba(255, 255, 255, 0.03)',
                    }}
                  >
                    <td style={{ padding: '6px 8px', fontFamily: 'var(--font-mono)' }}>
                      #{evt.track_id}
                    </td>
                    <td style={{ padding: '6px 8px', textTransform: 'capitalize', fontWeight: 500 }}>
                      {evt.class_name}
                    </td>
                    <td style={{ padding: '6px 8px' }}>
                      <span
                        style={{
                          padding: '2px 8px',
                          borderRadius: '10px',
                          fontSize: '0.6875rem',
                          background:
                            evt.direction === dir1
                              ? 'rgba(16, 185, 129, 0.15)'
                              : 'rgba(6, 182, 212, 0.15)',
                          color: evt.direction === dir1 ? '#34d399' : '#22d3ee',
                        }}
                      >
                        {evt.direction}
                      </span>
                    </td>
                    <td style={{ padding: '6px 8px', fontFamily: 'var(--font-mono)' }}>
                      {evt.timestamp_s}s
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Download Center & Evaluation Navigation */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '16px',
          }}
        >
          <div>
            <h4 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '4px' }}>
              Export Artifacts & Data
            </h4>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
              Download complete analysis reports in open standard formats.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <a
              href={`/api/download/${jobId}/intervals-csv`}
              download
              className="btn btn-secondary"
            >
              <FileSpreadsheet size={15} /> Interval Counts (CSV)
            </a>
            <a
              href={`/api/download/${jobId}/events-csv`}
              download
              className="btn btn-secondary"
            >
              <FileText size={15} /> Events (CSV)
            </a>
            <a
              href={`/api/download/${jobId}/summary-json`}
              download
              className="btn btn-secondary"
            >
              <Download size={15} /> Summary (JSON)
            </a>
            <a
              href={`/api/download/${jobId}/zip`}
              download
              className="btn btn-accent"
            >
              <Archive size={15} /> Download All (.ZIP)
            </a>
            <button className="btn btn-primary" onClick={onProceedToEval}>
              Ground Truth Evaluation &rarr;
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
