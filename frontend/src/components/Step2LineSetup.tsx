import React, { useState, useRef, useEffect, useCallback } from 'react'
import {
  Download,
  Upload,
  ArrowRight,
  Sliders,
  Sparkles,
} from 'lucide-react'
import type { CountingLineConfig, UploadResponse } from '../types'

interface Step2LineSetupProps {
  video: UploadResponse
  lineConfig: CountingLineConfig | null
  onSaveLine: (config: CountingLineConfig) => void
  onProceed: () => void
}

export const Step2LineSetup: React.FC<Step2LineSetupProps> = ({
  video,
  lineConfig,
  onSaveLine,
  onProceed,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [imageLoaded, setImageLoaded] = useState(false)
  const imageRef = useRef<HTMLImageElement | null>(null)

  const w = video.metadata.width
  const h = video.metadata.height

  // Default line if none provided: horizontal middle line
  const [p1, setP1] = useState<[number, number]>(
    lineConfig ? lineConfig.p1 : [w * 0.1, h * 0.5]
  )
  const [p2, setP2] = useState<[number, number]>(
    lineConfig ? lineConfig.p2 : [w * 0.9, h * 0.5]
  )
  const [offsetPx, setOffsetPx] = useState<number>(
    lineConfig ? lineConfig.offset_px : 30.0
  )
  const [dirAtoB, setDirAtoB] = useState<string>(
    lineConfig ? lineConfig.dir_a_to_b : 'entry'
  )
  const [dirBtoA, setDirBtoA] = useState<string>(
    lineConfig ? lineConfig.dir_b_to_a : 'exit'
  )

  const [activeHandle, setActiveHandle] = useState<'p1' | 'p2' | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Load first frame image
  useEffect(() => {
    const img = new Image()
    img.crossOrigin = 'anonymous'
    img.src = video.first_frame_url
    img.onload = () => {
      imageRef.current = img
      setImageLoaded(true)
    }
  }, [video.first_frame_url])

  // Save changes upstream whenever points/offset change
  useEffect(() => {
    onSaveLine({
      p1,
      p2,
      offset_px: offsetPx,
      dir_a_to_b: dirAtoB,
      dir_b_to_a: dirBtoA,
    })
  }, [p1, p2, offsetPx, dirAtoB, dirBtoA, onSaveLine])

  // Draw canvas scene
  const drawCanvas = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas || !imageRef.current) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    canvas.width = w
    canvas.height = h

    // 1. Draw base video frame
    ctx.drawImage(imageRef.current, 0, 0, w, h)

    const [x1, y1] = p1
    const [x2, y2] = p2

    // Compute unit normal vector for gate offset
    const dx = x2 - x1
    const dy = y2 - y1
    const len = Math.sqrt(dx * dx + dy * dy)

    if (len > 0.001) {
      const nx = -dy / len
      const ny = dx / len

      // Side A gate line (+normal)
      const ga1_x = x1 + nx * offsetPx
      const ga1_y = y1 + ny * offsetPx
      const ga2_x = x2 + nx * offsetPx
      const ga2_y = y2 + ny * offsetPx

      // Side B gate line (-normal)
      const gb1_x = x1 - nx * offsetPx
      const gb1_y = y1 - ny * offsetPx
      const gb2_x = x2 - nx * offsetPx
      const gb2_y = y2 - ny * offsetPx

      // Draw Gate A line
      ctx.beginPath()
      ctx.setLineDash([8, 6])
      ctx.moveTo(ga1_x, ga1_y)
      ctx.lineTo(ga2_x, ga2_y)
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.7)'
      ctx.lineWidth = 2
      ctx.stroke()

      // Draw Gate B line
      ctx.beginPath()
      ctx.moveTo(gb1_x, gb1_y)
      ctx.lineTo(gb2_x, gb2_y)
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.7)'
      ctx.lineWidth = 2
      ctx.stroke()
      ctx.setLineDash([])

      // Labels with background
      ctx.font = 'bold 16px Inter, sans-serif'

      // Label Side A
      ctx.fillStyle = 'rgba(16, 185, 129, 0.9)'
      ctx.fillText(
        `Side A (${dirAtoB} →)`,
        Math.min(ga1_x, ga2_x) + 12,
        Math.min(ga1_y, ga2_y) - 8
      )

      // Label Side B
      ctx.fillStyle = 'rgba(6, 182, 212, 0.9)'
      ctx.fillText(
        `Side B (← ${dirBtoA})`,
        Math.min(gb1_x, gb2_x) + 12,
        Math.min(gb1_y, gb2_y) - 8
      )
    }

    // 2. Draw Main Virtual Counting Line
    ctx.beginPath()
    ctx.moveTo(x1, y1)
    ctx.lineTo(x2, y2)
    ctx.strokeStyle = '#f59e0b'
    ctx.lineWidth = 4
    ctx.stroke()

    // 3. Draw Handle Handles with Glow
    const drawHandle = (x: number, y: number, color: string, label: string) => {
      ctx.beginPath()
      ctx.arc(x, y, 14, 0, Math.PI * 2)
      ctx.fillStyle = color
      ctx.fill()
      ctx.lineWidth = 3
      ctx.strokeStyle = '#ffffff'
      ctx.stroke()

      ctx.fillStyle = '#ffffff'
      ctx.font = 'bold 12px Inter, sans-serif'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(label, x, y)
    }

    drawHandle(x1, y1, '#10b981', 'A')
    drawHandle(x2, y2, '#ef4444', 'B')
  }, [w, h, p1, p2, offsetPx, dirAtoB, dirBtoA])

  useEffect(() => {
    if (imageLoaded) {
      drawCanvas()
    }
  }, [imageLoaded, drawCanvas])

  // Mouse / Touch Interaction for Dragging Handles
  const getCanvasCoords = (e: React.MouseEvent<HTMLCanvasElement>): [number, number] => {
    const canvas = canvasRef.current
    if (!canvas) return [0, 0]
    const rect = canvas.getBoundingClientRect()
    const scaleX = canvas.width / rect.width
    const scaleY = canvas.height / rect.height
    return [
      (e.clientX - rect.left) * scaleX,
      (e.clientY - rect.top) * scaleY,
    ]
  }

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const [clickX, clickY] = getCanvasCoords(e)
    const distP1 = Math.hypot(clickX - p1[0], clickY - p1[1])
    const distP2 = Math.hypot(clickX - p2[0], clickY - p2[1])

    const hitRadius = 35 // tolerance in video pixels
    if (distP1 < hitRadius && distP1 <= distP2) {
      setActiveHandle('p1')
    } else if (distP2 < hitRadius) {
      setActiveHandle('p2')
    }
  }

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!activeHandle) return
    const [curX, curY] = getCanvasCoords(e)
    const clampedX = Math.max(0, Math.min(w, curX))
    const clampedY = Math.max(0, Math.min(h, curY))

    if (activeHandle === 'p1') {
      setP1([clampedX, clampedY])
    } else {
      setP2([clampedX, clampedY])
    }
  }

  const handleMouseUp = () => {
    setActiveHandle(null)
  }

  // Presets
  const applyPreset = (preset: 'horizontal' | 'vertical' | 'diagonal') => {
    if (preset === 'horizontal') {
      setP1([w * 0.05, h * 0.5])
      setP2([w * 0.95, h * 0.5])
    } else if (preset === 'vertical') {
      setP1([w * 0.5, h * 0.05])
      setP2([w * 0.5, h * 0.95])
    } else if (preset === 'diagonal') {
      setP1([w * 0.1, h * 0.2])
      setP2([w * 0.9, h * 0.8])
    }
  }

  // Export & Import Line JSON
  const downloadLineJson = () => {
    const lineData = {
      p1: [Math.round(p1[0]), Math.round(p1[1])],
      p2: [Math.round(p2[0]), Math.round(p2[1])],
      offset_px: offsetPx,
      dir_a_to_b: dirAtoB,
      dir_b_to_a: dirBtoA,
    }
    const blob = new Blob([JSON.stringify(lineData, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'counting_line.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleImportJson = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || !e.target.files[0]) return
    const file = e.target.files[0]
    const reader = new FileReader()
    reader.onload = (event) => {
      try {
        const parsed = JSON.parse(event.target?.result as string)
        if (parsed.p1 && parsed.p2) {
          setP1([parsed.p1[0], parsed.p1[1]])
          setP2([parsed.p2[0], parsed.p2[1]])
          if (parsed.offset_px) setOffsetPx(parsed.offset_px)
          if (parsed.dir_a_to_b) setDirAtoB(parsed.dir_a_to_b)
          if (parsed.dir_b_to_a) setDirBtoA(parsed.dir_b_to_a)
        }
      } catch (err) {
        alert('Invalid JSON file format')
      }
    }
    reader.readAsText(file)
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '24px' }}>
      {/* Canvas Viewport */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '16px',
          }}
        >
          <div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>
              Interactive Line Calibrator
            </h3>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
              Click and drag handle circles <b style={{ color: '#10b981' }}>A</b> and{' '}
              <b style={{ color: '#ef4444' }}>B</b> directly on the video frame.
            </p>
          </div>
          <span
            style={{
              padding: '4px 10px',
              borderRadius: '8px',
              background: 'rgba(255, 255, 255, 0.05)',
              fontSize: '0.75rem',
              fontFamily: 'var(--font-mono)',
              color: 'var(--text-muted)',
            }}
          >
            {Math.round(w)} &times; {Math.round(h)} px
          </span>
        </div>

        <div
          style={{
            position: 'relative',
            borderRadius: 'var(--radius-md)',
            overflow: 'hidden',
            border: '1px solid var(--border-subtle)',
            background: '#05070d',
          }}
        >
          <canvas
            ref={canvasRef}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            style={{
              width: '100%',
              height: 'auto',
              display: 'block',
              cursor: activeHandle ? 'grabbing' : 'crosshair',
            }}
          />
        </div>
      </div>

      {/* Control Configuration Panel */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h4
            style={{
              fontSize: '1rem',
              fontWeight: 700,
              marginBottom: '16px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <Sparkles size={18} color="var(--accent-primary)" /> Quick Presets
          </h4>

          <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
            <button
              className="btn btn-secondary"
              style={{ flex: 1, fontSize: '0.8125rem' }}
              onClick={() => applyPreset('horizontal')}
            >
              Horizontal
            </button>
            <button
              className="btn btn-secondary"
              style={{ flex: 1, fontSize: '0.8125rem' }}
              onClick={() => applyPreset('vertical')}
            >
              Vertical
            </button>
            <button
              className="btn btn-secondary"
              style={{ flex: 1, fontSize: '0.8125rem' }}
              onClick={() => applyPreset('diagonal')}
            >
              Diagonal
            </button>
          </div>

          <h4
            style={{
              fontSize: '1rem',
              fontWeight: 700,
              marginBottom: '14px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <Sliders size={18} color="var(--accent-cyan)" /> Gate & Direction Settings
          </h4>

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
                Side A → B Name
              </label>
              <input
                type="text"
                className="input-field"
                value={dirAtoB}
                onChange={(e) => setDirAtoB(e.target.value)}
              />
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
                Side B → A Name
              </label>
              <input
                type="text"
                className="input-field"
                value={dirBtoA}
                onChange={(e) => setDirBtoA(e.target.value)}
              />
            </div>
          </div>

          <div style={{ marginBottom: '20px' }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                marginBottom: '6px',
                fontSize: '0.8125rem',
              }}
            >
              <span style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>
                Gate Line Offset
              </span>
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
                {offsetPx} px
              </span>
            </div>
            <input
              type="range"
              min="10"
              max="120"
              step="5"
              className="range-slider"
              value={offsetPx}
              onChange={(e) => setOffsetPx(parseFloat(e.target.value))}
            />
          </div>

          <div style={{ display: 'flex', gap: '10px', paddingTop: '10px', borderTop: '1px solid var(--border-subtle)' }}>
            <button className="btn btn-secondary" style={{ flex: 1 }} onClick={downloadLineJson}>
              <Download size={15} /> Save JSON
            </button>
            <button
              className="btn btn-secondary"
              style={{ flex: 1 }}
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload size={15} /> Load JSON
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".json"
              style={{ display: 'none' }}
              onChange={handleImportJson}
            />
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', display: 'block' }}>
                Status
              </span>
              <span style={{ fontSize: '0.9375rem', fontWeight: 600, color: '#10b981' }}>
                Virtual Line Calibrated
              </span>
            </div>
            <button className="btn btn-primary" onClick={onProceed}>
              Proceed to Run Counter <ArrowRight size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
