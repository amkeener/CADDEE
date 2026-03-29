import { useEffect, useRef, useCallback } from 'react'
import { parseScadParams, updateScadParam, type ScadParam } from '../utils/scadParser'

interface ParameterSlidersProps {
  scadCode: string
  params: ScadParam[]
  onParamsChange: (params: ScadParam[]) => void
  onCompile: (updatedScad: string) => void
}

export function ParameterSliders({ scadCode, params, onParamsChange, onCompile }: ParameterSlidersProps) {
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const latestScadRef = useRef(scadCode)
  latestScadRef.current = scadCode

  // Re-parse params when scadCode changes (but only from external changes, not slider updates)
  const prevScadRef = useRef('')
  useEffect(() => {
    // Only re-parse if the scad code structure changed (not just a value tweak)
    if (scadCode && scadCode !== prevScadRef.current) {
      const parsed = parseScadParams(scadCode)
      if (parsed.length > 0) {
        onParamsChange(parsed)
      }
      prevScadRef.current = scadCode
    }
  }, [scadCode, onParamsChange])

  const handleChange = useCallback((name: string, newValue: number) => {
    // Update local params
    onParamsChange(params.map(p => p.name === name ? { ...p, value: newValue } : p))

    // Update scad code and debounce compile
    const updated = updateScadParam(latestScadRef.current, name, newValue)
    latestScadRef.current = updated

    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      onCompile(updated)
    }, 300)
  }, [params, onParamsChange, onCompile])

  if (params.length === 0) {
    return <div style={styles.empty}>No customizer parameters detected.</div>
  }

  // Group by section
  const sections = new Map<string, ScadParam[]>()
  for (const p of params) {
    const list = sections.get(p.section) ?? []
    list.push(p)
    sections.set(p.section, list)
  }

  return (
    <div style={styles.container}>
      {[...sections.entries()].map(([section, sectionParams]) => (
        <div key={section}>
          {sections.size > 1 && (
            <div style={styles.sectionLabel}>{section}</div>
          )}
          {sectionParams.map(p => (
            <div key={p.name} style={styles.paramRow}>
              <div style={styles.paramHeader}>
                <span style={styles.paramName}>{p.name}</span>
                <span style={styles.paramValue}>{p.value}</span>
              </div>
              <input
                type="range"
                min={p.min}
                max={p.max}
                step={p.step}
                value={p.value}
                onChange={e => handleChange(p.name, parseFloat(e.target.value))}
                style={styles.slider}
              />
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: 4,
  },
  sectionLabel: {
    fontSize: 10,
    color: '#666',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginTop: 8,
    marginBottom: 4,
  },
  paramRow: {
    marginBottom: 8,
  },
  paramHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: 3,
  },
  paramName: {
    fontSize: 12,
    color: '#aaa',
  },
  paramValue: {
    fontSize: 12,
    color: '#5588ff',
    fontVariantNumeric: 'tabular-nums',
  },
  slider: {
    width: '100%',
    height: 4,
    cursor: 'pointer',
    accentColor: '#5588ff',
  },
  empty: {
    color: '#555',
    fontSize: 12,
  },
}
