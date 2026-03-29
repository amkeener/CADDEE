import { useState, useCallback, useEffect } from 'react'

interface ApiKeyModalProps {
  onClose: () => void
  onKeySaved: () => void
  canClose: boolean
}

export function ApiKeyModal({ onClose, onKeySaved, canClose }: ApiKeyModalProps) {
  const [apiKey, setApiKey] = useState('')
  const [showKey, setShowKey] = useState(false)
  const [status, setStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle')
  const [errorMessage, setErrorMessage] = useState('')
  const [keySource, setKeySource] = useState<'env' | 'stored' | 'none'>('none')

  useEffect(() => {
    window.caddee.getApiKeyStatus().then(result => {
      setKeySource(result.source)
    })
  }, [])

  const handleSave = useCallback(async () => {
    if (!apiKey.trim()) return

    setStatus('saving')
    setErrorMessage('')

    const result = await window.caddee.saveApiKey(apiKey.trim())
    if (result.success) {
      setStatus('success')
      setApiKey('')
      setKeySource('stored')
      setTimeout(() => {
        onKeySaved()
        onClose()
      }, 800)
    } else {
      setStatus('error')
      setErrorMessage(result.error ?? 'Failed to save key')
    }
  }, [apiKey, onKeySaved, onClose])

  const handleClear = useCallback(async () => {
    await window.caddee.clearApiKey()
    setKeySource('none')
    setStatus('idle')
    setApiKey('')
  }, [])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && apiKey.trim()) {
      handleSave()
    }
  }, [apiKey, handleSave])

  return (
    <div style={styles.overlay}>
      <div style={styles.modal}>
        <div style={styles.header}>
          <span style={styles.title}>API Key Settings</span>
          {canClose && (
            <button style={styles.closeButton} onClick={onClose}>x</button>
          )}
        </div>

        <div style={styles.body}>
          <div style={styles.statusRow}>
            <span style={styles.statusLabel}>Status:</span>
            <span style={{
              ...styles.statusValue,
              color: keySource === 'none' ? '#ff6b6b' : '#51cf66',
            }}>
              {keySource === 'env' && 'Configured (environment variable)'}
              {keySource === 'stored' && 'Configured (stored)'}
              {keySource === 'none' && 'Not configured'}
            </span>
          </div>

          <label style={styles.label}>Anthropic API Key</label>
          <div style={styles.inputRow}>
            <input
              type={showKey ? 'text' : 'password'}
              value={apiKey}
              onChange={e => setApiKey(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="sk-ant-..."
              style={styles.input}
              autoFocus
            />
            <button
              style={styles.toggleButton}
              onClick={() => setShowKey(!showKey)}
              title={showKey ? 'Hide key' : 'Show key'}
            >
              {showKey ? 'Hide' : 'Show'}
            </button>
          </div>

          {status === 'error' && (
            <div style={styles.errorText}>{errorMessage}</div>
          )}
          {status === 'success' && (
            <div style={styles.successText}>Key saved and validated.</div>
          )}

          <div style={styles.actions}>
            <button
              style={{
                ...styles.saveButton,
                opacity: !apiKey.trim() || status === 'saving' ? 0.5 : 1,
              }}
              onClick={handleSave}
              disabled={!apiKey.trim() || status === 'saving'}
            >
              {status === 'saving' ? 'Validating...' : 'Save'}
            </button>
            {keySource === 'stored' && (
              <button style={styles.clearButton} onClick={handleClear}>
                Clear Stored Key
              </button>
            )}
          </div>

          <div style={styles.helpRow}>
            <span style={styles.helpText}>
              Need a key?{' '}
              <a
                href="#"
                onClick={(e) => {
                  e.preventDefault()
                  window.caddee.openExternal('https://console.anthropic.com/settings/keys')
                }}
                style={styles.link}
              >
                Get one from Anthropic Console
              </a>
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  overlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'rgba(0, 0, 0, 0.7)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  },
  modal: {
    background: '#1a1a2e',
    borderRadius: 12,
    border: '1px solid #2a2a3e',
    width: 440,
    maxWidth: '90vw',
    boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5)',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '16px 20px',
    borderBottom: '1px solid #2a2a3e',
  },
  title: {
    fontSize: 16,
    fontWeight: 600,
    color: '#fff',
  },
  closeButton: {
    background: 'none',
    border: 'none',
    color: '#888',
    fontSize: 18,
    cursor: 'pointer',
    padding: '2px 6px',
    lineHeight: 1,
  },
  body: {
    padding: '20px',
  },
  statusRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    marginBottom: 20,
  },
  statusLabel: {
    fontSize: 13,
    color: '#888',
  },
  statusValue: {
    fontSize: 13,
    fontWeight: 500,
  },
  label: {
    display: 'block',
    fontSize: 13,
    color: '#ccc',
    marginBottom: 6,
  },
  inputRow: {
    display: 'flex',
    gap: 8,
    marginBottom: 12,
  },
  input: {
    flex: 1,
    padding: '10px 12px',
    background: '#0f0f23',
    border: '1px solid #333',
    borderRadius: 6,
    color: '#fff',
    fontSize: 14,
    fontFamily: 'monospace',
    outline: 'none',
  },
  toggleButton: {
    padding: '8px 12px',
    background: '#2a2a3e',
    border: '1px solid #333',
    borderRadius: 6,
    color: '#ccc',
    fontSize: 12,
    cursor: 'pointer',
    whiteSpace: 'nowrap',
  },
  errorText: {
    color: '#ff6b6b',
    fontSize: 13,
    marginBottom: 12,
  },
  successText: {
    color: '#51cf66',
    fontSize: 13,
    marginBottom: 12,
  },
  actions: {
    display: 'flex',
    gap: 10,
    marginBottom: 16,
  },
  saveButton: {
    padding: '10px 24px',
    background: '#7c8aff',
    border: 'none',
    borderRadius: 6,
    color: '#fff',
    fontSize: 14,
    fontWeight: 500,
    cursor: 'pointer',
  },
  clearButton: {
    padding: '10px 16px',
    background: 'transparent',
    border: '1px solid #444',
    borderRadius: 6,
    color: '#ccc',
    fontSize: 13,
    cursor: 'pointer',
  },
  helpRow: {
    borderTop: '1px solid #2a2a3e',
    paddingTop: 14,
  },
  helpText: {
    fontSize: 12,
    color: '#888',
  },
  link: {
    color: '#7c8aff',
    textDecoration: 'none',
  },
}
