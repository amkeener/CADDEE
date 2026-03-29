import { useState, useRef, useCallback, useEffect, type ReactNode } from 'react'

interface ResizablePanesProps {
  left: ReactNode
  center: ReactNode
  right: ReactNode
  defaultLeftWidth?: number
  defaultRightWidth?: number
  minLeftWidth?: number
  minCenterWidth?: number
  minRightWidth?: number
}

export function ResizablePanes({
  left,
  center,
  right,
  defaultLeftWidth = 0.5,
  defaultRightWidth = 0.22,
  minLeftWidth = 200,
  minCenterWidth = 280,
  minRightWidth = 220,
}: ResizablePanesProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  // Store fractions (0–1) of container width
  const [leftFrac, setLeftFrac] = useState(defaultLeftWidth)
  const [rightFrac, setRightFrac] = useState(defaultRightWidth)
  const dragging = useRef<'left' | 'right' | null>(null)

  const handleMouseMove = useCallback((e: MouseEvent) => {
    const container = containerRef.current
    if (!container || !dragging.current) return

    const rect = container.getBoundingClientRect()
    const totalWidth = rect.width
    const x = e.clientX - rect.left

    if (dragging.current === 'left') {
      let newLeftFrac = x / totalWidth
      const minLeftFrac = minLeftWidth / totalWidth
      const maxLeftFrac = 1 - rightFrac - minCenterWidth / totalWidth
      newLeftFrac = Math.max(minLeftFrac, Math.min(maxLeftFrac, newLeftFrac))
      setLeftFrac(newLeftFrac)
    } else {
      let newRightFrac = 1 - x / totalWidth
      const minRightFrac = minRightWidth / totalWidth
      const maxRightFrac = 1 - leftFrac - minCenterWidth / totalWidth
      newRightFrac = Math.max(minRightFrac, Math.min(maxRightFrac, newRightFrac))
      setRightFrac(newRightFrac)
    }
  }, [leftFrac, rightFrac, minLeftWidth, minCenterWidth, minRightWidth])

  const handleMouseUp = useCallback(() => {
    dragging.current = null
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
  }, [])

  useEffect(() => {
    window.addEventListener('mousemove', handleMouseMove)
    window.addEventListener('mouseup', handleMouseUp)
    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('mouseup', handleMouseUp)
    }
  }, [handleMouseMove, handleMouseUp])

  const startDrag = (handle: 'left' | 'right') => {
    dragging.current = handle
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }

  const centerFrac = 1 - leftFrac - rightFrac
  const leftPct = `${leftFrac * 100}%`
  const centerPct = `${centerFrac * 100}%`
  const rightPct = `${rightFrac * 100}%`

  return (
    <div ref={containerRef} style={styles.container}>
      <div style={{ ...styles.pane, width: leftPct }}>{left}</div>
      <div style={styles.handle} onMouseDown={() => startDrag('left')} />
      <div style={{ ...styles.pane, width: centerPct }}>{center}</div>
      <div style={styles.handle} onMouseDown={() => startDrag('right')} />
      <div style={{ ...styles.pane, width: rightPct }}>{right}</div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    height: '100vh',
    width: '100vw',
    overflow: 'hidden',
  },
  pane: {
    height: '100%',
    overflow: 'hidden',
    minWidth: 0,
  },
  handle: {
    width: 4,
    cursor: 'col-resize',
    background: '#2a2a3e',
    flexShrink: 0,
    transition: 'background 0.15s',
  },
}
