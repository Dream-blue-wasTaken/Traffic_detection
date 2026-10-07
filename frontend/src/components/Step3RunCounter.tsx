import React, { useState, useEffect, useRef } from 'react'
import {
  Play,
  Square,
  Clock,
  ArrowRight,
  AlertCircle,
  CheckCircle2,
  Sliders,
  Eye,
} from 'lucide-react'
import type {
  CountingLineConfig,
  PipelineStatus,
  SystemInfo,
  UploadResponse,
} from '../types'

interface Step3RunCounterProps {
  systemInfo: SystemInfo | null
  video: UploadResponse
  lineConfig: CountingLineConfig
  onJobCompleted: (jobId: string) => void
  onProceedToResults: () => void
}

export const Step3RunCounter: React.FC<Step3RunCounterProps> = ({
  systemInfo,
  video,
  lineConfig,
  onJobCompleted,
  onProceedToResults,
}) => {
  // Pipeline Settings
  const [modelWeights, setModelWeights] = useState<string>(
    systemInfo?.default_model || 'yolo26s.pt'
  )
  const [tracker, setTracker] = useState<string>('bytetrack')
  const [confThreshold, setConfThreshold] = useState<number>(0.25)
  const [imgSize, setImgSize] = useState<number>(640)
  const [intervalMinutes, setIntervalMinutes] = useState<number>(5)
  const [countingMode, setCountingMode] = useState<'simple' | 'gated'>('simple')
  const [limitSeconds, setLimitSeconds] = useState<number>(0.0)

  // Classes
  const [trackCars, setTrackCars] = useState(true)
  const [trackMotorcycles, setTrackMotorcycles] = useState(true)
  const [trackBuses, setTrackBuses] = useState(true)
  const [trackTrucks, setTrackTrucks] = useState(true)
  const [trackBicycles, setTrackBicycles] = useState(false)
  const [enableRickshaw, setEnableRickshaw] = useState(
    Boolean(systemInfo?.has_rickshaw_model)
  )

  // Running State
  const [currentJobId, setCurrentJobId] = useState<string | null>(null)
  const [jobStatus, setJobStatus] = useState<PipelineStatus | null>(null)
  const [isStarting, setIsStarting] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  const isRunning = jobStatus?.status === 'running'

  // Handle start pipeline
  const handleStartPipeline = async () => {
    setIsStarting(true)

    // Build active classes dictionary
    const activeClasses: Record<string, number> = {}
    if (trackCars) activeClasses['car'] = 2
    if (trackMotorcycles) activeClasses['motorcycle'] = 3
    if (trackBuses) activeClasses['bus'] = 5
    if (trackTrucks) activeClasses['truck'] = 7
    if (trackBicycles) activeClasses['bicycle'] = 1

    const payload = {
      video_path: video.video_path,
      p1: lineConfig.p1,
      p2: lineConfig.p2,
      offset_px: lineConfig.offset_px,
      dir_a_to_b: lineConfig.dir_a_to_b,
      dir_b_to_a: lineConfig.dir_b_to_a,
      model_weights: modelWeights,
      tracker,
      conf_threshold: confThreshold,
      img_size: imgSize,
      interval_minutes: intervalMinutes,
      counting_mode: countingMode,
      active_classes: activeClasses,
      enable_rickshaw: enableRickshaw,
      limit_seconds: limitSeconds,
    }

    try {
      const resp = await fetch('/api/pipeline/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!resp.ok) {
        const err = await resp.json()
        throw new Error(err.detail || 'Failed to start pipeline')
      }

      const data = await resp.json()
      setCurrentJobId(data.job_id)
      setJobStatus({
        job_id: data.job_id,
        status: 'running',
        progress: 0.0,
        eta_s: 0.0,
        preview_base64: null,
        error: null,
        has_result: false,
      })

      // Connect WebSocket for real-time progress & preview
      connectWebSocket(data.job_id)
    } catch (err: any) {
      alert(`Error starting pipeline: ${err.message}`)
    } finally {
      setIsStarting(false)
    }
  }

  // Connect WebSocket
  const connectWebSocket = (jobId: string) => {
    if (wsRef.current) {
      wsRef.current.close()
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/pipeline/${jobId}`
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onmessage = (event) => {
      try {
        const data: PipelineStatus = JSON.parse(event.data)
        setJobStatus(data)

        if (data.status === 'completed' || data.status === 'stopped') {
          onJobCompleted(jobId)
        }
      } catch (err) {
        console.error('Error parsing WS message:', err)
      }
    }

    ws.onerror = (error) => {
      console.warn('WebSocket connection error, switching to fallback polling:', error)
      pollStatus(jobId)
    }
  }

  // Fallback Polling if WebSocket disconnected
  const pollStatus = async (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/pipeline/status/${jobId}`)
        if (!res.ok) return
        const data: PipelineStatus = await res.json()
        setJobStatus(data)

        if (data.status === 'completed' || data.status === 'stopped' || data.status === 'error') {
          clearInterval(interval)
          if (data.status === 'completed' || data.status === 'stopped') {
            onJobCompleted(jobId)
          }
        }
      } catch (e) {
        console.error('Polling error', e)
      }
    }, 500)
  }

  // Handle Stop Pipeline
  const handleStopPipeline = async () => {
    if (!currentJobId) return
    try {
      await fetch(`/api/pipeline/stop/${currentJobId}`, { method: 'POST' })
    } catch (e) {
      console.error('Stop error', e)
    }
  }

  useEffect(() => {
    return () => {
      if (wsRef.current) wsRef.current.close()
    }
  }, [])

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.3fr', gap: '24px' }}>
      {/* Configuration Sidebar */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3
            style={{
              fontSize: '1.1rem',
              fontWeight: 700,
              marginBottom: '18px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <Sliders size={18} color="var(--accent-primary)" /> Inference Parameters
          </h3>

          {/* Model Weights */}
          <div style={{ marginBottom: '16px' }}>
            <label
              style={{
                display: 'block',
                fontSize: '0.8125rem',
                fontWeight: 500,
                color: 'var(--text-secondary)',
                marginBottom: '6px',
              }}
            >
              YOLO Model Weights
            </label>
            <select
              className="select-field"
              value={modelWeights}
              onChange={(e) => setModelWeights(e.target.value)}
              disabled={isRunning}
            >
              {systemInfo?.models.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>

          {/* Tracker & Resolution */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
            <div>
              <label
                style={{
                  display: 'block',
                  fontSize: '0.8125rem',
                  fontWeight: 500,
                  color: 'var(--text-secondary)',
                  marginBottom: '6px',
                }}
              >
                Tracker Algorithm
              </label>
              <select
                className="select-field"
                value={tracker}
                onChange={(e) => setTracker(e.target.value)}
                disabled={isRunning}
              >
                <option value="bytetrack">ByteTrack (Fast & Robust)</option>
                <option value="botsort">BoTSORT (With ReID)</option>
              </select>
            </div>

            <div>
              <label
                style={{
                  display: 'block',
                  fontSize: '0.8125rem',
                  fontWeight: 500,
                  color: 'var(--text-secondary)',
                  marginBottom: '6px',
                }}
              >
                Inference Size (px)
              </label>
              <select
                className="select-field"
                value={imgSize}
                onChange={(e) => setImgSize(parseInt(e.target.value, 10))}
                disabled={isRunning}
              >
                <option value={640}>640 (Standard)</option>
                <option value={960}>960 (High Detail)</option>
                <option value={1280}>1280 (Ultra HD)</option>
              </select>
            </div>
          </div>

          {/* Confidence Slider */}
          <div style={{ marginBottom: '16px' }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                marginBottom: '6px',
                fontSize: '0.8125rem',
              }}
            >
              <span style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>
                Confidence Threshold
              </span>
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-primary)' }}>
                {Math.round(confThreshold * 100)}%
              </span>
            </div>
            <input
              type="range"
              min="0.10"
              max="0.85"
              step="0.05"
              className="range-slider"
              value={confThreshold}
              onChange={(e) => setConfThreshold(parseFloat(e.target.value))}
              disabled={isRunning}
            />
          </div>

          {/* Counting Mode & Interval */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
            <div>
              <label
                style={{
                  display: 'block',
                  fontSize: '0.8125rem',
                  fontWeight: 500,
                  color: 'var(--text-secondary)',
                  marginBottom: '6px',
                }}
              >
                Counting Mode
              </label>
              <select
                className="select-field"
                value={countingMode}
                onChange={(e) => setCountingMode(e.target.value as any)}
                disabled={isRunning}
              >
                <option value="simple">Simple Intersection</option>
                <option value="gated">Gated Directional</option>
              </select>
            </div>

            <div>
              <label
                style={{
                  display: 'block',
                  fontSize: '0.8125rem',
                  fontWeight: 500,
                  color: 'var(--text-secondary)',
                  marginBottom: '6px',
                }}
              >
                Time Interval
              </label>
              <select
                className="select-field"
                value={intervalMinutes}
                onChange={(e) => setIntervalMinutes(parseInt(e.target.value, 10))}
                disabled={isRunning}
              >
                <option value={1}>1 Minute</option>
                <option value={5}>5 Minutes</option>
                <option value={15}>15 Minutes</option>
                <option value={30}>30 Minutes</option>
              </select>
            </div>
          </div>

          {/* Process First N Seconds */}
          <div style={{ marginBottom: '20px' }}>
            <label
              style={{
                display: 'block',
                fontSize: '0.8125rem',
                fontWeight: 500,
                color: 'var(--text-secondary)',
                marginBottom: '6px',
              }}
            >
              Process Limit (0 = Full Video)
            </label>
            <input
              type="number"
              min="0"
              max="7200"
              step="5"
              className="input-field"
              value={limitSeconds}
              onChange={(e) => setLimitSeconds(parseFloat(e.target.value) || 0)}
              disabled={isRunning}
              placeholder="0 (full duration)"
            />
          </div>

          {/* Active Classes */}
          <h4
            style={{
              fontSize: '0.9rem',
              fontWeight: 600,
              color: 'var(--text-secondary)',
              marginBottom: '10px',
            }}
          >
            Vehicle Classes
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '16px' }}>
            <div
              className={`toggle-btn ${trackCars ? 'active' : ''}`}
              onClick={() => !isRunning && setTrackCars(!trackCars)}
            >
              <span style={{ fontSize: '0.8125rem', fontWeight: 500 }}>Cars</span>
              <span style={{ fontSize: '0.75rem', color: trackCars ? '#10b981' : 'var(--text-muted)' }}>
                {trackCars ? 'ON' : 'OFF'}
              </span>
            </div>
            <div
              className={`toggle-btn ${trackMotorcycles ? 'active' : ''}`}
              onClick={() => !isRunning && setTrackMotorcycles(!trackMotorcycles)}
            >
              <span style={{ fontSize: '0.8125rem', fontWeight: 500 }}>Motorcycles</span>
              <span style={{ fontSize: '0.75rem', color: trackMotorcycles ? '#10b981' : 'var(--text-muted)' }}>
                {trackMotorcycles ? 'ON' : 'OFF'}
              </span>
            </div>
            <div
              className={`toggle-btn ${trackBuses ? 'active' : ''}`}
              onClick={() => !isRunning && setTrackBuses(!trackBuses)}
            >
              <span style={{ fontSize: '0.8125rem', fontWeight: 500 }}>Buses</span>
              <span style={{ fontSize: '0.75rem', color: trackBuses ? '#10b981' : 'var(--text-muted)' }}>
                {trackBuses ? 'ON' : 'OFF'}
              </span>
            </div>
            <div
              className={`toggle-btn ${trackTrucks ? 'active' : ''}`}
              onClick={() => !isRunning && setTrackTrucks(!trackTrucks)}
            >
              <span style={{ fontSize: '0.8125rem', fontWeight: 500 }}>Trucks</span>
              <span style={{ fontSize: '0.75rem', color: trackTrucks ? '#10b981' : 'var(--text-muted)' }}>
                {trackTrucks ? 'ON' : 'OFF'}
              </span>
            </div>
            <div
              className={`toggle-btn ${trackBicycles ? 'active' : ''}`}
              onClick={() => !isRunning && setTrackBicycles(!trackBicycles)}
            >
              <span style={{ fontSize: '0.8125rem', fontWeight: 500 }}>Bicycles</span>
              <span style={{ fontSize: '0.75rem', color: trackBicycles ? '#10b981' : 'var(--text-muted)' }}>
                {trackBicycles ? 'ON' : 'OFF'}
              </span>
            </div>
          </div>

          {/* Auto-rickshaw ensemble */}
          {systemInfo?.has_rickshaw_model && (
            <div
              className={`toggle-btn ${enableRickshaw ? 'active' : ''}`}
              style={{ marginBottom: '16px' }}
              onClick={() => !isRunning && setEnableRickshaw(!enableRickshaw)}
            >
              <span style={{ fontSize: '0.8125rem', fontWeight: 500 }}>
                🛺 Auto-Rickshaw Model
              </span>
              <span style={{ fontSize: '0.75rem', color: enableRickshaw ? '#10b981' : 'var(--text-muted)' }}>
                {enableRickshaw ? 'ENSEMBLE' : 'OFF'}
              </span>
            </div>
          )}

          {/* Action Buttons */}
          <div style={{ display: 'flex', gap: '10px' }}>
            {!isRunning ? (
              <button
                className="btn btn-primary"
                style={{ flex: 1, padding: '12px' }}
                onClick={handleStartPipeline}
                disabled={isStarting}
              >
                <Play size={18} /> {isStarting ? 'Launching...' : 'Start Pipeline'}
              </button>
            ) : (
              <button
                className="btn btn-danger"
                style={{ flex: 1, padding: '12px' }}
                onClick={handleStopPipeline}
              >
                <Square size={18} /> Stop Pipeline
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Live Preview & Status Center */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div className="glass-panel" style={{ padding: '24px', flex: 1, display: 'flex', flexDirection: 'column' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '16px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Eye size={18} color="var(--accent-cyan)" />
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>
                Live Detection Stream
              </h3>
            </div>
            {isRunning && (
              <span
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  color: 'var(--danger)',
                  letterSpacing: '0.05em',
                }}
              >
                <span className="live-indicator" /> LIVE
              </span>
            )}
          </div>

          {/* Preview Viewport */}
          <div
            style={{
              flex: 1,
              minHeight: '360px',
              borderRadius: 'var(--radius-md)',
              overflow: 'hidden',
              border: '1px solid var(--border-subtle)',
              background: '#040711',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative',
            }}
          >
            {jobStatus?.preview_base64 ? (
              <img
                src={`data:image/jpeg;base64,${jobStatus.preview_base64}`}
                alt="Live Preview"
                style={{ width: '100%', height: '100%', objectFit: 'contain' }}
              />
            ) : (
              <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                <Clock size={48} style={{ opacity: 0.3, marginBottom: '12px' }} />
                <p style={{ fontSize: '0.875rem' }}>
                  {isRunning
                    ? 'Warming up neural network & tracking engine...'
                    : 'Click "Start Pipeline" to begin live processing.'}
                </p>
              </div>
            )}
          </div>

          {/* Progress & Metrics */}
          {jobStatus && (
            <div style={{ marginTop: '20px' }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '8px',
                  fontSize: '0.875rem',
                }}
              >
                <span style={{ fontWeight: 600 }}>
                  Progress:{' '}
                  <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-primary)' }}>
                    {Math.round(jobStatus.progress * 100)}%
                  </span>
                </span>
                <span style={{ color: 'var(--text-secondary)' }}>
                  ETA:{' '}
                  <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
                    {Math.round(jobStatus.eta_s)}s
                  </span>
                </span>
              </div>

              {/* Progress bar */}
              <div
                style={{
                  height: '8px',
                  borderRadius: '4px',
                  background: 'rgba(255, 255, 255, 0.08)',
                  overflow: 'hidden',
                  position: 'relative',
                }}
              >
                <div
                  style={{
                    height: '100%',
                    width: `${Math.min(100, jobStatus.progress * 100)}%`,
                    background: 'linear-gradient(90deg, #6366f1, #06b6d4)',
                    borderRadius: '4px',
                    transition: 'width 0.2s linear',
                  }}
                />
              </div>

              {/* Status messages */}
              {jobStatus.status === 'completed' && (
                <div
                  style={{
                    marginTop: '16px',
                    padding: '14px 18px',
                    borderRadius: 'var(--radius-md)',
                    background: 'rgba(16, 185, 129, 0.12)',
                    border: '1px solid rgba(16, 185, 129, 0.3)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <CheckCircle2 color="#10b981" size={20} />
                    <span style={{ fontWeight: 600, color: '#34d399', fontSize: '0.9rem' }}>
                      Processing Complete!
                    </span>
                  </div>
                  <button className="btn btn-primary" onClick={onProceedToResults}>
                    View Analytics <ArrowRight size={16} />
                  </button>
                </div>
              )}

              {jobStatus.status === 'error' && (
                <div
                  style={{
                    marginTop: '16px',
                    padding: '14px',
                    borderRadius: 'var(--radius-md)',
                    background: 'rgba(239, 68, 68, 0.12)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    color: '#fca5a5',
                    fontSize: '0.875rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                  }}
                >
                  <AlertCircle size={20} />
                  <span>Execution Error: {jobStatus.error}</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
