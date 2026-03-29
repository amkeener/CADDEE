import { useState, useRef, useCallback, useEffect } from 'react'
import { createLogger } from './utils/logger'
import { ResizablePanes } from './components/ResizablePanes'

const log = createLogger('app')
import { Viewport } from './components/Viewport'
import { ChatConsole } from './components/ChatConsole'
import { ToolsPanel } from './components/ToolsPanel'
import { ExportButtons } from './components/ExportButtons'
import { IterationHistory } from './components/IterationHistory'
import { ParameterSliders } from './components/ParameterSliders'
import { CompatibilityPanel } from './components/CompatibilityPanel'
import { LiveSyncToggle } from './components/LiveSyncToggle'
import { ImportWizard, type ImportedFile } from './components/ImportWizard'
import { ApiKeyModal } from './components/ApiKeyModal'
import type { ScadParam } from './utils/scadParser'
import type { ChatMessage } from './types/messages'

export interface Iteration {
  id: string
  prompt: string
  scadCode: string
  stlBase64: string
  thumbnail: string
  timestamp: number
}

export function App() {
  const [stlData, setStlData] = useState<ArrayBuffer | null>(null)
  const [isCompiling, setIsCompiling] = useState(false)
  const [currentScad, setCurrentScad] = useState<string>('')
  const [currentStlBase64, setCurrentStlBase64] = useState<string>('')
  const [iterations, setIterations] = useState<Iteration[]>([])
  const [params, setParams] = useState<ScadParam[]>([])
  const [liveSyncEnabled, setLiveSyncEnabled] = useState(false)
  const [showImportWizard, setShowImportWizard] = useState(false)
  const [showApiKeyModal, setShowApiKeyModal] = useState(false)
  const [apiKeyConfigured, setApiKeyConfigured] = useState(true)
  const [capabilities, setCapabilities] = useState<{ stepExport: boolean; fcstdExport: boolean }>({ stepExport: false, fcstdExport: false })
  const captureThumbRef = useRef<(() => string) | null>(null)
  const chatMessagesRef = useRef<ChatMessage[]>([])
  const setChatMessagesRef = useRef<((msgs: ChatMessage[]) => void) | null>(null)

  // Session save handler
  const handleSaveSession = useCallback(async () => {
    const response = await window.caddee.sendToSidecar({
      id: crypto.randomUUID(),
      type: 'save_session',
    })
    if (response.type === 'session_data') {
      const sessionFile = {
        ...response.sessionData,
        uiIterations: iterations.map(({ stlBase64: _stl, ...rest }) => rest),
      }
      await window.caddee.saveSession(JSON.stringify(sessionFile, null, 2))
    }
  }, [iterations])

  // Session load handler
  const handleOpenSession = useCallback(async () => {
    const result = await window.caddee.openSession()
    if (!result.success || !result.data) return

    const sessionData = JSON.parse(result.data)

    // Restore sidecar state
    await window.caddee.sendToSidecar({
      id: crypto.randomUUID(),
      type: 'load_session',
      sessionData,
    })

    // Restore frontend state from session data
    const convMessages = sessionData.conversation ?? []
    const restoredMessages: ChatMessage[] = convMessages.map((m: { role: string; content: string }, i: number) => ({
      id: `restored-${i}`,
      role: m.role === 'user' ? 'user' : 'assistant',
      content: m.content,
      timestamp: Date.now(),
    }))
    setChatMessagesRef.current?.(restoredMessages)

    if (sessionData.current_scad) {
      setCurrentScad(sessionData.current_scad)
    }

    // Restore last iteration's STL if available
    const iters = sessionData.iterations ?? []
    if (iters.length > 0) {
      const last = iters[iters.length - 1]
      if (last.stl_base64) {
        const binary = atob(last.stl_base64)
        const bytes = new Uint8Array(binary.length)
        for (let i = 0; i < binary.length; i++) {
          bytes[i] = binary.charCodeAt(i)
        }
        setStlData(bytes.buffer)
        setCurrentStlBase64(last.stl_base64)
      }
    }

    // Restore iteration history (thumbnails won't be available from file)
    const restoredIterations: Iteration[] = iters.map((it: { prompt: string; scad_code: string; stl_base64: string; timestamp: number }, i: number) => ({
      id: `restored-${i}`,
      prompt: it.prompt,
      scadCode: it.scad_code,
      stlBase64: it.stl_base64,
      thumbnail: '',
      timestamp: it.timestamp * 1000,
    }))
    setIterations(restoredIterations)
  }, [])

  // Fetch capabilities on mount
  useEffect(() => {
    log.info('App mounted — fetching capabilities')
    window.caddee.sendToSidecar({
      id: crypto.randomUUID(),
      type: 'get_capabilities',
    }).then(response => {
      if (response.type === 'capabilities') {
        log.info('Capabilities: STEP=%s, FCStd=%s',
          response.capabilities.stepExport, response.capabilities.fcstdExport)
        setCapabilities({
          stepExport: response.capabilities.stepExport,
          fcstdExport: response.capabilities.fcstdExport,
        })
      }
    }).catch((err) => {
      log.error('Failed to fetch capabilities: %s', err)
    })
  }, [])

  // Check API key status on mount
  useEffect(() => {
    window.caddee.getApiKeyStatus().then(result => {
      log.info('API key status: configured=%s source=%s', result.configured, result.source)
      setApiKeyConfigured(result.configured)
      if (!result.configured) {
        setShowApiKeyModal(true)
      }
    })
    const cleanup = window.caddee.onApiKeyMissing(() => {
      log.warn('API key missing event received')
      setApiKeyConfigured(false)
      setShowApiKeyModal(true)
    })
    return cleanup
  }, [])

  // Handle imported file
  const handleImport = useCallback((result: ImportedFile) => {
    if (result.scadCode) {
      setCurrentScad(result.scadCode)
    }
    if (result.stlBase64) {
      const binary = atob(result.stlBase64)
      const bytes = new Uint8Array(binary.length)
      for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i)
      }
      setStlData(bytes.buffer)
      setCurrentStlBase64(result.stlBase64)
    }
  }, [])

  // Listen for menu events
  useEffect(() => {
    const cleanupSave = window.caddee.onMenuSaveSession(handleSaveSession)
    const cleanupOpen = window.caddee.onMenuOpenSession(handleOpenSession)
    const cleanupImport = window.caddee.onMenuImportFile(() => setShowImportWizard(true))
    return () => {
      cleanupSave()
      cleanupOpen()
      cleanupImport()
    }
  }, [handleSaveSession, handleOpenSession])

  const handleStlUpdate = useCallback((data: ArrayBuffer | null, scadCode?: string, stlBase64?: string) => {
    setStlData(data)
    if (scadCode !== undefined) setCurrentScad(scadCode)
    if (stlBase64 !== undefined) setCurrentStlBase64(stlBase64)
  }, [])

  const addIteration = useCallback((prompt: string, scadCode: string, stlBase64: string) => {
    const thumb = captureThumbRef.current?.() ?? ''
    const iteration: Iteration = {
      id: crypto.randomUUID(),
      prompt,
      scadCode,
      stlBase64,
      thumbnail: thumb,
      timestamp: Date.now(),
    }
    setIterations(prev => [...prev, iteration])
  }, [])

  const restoreIteration = useCallback((iteration: Iteration) => {
    const binary = atob(iteration.stlBase64)
    const bytes = new Uint8Array(binary.length)
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i)
    }
    setStlData(bytes.buffer)
    setCurrentScad(iteration.scadCode)
    setCurrentStlBase64(iteration.stlBase64)
  }, [])

  const handleOpenSettings = useCallback(() => {
    setShowApiKeyModal(true)
  }, [])

  const handleApiKeySaved = useCallback(() => {
    log.info('API key saved successfully')
    setApiKeyConfigured(true)
  }, [])

  const handleParameterCompile = useCallback(async (updatedScad: string) => {
    setIsCompiling(true)
    try {
      const response = await window.caddee.sendToSidecar({
        id: crypto.randomUUID(),
        type: 'update_parameters',
        scadCode: updatedScad,
      })
      if (response.type === 'parameter_response' && response.stlBase64) {
        const binary = atob(response.stlBase64)
        const bytes = new Uint8Array(binary.length)
        for (let i = 0; i < binary.length; i++) {
          bytes[i] = binary.charCodeAt(i)
        }
        setStlData(bytes.buffer)
        setCurrentScad(updatedScad)
        setCurrentStlBase64(response.stlBase64)
      }
    } finally {
      setIsCompiling(false)
    }
  }, [])

  return (
    <div style={{ fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' }}>
      <ResizablePanes
        left={
          <Viewport
            stlData={stlData}
            isCompiling={isCompiling}
            captureThumbRef={captureThumbRef}
          />
        }
        center={
          <ChatConsole
            onStlUpdate={handleStlUpdate}
            onCompileStateChange={setIsCompiling}
            onIteration={addIteration}
            iterationCount={iterations.length}
            messagesRef={chatMessagesRef}
            setMessagesRef={setChatMessagesRef}
          />
        }
        right={
          <ToolsPanel
            onOpenSettings={handleOpenSettings}
            iterationHistory={
              <IterationHistory
                iterations={iterations}
                onRestore={restoreIteration}
              />
            }
            parameterSliders={
              <ParameterSliders
                scadCode={currentScad}
                params={params}
                onParamsChange={setParams}
                onCompile={handleParameterCompile}
              />
            }
            compatibilityPanel={
              <CompatibilityPanel
                currentStlBase64={currentStlBase64}
              />
            }
            exportButtons={
              <ExportButtons
                currentScad={currentScad}
                currentStlBase64={currentStlBase64}
                capabilities={capabilities}
              />
            }
            liveSyncToggle={
              <LiveSyncToggle
                currentStlBase64={currentStlBase64}
                enabled={liveSyncEnabled}
                onToggle={setLiveSyncEnabled}
              />
            }
          />
        }
      />
      {showImportWizard && (
        <ImportWizard
          onImport={handleImport}
          onClose={() => setShowImportWizard(false)}
        />
      )}
      {showApiKeyModal && (
        <ApiKeyModal
          canClose={apiKeyConfigured}
          onClose={() => setShowApiKeyModal(false)}
          onKeySaved={handleApiKeySaved}
        />
      )}
    </div>
  )
}
