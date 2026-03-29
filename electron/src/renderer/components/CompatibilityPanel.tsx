import { useState, useCallback, useEffect } from 'react'
import type { CompatibilityCheck } from '../../../../shared/messages'
import { colors } from '../theme/colors'

interface CompatibilityPanelProps {
  currentStlBase64: string
  autoCheck?: boolean
}

type Overall = 'pass' | 'warning' | 'fail' | 'unknown'

interface CompatibilityState {
  checks: CompatibilityCheck[]
  stats: Record<string, number | string>
  overall: Overall
}

const severityIcon: Record<string, string> = {
  info: '\u2705',     // green check
  warning: '\u26A0',  // warning triangle
  error: '\u274C',    // red X
}

const overallColor: Record<Overall, string> = {
  pass: colors.success,
  warning: colors.warning,
  fail: colors.error,
  unknown: colors.textMuted,
}

export function CompatibilityPanel({ currentStlBase64, autoCheck = true }: CompatibilityPanelProps) {
  const [state, setState] = useState<CompatibilityState | null>(null)
  const [checking, setChecking] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const runCheck = useCallback(async () => {
    if (!currentStlBase64) return
    setChecking(true)
    setError(null)
    try {
      const response = await window.caddee.sendToSidecar({
        id: crypto.randomUUID(),
        type: 'check_compatibility',
        stlBase64: currentStlBase64,
      })
      if (response.type === 'compatibility_result') {
        setState({
          checks: response.checks,
          stats: response.stats,
          overall: response.overall,
        })
      } else if (response.type === 'error') {
        setError(response.error)
      }
    } catch (e) {
      setError(String(e))
    } finally {
      setChecking(false)
    }
  }, [currentStlBase64])

  // Auto-check when STL changes
  useEffect(() => {
    if (autoCheck && currentStlBase64) {
      runCheck()
    }
  }, [currentStlBase64, autoCheck, runCheck])

  if (!currentStlBase64) {
    return <div style={styles.empty}>No model to analyze.</div>
  }

  return (
    <div style={styles.container}>
      <div style={styles.toolbar}>
        <button
          onClick={runCheck}
          disabled={checking}
          style={{
            ...styles.checkButton,
            opacity: checking ? 0.6 : 1,
          }}
        >
          {checking ? 'Checking...' : 'Run Check'}
        </button>
        {state && (
          <span style={{ ...styles.overallBadge, color: overallColor[state.overall] }}>
            {state.overall.toUpperCase()}
          </span>
        )}
      </div>

      {error && <div style={styles.errorText}>{error}</div>}

      {state && (
        <>
          <div style={styles.checkList}>
            {state.checks.map((check, i) => (
              <div key={i} style={styles.checkItem}>
                <span style={styles.checkIcon}>{severityIcon[check.severity] ?? '?'}</span>
                <div style={styles.checkContent}>
                  <div style={styles.checkName}>{formatCheckName(check.name)}</div>
                  <div style={styles.checkMessage}>{check.message}</div>
                </div>
              </div>
            ))}
          </div>

          {Object.keys(state.stats).length > 0 && (
            <div style={styles.statsSection}>
              <div style={styles.statsTitle}>Mesh Stats</div>
              {Object.entries(state.stats).map(([key, val]) => (
                <div key={key} style={styles.statRow}>
                  <span style={styles.statKey}>{formatStatKey(key)}</span>
                  <span style={styles.statVal}>{formatStatVal(key, val)}</span>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}

function formatCheckName(name: string): string {
  return name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function formatStatKey(key: string): string {
  return key.replace(/([A-Z])/g, ' $1').replace(/^./, c => c.toUpperCase())
}

function formatStatVal(key: string, val: number | string): string {
  if (key === 'boundingBox' && Array.isArray(val)) {
    return val.map((v: number) => v.toFixed(2)).join(' x ')
  }
  if (typeof val === 'number') {
    return Number.isInteger(val) ? val.toLocaleString() : val.toFixed(4)
  }
  return String(val)
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
  },
  toolbar: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
  },
  checkButton: {
    padding: '6px 14px',
    background: colors.bgElevated,
    border: `1px solid ${colors.border}`,
    borderRadius: 6,
    color: colors.textPrimary,
    fontSize: 12,
    fontWeight: 500,
    fontFamily: 'inherit',
    cursor: 'pointer',
  },
  overallBadge: {
    fontSize: 11,
    fontWeight: 700,
    letterSpacing: 1,
  },
  errorText: {
    color: colors.error,
    fontSize: 12,
    padding: '4px 0',
  },
  checkList: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
  },
  checkItem: {
    display: 'flex',
    gap: 8,
    padding: '6px 8px',
    background: colors.bgPanel,
    borderRadius: 4,
  },
  checkIcon: {
    fontSize: 14,
    lineHeight: '20px',
    flexShrink: 0,
  },
  checkContent: {
    flex: 1,
    minWidth: 0,
  },
  checkName: {
    fontSize: 12,
    fontWeight: 600,
    color: colors.textPrimary,
    marginBottom: 2,
  },
  checkMessage: {
    fontSize: 11,
    color: colors.textSecondary,
    lineHeight: 1.4,
  },
  statsSection: {
    marginTop: 4,
    padding: '8px',
    background: colors.bgPanel,
    borderRadius: 4,
  },
  statsTitle: {
    fontSize: 11,
    fontWeight: 600,
    color: colors.textSecondary,
    textTransform: 'uppercase' as const,
    letterSpacing: 0.8,
    marginBottom: 6,
  },
  statRow: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '2px 0',
  },
  statKey: {
    fontSize: 11,
    color: colors.textSecondary,
  },
  statVal: {
    fontSize: 11,
    color: colors.textPrimary,
    fontFamily: 'monospace',
  },
  empty: {
    color: colors.textMuted,
    fontSize: 12,
    textAlign: 'center',
    padding: '8px 0',
  },
}
