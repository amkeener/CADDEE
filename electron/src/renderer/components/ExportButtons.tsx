interface ExportButtonsProps {
  currentScad: string
  currentStlBase64: string
}

export function ExportButtons({ currentScad, currentStlBase64 }: ExportButtonsProps) {
  const hasModel = currentStlBase64.length > 0
  const hasScad = currentScad.length > 0

  const handleExportSTL = async () => {
    if (!hasModel) return
    await window.caddee.exportSTL(currentStlBase64)
  }

  const handleExportScad = async () => {
    if (!hasScad) return
    await window.caddee.exportScad(currentScad)
  }

  return (
    <div style={styles.container}>
      <button
        onClick={handleExportSTL}
        disabled={!hasModel}
        style={{
          ...styles.button,
          opacity: hasModel ? 1 : 0.4,
          cursor: hasModel ? 'pointer' : 'not-allowed',
        }}
      >
        Save STL
      </button>
      <button
        onClick={handleExportScad}
        disabled={!hasScad}
        style={{
          ...styles.button,
          opacity: hasScad ? 1 : 0.4,
          cursor: hasScad ? 'pointer' : 'not-allowed',
        }}
      >
        Save .scad
      </button>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    gap: 8,
  },
  button: {
    flex: 1,
    padding: '8px 12px',
    background: '#1a1a2e',
    border: '1px solid #333',
    borderRadius: 6,
    color: '#ccc',
    fontSize: 13,
    fontWeight: 500,
    fontFamily: 'inherit',
  },
}
