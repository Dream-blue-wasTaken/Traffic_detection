import React, { useState, useRef } from 'react'
import {
  UploadCloud,
  AlertCircle,
  Target,
} from 'lucide-react'
import type { EvalMetrics } from '../types'

interface Step5EvaluationProps {
  jobId: string
}

export const Step5Evaluation: React.FC<Step5EvaluationProps> = ({ jobId }) => {
  const [tolerance, setTolerance] = useState<number>(2.0)
  const [evalFile, setEvalFile] = useState<File | null>(null)
  const [evaluating, setEvaluating] = useState<boolean>(false)
  const [metrics, setMetrics] = useState<EvalMetrics | null>(null)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleRunEvaluation = async () => {
    if (!evalFile) {
      setError('Please upload a ground truth CSV file first.')
      return
    }

    setError(null)
    setEvaluating(true)

    const formData = new FormData()
    formData.append('file', evalFile)
    formData.append('tolerance_s', String(tolerance))

    try {
      const resp = await fetch(`/api/evaluate/${jobId}`, {
        method: 'POST',
        body: formData,
      })

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}))
        throw new Error(err.detail || 'Evaluation failed')
      }

      const data = await resp.json()
      setMetrics(data)
    } catch (err: any) {
      setError(err.message || 'Evaluation error')
    } finally {
      setEvaluating(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div className="glass-panel" style={{ padding: '28px' }}>
        <h3
          style={{
            fontSize: '1.15rem',
            fontWeight: 700,
            marginBottom: '6px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <Target size={20} color="var(--accent-primary)" /> Ground Truth Accuracy Evaluation
        </h3>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '20px' }}>
          Compare automated YOLO + ByteTrack detections against human ground truth counts to quantify system precision, recall, and count error.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '24px' }}>
          {/* File Upload Box */}
          <div
            style={{
              padding: '24px',
              border: '1px dashed var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              background: 'rgba(255, 255, 255, 0.02)',
              textAlign: 'center',
              cursor: 'pointer',
            }}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              style={{ display: 'none' }}
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  setEvalFile(e.target.files[0])
                }
              }}
            />
            <UploadCloud size={32} color="var(--accent-cyan)" style={{ margin: '0 auto 8px' }} />
            <h4 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '4px' }}>
              {evalFile ? evalFile.name : 'Select Ground Truth CSV'}
            </h4>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Requires columns: track_id, class_name, direction, timestamp_s (or count data)
            </span>
          </div>

          {/* Tolerance & Execute */}
          <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  marginBottom: '8px',
                  fontSize: '0.8125rem',
                }}
              >
                <span style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>
                  Matching Time Tolerance
                </span>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-primary)' }}>
                  {tolerance} seconds
                </span>
              </div>
              <input
                type="range"
                min="0.5"
                max="5.0"
                step="0.5"
                className="range-slider"
                value={tolerance}
                onChange={(e) => setTolerance(parseFloat(e.target.value))}
              />
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginTop: '6px' }}>
                Window within which an automated crossing is matched to a human log.
              </span>
            </div>

            <button
              className="btn btn-primary"
              style={{ padding: '12px', marginTop: '16px' }}
              onClick={handleRunEvaluation}
              disabled={!evalFile || evaluating}
            >
              {evaluating ? 'Computing Metrics...' : 'Evaluate Accuracy'}
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '14px',
            background: 'rgba(239, 68, 68, 0.12)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: 'var(--radius-md)',
            color: '#fca5a5',
            fontSize: '0.875rem',
          }}
        >
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* Metrics Results */}
      {metrics && metrics.total_count_metrics && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div className="metrics-grid">
            <div className="metric-card glass-panel">
              <span className="metric-title">Ground Truth Count</span>
              <span className="metric-value">{metrics.total_count_metrics.manual}</span>
            </div>

            <div className="metric-card glass-panel">
              <span className="metric-title">Automated AI Count</span>
              <span className="metric-value">{metrics.total_count_metrics.auto}</span>
            </div>

            <div className="metric-card glass-panel">
              <span className="metric-title">Count Accuracy</span>
              <span className="metric-value" style={{ color: '#10b981' }}>
                {metrics.total_count_metrics.accuracy_pct.toFixed(1)}%
              </span>
            </div>

            <div className="metric-card glass-panel">
              <span className="metric-title">Signed Error</span>
              <span
                className="metric-value"
                style={{
                  color:
                    metrics.total_count_metrics.signed_error_pct === 0
                      ? 'var(--text-primary)'
                      : metrics.total_count_metrics.signed_error_pct > 0
                      ? '#fbbf24'
                      : '#ef4444',
                }}
              >
                {metrics.total_count_metrics.signed_error_pct > 0 ? '+' : ''}
                {metrics.total_count_metrics.signed_error_pct.toFixed(1)}%
              </span>
            </div>
          </div>

          {/* Event-Level Precision & Recall */}
          {metrics.event_metrics && (
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h4 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '16px' }}>
                Event-Level Matching Metrics
              </h4>
              <div className="metrics-grid">
                <div className="metric-card glass-panel">
                  <span className="metric-title">Precision</span>
                  <span className="metric-value" style={{ fontSize: '1.6rem' }}>
                    {(metrics.event_metrics.precision * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="metric-card glass-panel">
                  <span className="metric-title">Recall</span>
                  <span className="metric-value" style={{ fontSize: '1.6rem' }}>
                    {(metrics.event_metrics.recall * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="metric-card glass-panel">
                  <span className="metric-title">F1 Score</span>
                  <span className="metric-value" style={{ fontSize: '1.6rem', color: 'var(--accent-cyan)' }}>
                    {metrics.event_metrics.f1.toFixed(3)}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Plot Gallery */}
          {metrics.plots && metrics.plots.length > 0 && (
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h4 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '16px' }}>
                Evaluation Plots & Distributions
              </h4>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
                  gap: '16px',
                }}
              >
                {metrics.plots.map((plot) => (
                  <div
                    key={plot.name}
                    style={{
                      borderRadius: 'var(--radius-md)',
                      overflow: 'hidden',
                      border: '1px solid var(--border-subtle)',
                      background: '#fff',
                    }}
                  >
                    <img
                      src={plot.url}
                      alt={plot.name}
                      style={{ width: '100%', height: 'auto', display: 'block' }}
                    />
                    <div
                      style={{
                        padding: '10px 14px',
                        background: 'rgba(10, 14, 23, 0.9)',
                        color: 'var(--text-secondary)',
                        fontSize: '0.8125rem',
                      }}
                    >
                      {plot.name}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
