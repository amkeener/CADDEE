import type { Iteration } from '../App'

interface IterationHistoryProps {
  iterations: Iteration[]
  onRestore: (iteration: Iteration) => void
}

export function IterationHistory({ iterations, onRestore }: IterationHistoryProps) {
  if (iterations.length === 0) {
    return <div style={styles.empty}>No iterations yet.</div>
  }

  return (
    <div style={styles.list}>
      {iterations.map((iter, index) => (
        <button
          key={iter.id}
          onClick={() => onRestore(iter)}
          style={styles.item}
          title={iter.prompt}
        >
          <div style={styles.thumbWrapper}>
            {iter.thumbnail ? (
              <img src={iter.thumbnail} alt="" style={styles.thumb} />
            ) : (
              <div style={styles.thumbPlaceholder}>
                {index + 1}
              </div>
            )}
          </div>
          <div style={styles.info}>
            <div style={styles.prompt}>
              {iter.prompt.length > 50 ? iter.prompt.slice(0, 50) + '...' : iter.prompt}
            </div>
            <div style={styles.time}>
              {new Date(iter.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
          </div>
        </button>
      ))}
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  list: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
  },
  item: {
    display: 'flex',
    gap: 10,
    alignItems: 'center',
    padding: '6px 8px',
    background: '#1a1a2e',
    border: '1px solid #2a2a3e',
    borderRadius: 6,
    cursor: 'pointer',
    textAlign: 'left',
    color: 'inherit',
    fontFamily: 'inherit',
    width: '100%',
  },
  thumbWrapper: {
    flexShrink: 0,
    width: 48,
    height: 48,
    borderRadius: 4,
    overflow: 'hidden',
    background: '#13132a',
  },
  thumb: {
    width: '100%',
    height: '100%',
    objectFit: 'cover',
  },
  thumbPlaceholder: {
    width: '100%',
    height: '100%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#555',
    fontSize: 16,
    fontWeight: 600,
  },
  info: {
    flex: 1,
    minWidth: 0,
    overflow: 'hidden',
  },
  prompt: {
    fontSize: 12,
    color: '#ccc',
    lineHeight: 1.3,
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  time: {
    fontSize: 10,
    color: '#555',
    marginTop: 3,
  },
  empty: {
    color: '#555',
    fontSize: 12,
  },
}
