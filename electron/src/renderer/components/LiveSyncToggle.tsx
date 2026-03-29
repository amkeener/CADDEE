import { useState, useCallback, useEffect, useRef } from 'react'

interface LiveSyncToggleProps {
  currentStlBase64: string
  enabled: boolean
  onToggle: (enabled: boolean) => void
}

export function LiveSyncToggle({ currentStlBase64, enabled, onToggle }: LiveSyncToggleProps) {
  const [connected, setConnected] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const prevStlRef = useRef<string>('')

  // Check connection status periodically when enabled
  useEffect(() => {
    if (!enabled) {
      setConnected(false)
      return
    }

    const checkConnection = async () => {
      try {
        const response = await window.caddee.sendToSidecar({
          id: crypto.randomUUID(),
          type: 'live_sync',
          stlBase64: '',
          action: 'check',
        })
        if (response.type === 'live_sync_result') {
          setConnected(response.connected)
          if (!response.connected) {
            setError('FreeCAD not detected. Start FreeCAD with remote scripting enabled.')
          } else {
            setError(null)
          }
        }
      } catch {
        setConnected(false)
      }
    }

    checkConnection()
    const interval = setInterval(checkConnection, 5000)
    return () => clearInterval(interval)
  }, [enabled])

  // Auto-push when STL changes and sync is enabled + connected
  useEffect(() => {
    if (!enabled || !connected || !currentStlBase64 || currentStlBase64 === prevStlRef.current) return
    prevStlRef.current = currentStlBase64

    const push = async () => {
      setSyncing(true)
      try {
        const response = await window.caddee.sendToSidecar({
          id: crypto.randomUUID(),
          type: 'live_sync',
          stlBase64: currentStlBase64,
          action: 'push',
        })
        if (response.type === 'live_sync_result' && !response.success) {
          setError(response.error ?? 'Push failed')
        }
      } catch (e) {
        setError(String(e))
      } finally {
        setSyncing(false)
      }
    }

    push()
  }, [enabled, connected, currentStlBase64])

  const handleToggle = useCallback(() => {
    setError(null)
    onToggle(!enabled)
  }, [enabled, onToggle])

  return (
    <div style={styles.container}>
      <div style={styles.row}>
        <label style={styles.label}>
          <input
            type="checkbox"
            checked={enabled}
            onChange={handleToggle}
            style={styles.checkbox}
          />
          Live Sync
        </label>
        <span style={{
          ...styles.statusDot,
          background: !enabled ? '#555' : connected ? '#4caf50' : '#f44336',
        }} />
        <span style={styles.statusText}>
          {!enabled ? 'Off' : connected ? (syncing ? 'Syncing...' : 'Connected') : 'Disconnected'}
        </span>
      </div>
      {error && enabled && <div style={styles.error}>{error}</div>}
      {enabled && !connected && (
        <div style={styles.hint}>
          Start FreeCAD and enable remote scripting (port 12345).
        </div>
      )}
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
  },
  row: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
  },
  label: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    fontSize: 13,
    color: '#ccc',
    cursor: 'pointer',
  },
  checkbox: {
    accentColor: '#7c8aff',
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: '50%',
    flexShrink: 0,
  },
  statusText: {
    fontSize: 11,
    color: '#888',
  },
  error: {
    color: '#f44336',
    fontSize: 11,
    padding: '4px 0',
  },
  hint: {
    color: '#666',
    fontSize: 11,
    lineHeight: 1.4,
  },
}
