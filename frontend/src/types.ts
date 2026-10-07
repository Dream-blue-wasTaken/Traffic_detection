export interface SystemInfo {
  device: string
  device_badge: string
  models: string[]
  available_local_models: string[]
  default_model: string
  has_rickshaw_model: boolean
}

export interface VideoMetadata {
  width: number
  height: number
  fps: number
  duration_s: number
  frame_count: number
}

export interface UploadResponse {
  success: boolean
  video_id: string
  filename: string
  video_path: string
  first_frame_url: string
  metadata: VideoMetadata
}

export interface Point {
  x: number
  y: number
}

export interface CountingLineConfig {
  p1: [number, number]
  p2: [number, number]
  offset_px: number
  dir_a_to_b: string
  dir_b_to_a: string
}

export interface PipelineParams {
  model_weights: string
  tracker: string
  conf_threshold: number
  img_size: number
  interval_minutes: number
  counting_mode: 'simple' | 'gated'
  active_classes: Record<string, number>
  enable_rickshaw: boolean
  limit_seconds: number
}

export interface PipelineStatus {
  job_id: string
  status: 'queued' | 'running' | 'completed' | 'error' | 'stopped'
  progress: number
  eta_s: number
  preview_base64: string | null
  error: string | null
  has_result: boolean
}

export interface CrossingEvent {
  track_id: number
  class_name: string
  direction: string
  timestamp_s: number
}

export interface RunResults {
  job_id: string
  total_vehicles: number
  totals: Record<string, Record<string, number>>
  summary: Record<string, any>
  intervals: Record<string, any>[]
  events: CrossingEvent[]
  annotated_video_available: boolean
  video_url: string | null
  output_dir: string | null
}

export interface EvalMetrics {
  total_count_metrics: {
    manual: number
    auto: number
    accuracy_pct: number
    signed_error_pct: number
  }
  event_metrics?: {
    precision: number
    recall: number
    f1: number
  }
  plots: { name: string; url: string }[]
}
