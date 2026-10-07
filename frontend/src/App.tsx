import React, { useState, useEffect } from 'react'
import { Header } from './components/Header'
import { TabNav } from './components/TabNav'
import type { TabId } from './components/TabNav'
import { Step1Upload } from './components/Step1Upload'
import { Step2LineSetup } from './components/Step2LineSetup'
import { Step3RunCounter } from './components/Step3RunCounter'
import { Step4Results } from './components/Step4Results'
import { Step5Evaluation } from './components/Step5Evaluation'
import type { CountingLineConfig, SystemInfo, UploadResponse } from './types'

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabId>('upload')
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null)
  const [currentVideo, setCurrentVideo] = useState<UploadResponse | null>(null)
  const [lineConfig, setLineConfig] = useState<CountingLineConfig | null>(null)
  const [completedJobId, setCompletedJobId] = useState<string | null>(null)
  const [currentJobStatus, setCurrentJobStatus] = useState<string>('idle')

  // Fetch System Information
  useEffect(() => {
    fetch('/api/system')
      .then((res) => res.json())
      .then((data: SystemInfo) => setSystemInfo(data))
      .catch((err) => console.error('Error fetching system info:', err))
  }, [])

  // Auto-initialize line config when video is uploaded
  const handleVideoUploaded = (videoData: UploadResponse) => {
    setCurrentVideo(videoData)
    const w = videoData.metadata.width
    const h = videoData.metadata.height

    const defaultLine: CountingLineConfig = {
      p1: [w * 0.1, h * 0.5],
      p2: [w * 0.9, h * 0.5],
      offset_px: 30.0,
      dir_a_to_b: 'entry',
      dir_b_to_a: 'exit',
    }
    setLineConfig(defaultLine)
  }

  const handleJobCompleted = (jobId: string) => {
    setCompletedJobId(jobId)
    setCurrentJobStatus('completed')
  }

  return (
    <div className="app-container">
      <Header systemInfo={systemInfo} currentJobStatus={currentJobStatus} />

      <TabNav
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        hasVideo={Boolean(currentVideo)}
        hasLine={Boolean(lineConfig)}
        hasResults={Boolean(completedJobId)}
      />

      <main>
        {activeTab === 'upload' && (
          <Step1Upload
            onVideoUploaded={handleVideoUploaded}
            currentVideo={currentVideo}
            onProceed={() => setActiveTab('line')}
          />
        )}

        {activeTab === 'line' && currentVideo && (
          <Step2LineSetup
            video={currentVideo}
            lineConfig={lineConfig}
            onSaveLine={setLineConfig}
            onProceed={() => setActiveTab('run')}
          />
        )}

        {activeTab === 'run' && currentVideo && lineConfig && (
          <Step3RunCounter
            systemInfo={systemInfo}
            video={currentVideo}
            lineConfig={lineConfig}
            onJobCompleted={handleJobCompleted}
            onProceedToResults={() => setActiveTab('results')}
          />
        )}

        {activeTab === 'results' && completedJobId && (
          <Step4Results
            jobId={completedJobId}
            onProceedToEval={() => setActiveTab('eval')}
          />
        )}

        {activeTab === 'eval' && completedJobId && (
          <Step5Evaluation jobId={completedJobId} />
        )}
      </main>
    </div>
  )
}

export default App
