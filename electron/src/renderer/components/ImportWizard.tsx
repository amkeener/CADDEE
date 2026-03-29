import { useState } from 'react'
import { colors } from '../theme/colors'

interface ImportWizardProps {
  onImport: (result: ImportedFile) => void
  onClose: () => void
}

export interface ImportedFile {
  fileType: string
  scadCode?: string
  stlBase64?: string
  metadata: Record<string, unknown>
}

export function ImportWizard({ onImport, onClose }: ImportWizardProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSelectFile = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await window.caddee.importFile()
      if (!result.success || !result.filePath) {
        setLoading(false)
        return // User cancelled
      }

      const response = await window.caddee.sendToSidecar({
        id: crypto.randomUUID(),
        type: 'import_file',
        filePath: result.filePath,
      })

      if (response.type === 'import_result' && response.success) {
        onImport({
          fileType: response.fileType,
          scadCode: response.scadCode,
          stlBase64: response.stlBase64,
          metadata: response.metadata,
        })
        onClose()
      } else if (response.type === 'import_result' && response.error) {
        setError(response.error)
      } else if (response.type === 'error') {
        setError(response.error)
      }
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={styles.overlay} onClick={onClose}>
      <div style={styles.dialog} onClick={e => e.stopPropagation()}>
        <div style={styles.header}>
          <span style={styles.title}>Import CAD File</span>
          <button onClick={onClose} style={styles.closeButton}>&times;</button>
        </div>

        <div style={styles.body}>
          <p style={styles.description}>
            Import an existing file as a starting point for your design.
          </p>

          <div style={styles.formats}>
            <FormatRow ext=".scad" desc="OpenSCAD source — loads directly as editable code" />
            <FormatRow ext=".stl" desc="Mesh file — loads into viewport for reference" />
            <FormatRow ext=".step / .stp" desc="CAD solid — requires FreeCAD installed" />
            <FormatRow ext=".FCStd" desc="FreeCAD document — requires FreeCAD installed" />
          </div>

          {error && <div style={styles.error}>{error}</div>}

          <button
            onClick={handleSelectFile}
            disabled={loading}
            style={{
              ...styles.importButton,
              opacity: loading ? 0.6 : 1,
            }}
          >
            {loading ? 'Importing...' : 'Choose File...'}
          </button>
        </div>
      </div>
    </div>
  )
}

function FormatRow({ ext, desc }: { ext: string; desc: string }) {
  return (
    <div style={styles.formatRow}>
      <code style={styles.formatExt}>{ext}</code>
      <span style={styles.formatDesc}>{desc}</span>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  overlay: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(0,0,0,0.6)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  },
  dialog: {
    background: colors.bgElevated,
    border: `1px solid ${colors.border}`,
    borderRadius: 12,
    width: 480,
    maxWidth: '90vw',
    overflow: 'hidden',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '16px 20px',
    borderBottom: `1px solid ${colors.border}`,
  },
  title: {
    fontSize: 16,
    fontWeight: 600,
    color: colors.textPrimary,
  },
  closeButton: {
    background: 'none',
    border: 'none',
    color: colors.textSecondary,
    fontSize: 22,
    cursor: 'pointer',
    padding: '0 4px',
    fontFamily: 'inherit',
  },
  body: {
    padding: '20px',
  },
  description: {
    color: colors.textSecondary,
    fontSize: 13,
    marginTop: 0,
    marginBottom: 16,
    lineHeight: 1.5,
  },
  formats: {
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
    marginBottom: 16,
  },
  formatRow: {
    display: 'flex',
    gap: 12,
    alignItems: 'baseline',
    padding: '6px 10px',
    background: colors.bgPanel,
    borderRadius: 4,
  },
  formatExt: {
    fontSize: 12,
    color: colors.gold,
    fontWeight: 600,
    minWidth: 80,
    flexShrink: 0,
  },
  formatDesc: {
    fontSize: 12,
    color: colors.textSecondary,
  },
  error: {
    color: colors.error,
    fontSize: 12,
    marginBottom: 12,
    padding: '8px 10px',
    background: 'rgba(229,115,115,0.1)',
    borderRadius: 4,
  },
  importButton: {
    width: '100%',
    padding: '10px',
    background: colors.primary,
    border: `1px solid ${colors.borderStrong}`,
    borderRadius: 8,
    color: '#fff',
    fontSize: 14,
    fontWeight: 500,
    cursor: 'pointer',
    fontFamily: 'inherit',
  },
}
