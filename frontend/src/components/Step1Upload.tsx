import React, { useState, useRef } from 'react'
import {
  UploadCloud,
  Film,
  Clock,
  Layers,
  ArrowRight,
  AlertCircle,
  CheckCircle,
} from 'lucide-react'
import type { UploadResponse } from '../types'

interface Step1UploadProps {
  onVideoUploaded: (data: UploadResponse) => void
  currentVideo: UploadResponse | null
  onProceed: () => void
}

export const Step1Upload: React.FC<Step1UploadProps> = ({
  onVideoUploaded,
  currentVideo,
  onProceed,
}) => {
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileUpload = async (file: File) => {
    if (!file) return

    const validExtensions = ['.mp4', '.avi', '.mov', '.mkv']
    const hasValidExt = validExtensions.some((ext) =>
      file.name.toLowerCase().endsWith(ext)
    )
    if (!hasValidExt) {
      setErrorMsg('Please select a valid video file (.mp4, .avi, .mov, or .mkv)')
      return
    }

    setErrorMsg(null)
    setIsUploading(true)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Upload failed')
      }

      const data: UploadResponse = await response.json()
      onVideoUploaded(data)
    } catch (err: any) {
      setErrorMsg(err.message || 'An error occurred while uploading.')
    } finally {
      setIsUploading(false)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0])
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div
        className="glass-panel"
        style={{
          padding: '36px',
          border: isDragging
            ? '2px dashed var(--accent-primary)'
            : '1px dashed var(--border-subtle)',
          borderRadius: 'var(--radius-xl)',
          textAlign: 'center',
          cursor: isUploading ? 'wait' : 'pointer',
          backgroundColor: isDragging
            ? 'rgba(99, 102, 241, 0.08)'
            : 'var(--bg-card)',
          transition: 'all 0.25s',
        }}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isUploading && fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".mp4,.avi,.mov,.mkv"
          style={{ display: 'none' }}
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              handleFileUpload(e.target.files[0])
            }
          }}
        />

        <div
          style={{
            width: '64px',
            height: '64px',
            margin: '0 auto 16px',
            borderRadius: '16px',
            background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(6, 182, 212, 0.2))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--accent-primary)',
          }}
        >
          <UploadCloud size={32} />
        </div>

        <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '8px' }}>
          {isUploading ? 'Extracting Video Metadata...' : 'Upload Traffic Video'}
        </h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '16px' }}>
          Drag and drop your video file here, or click to browse
        </p>
        <span
          style={{
            display: 'inline-block',
            padding: '4px 12px',
            borderRadius: '12px',
            background: 'rgba(255, 255, 255, 0.05)',
            fontSize: '0.75rem',
            color: 'var(--text-muted)',
            fontFamily: 'var(--font-mono)',
          }}
        >
          Supported: MP4, AVI, MOV, MKV
        </span>
      </div>

      {errorMsg && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '14px 20px',
            background: 'rgba(239, 68, 68, 0.12)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: 'var(--radius-md)',
            color: '#fca5a5',
          }}
        >
          <AlertCircle size={20} />
          <span style={{ fontSize: '0.875rem' }}>{errorMsg}</span>
        </div>
      )}

      {currentVideo && (
        <div className="glass-panel" style={{ padding: '28px' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '20px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <CheckCircle size={20} color="#10b981" />
              <h4 style={{ fontSize: '1.1rem', fontWeight: 700 }}>
                {currentVideo.filename}
              </h4>
            </div>
            <button className="btn btn-primary" onClick={onProceed}>
              Proceed to Counting Line <ArrowRight size={16} />
            </button>
          </div>

          <div className="metrics-grid">
            <div className="metric-card glass-panel">
              <span className="metric-title">
                <Film size={14} /> Resolution
              </span>
              <span className="metric-value" style={{ fontSize: '1.5rem' }}>
                {currentVideo.metadata.width} &times; {currentVideo.metadata.height}
              </span>
            </div>

            <div className="metric-card glass-panel">
              <span className="metric-title">
                <Clock size={14} /> Frame Rate
              </span>
              <span className="metric-value" style={{ fontSize: '1.5rem' }}>
                {currentVideo.metadata.fps}{' '}
                <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                  FPS
                </span>
              </span>
            </div>

            <div className="metric-card glass-panel">
              <span className="metric-title">
                <Clock size={14} /> Duration
              </span>
              <span className="metric-value" style={{ fontSize: '1.5rem' }}>
                {currentVideo.metadata.duration_s}s
              </span>
            </div>

            <div className="metric-card glass-panel">
              <span className="metric-title">
                <Layers size={14} /> Total Frames
              </span>
              <span className="metric-value" style={{ fontSize: '1.5rem' }}>
                {currentVideo.metadata.frame_count.toLocaleString()}
              </span>
            </div>
          </div>

          <div style={{ marginTop: '20px' }}>
            <span
              style={{
                fontSize: '0.8125rem',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                display: 'block',
                marginBottom: '10px',
              }}
            >
              Extracted Calibration Frame
            </span>
            <div
              style={{
                borderRadius: 'var(--radius-md)',
                overflow: 'hidden',
                border: '1px solid var(--border-subtle)',
                maxHeight: '380px',
                background: '#000',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <img
                src={currentVideo.first_frame_url}
                alt="Calibration Frame"
                style={{ width: '100%', height: 'auto', display: 'block' }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
