import { colors } from '../theme/colors'

interface ExportButtonsProps {
  currentScad: string
  currentStlBase64: string
  capabilities?: {
    stepExport: boolean
    fcstdExport: boolean
  }
}

export function ExportButtons({ currentScad, currentStlBase64, capabilities }: ExportButtonsProps) {
  const hasModel = currentStlBase64.length > 0
  const hasScad = currentScad.length > 0
  const canStep = capabilities?.stepExport ?? false
  const canFcstd = capabilities?.fcstdExport ?? false

  const handleExportSTL = async () => {
    if (!hasModel) return
    await window.caddee.exportSTL(currentStlBase64)
  }

  const handleExportScad = async () => {
    if (!hasScad) return
    await window.caddee.exportScad(currentScad)
  }

  const handleExportStep = async () => {
    if (!hasModel) return
    await window.caddee.exportStep(currentStlBase64)
  }

  const handleExportFcstd = async () => {
    if (!hasModel) return
    await window.caddee.exportFcstd(currentStlBase64)
  }

  return (
    <div style={styles.container}>
      <div style={styles.row}>
        <ExportBtn label="Save STL" onClick={handleExportSTL} enabled={hasModel} />
        <ExportBtn label="Save .scad" onClick={handleExportScad} enabled={hasScad} />
      </div>
      <div style={styles.row}>
        <ExportBtn
          label="Export STEP"
          onClick={handleExportStep}
          enabled={hasModel && canStep}
          tooltip={!canStep ? 'Requires FreeCAD' : undefined}
        />
        <ExportBtn
          label="Export .FCStd"
          onClick={handleExportFcstd}
          enabled={hasModel && canFcstd}
          tooltip={!canFcstd ? 'Requires FreeCAD' : undefined}
        />
      </div>
    </div>
  )
}

function ExportBtn({ label, onClick, enabled, tooltip }: {
  label: string
  onClick: () => void
  enabled: boolean
  tooltip?: string
}) {
  return (
    <button
      onClick={onClick}
      disabled={!enabled}
      title={tooltip}
      style={{
        ...styles.button,
        opacity: enabled ? 1 : 0.4,
        cursor: enabled ? 'pointer' : 'not-allowed',
      }}
    >
      {label}
    </button>
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
    gap: 8,
  },
  button: {
    flex: 1,
    padding: '8px 12px',
    background: colors.bgElevated,
    border: `1px solid ${colors.border}`,
    borderRadius: 6,
    color: colors.textPrimary,
    fontSize: 13,
    fontWeight: 500,
    fontFamily: 'inherit',
  },
}
