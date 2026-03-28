import { useState } from 'react'
import { Viewport } from './components/Viewport'
import { ChatConsole } from './components/ChatConsole'

export function App() {
  const [stlData, setStlData] = useState<ArrayBuffer | null>(null)
  const [isCompiling, setIsCompiling] = useState(false)

  return (
    <div style={{
      display: 'flex',
      height: '100vh',
      width: '100vw',
      overflow: 'hidden',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    }}>
      <div style={{ flex: 1, minWidth: 0 }}>
        <Viewport stlData={stlData} isCompiling={isCompiling} />
      </div>
      <div style={{ width: 400, borderLeft: '1px solid #333', display: 'flex', flexDirection: 'column' }}>
        <ChatConsole
          onStlUpdate={setStlData}
          onCompileStateChange={setIsCompiling}
        />
      </div>
    </div>
  )
}
