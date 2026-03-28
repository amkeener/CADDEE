import type { ReactNode } from 'react'

interface ToolsPanelProps {
  iterationHistory?: ReactNode
  parameterSliders?: ReactNode
  exportButtons?: ReactNode
}

export function ToolsPanel({ iterationHistory, parameterSliders, exportButtons }: ToolsPanelProps) {
  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <span style={styles.headerTitle}>Tools</span>
      </div>
      <div style={styles.content}>
        {iterationHistory && (
          <Section title="History">
            {iterationHistory}
          </Section>
        )}
        {parameterSliders && (
          <Section title="Parameters">
            {parameterSliders}
          </Section>
        )}
        {exportButtons && (
          <Section title="Export">
            {exportButtons}
          </Section>
        )}
        {!iterationHistory && !parameterSliders && !exportButtons && (
          <div style={styles.empty}>
            Design something to see tools here.
          </div>
        )}
      </div>
    </div>
  )
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div style={styles.section}>
      <div style={styles.sectionTitle}>{title}</div>
      {children}
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    background: '#0f0f23',
    color: '#ccc',
  },
  header: {
    padding: '14px 16px',
    borderBottom: '1px solid #2a2a3e',
    flexShrink: 0,
  },
  headerTitle: {
    fontSize: 15,
    fontWeight: 600,
    color: '#fff',
    letterSpacing: 0.5,
  },
  content: {
    flex: 1,
    overflowY: 'auto',
    padding: '8px 0',
  },
  section: {
    padding: '8px 16px 16px',
  },
  sectionTitle: {
    fontSize: 11,
    fontWeight: 600,
    color: '#888',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 10,
  },
  empty: {
    color: '#555',
    fontSize: 13,
    textAlign: 'center',
    marginTop: 40,
    padding: '0 20px',
    lineHeight: 1.5,
  },
}
