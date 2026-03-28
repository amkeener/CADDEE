import { useRef, useEffect, useState, type KeyboardEvent } from 'react'
import { useChat } from '../hooks/useChat'
import type { ChatMessage, ChatStatus } from '../types/messages'

interface ChatConsoleProps {
  onStlUpdate: (data: ArrayBuffer | null) => void
  onCompileStateChange: (compiling: boolean) => void
}

const STATUS_LABELS: Record<ChatStatus, string | null> = {
  idle: null,
  thinking: 'Thinking...',
  compiling: 'Compiling...',
  retrying: 'Compile error (retrying...)',
  error: null,
}

export function ChatConsole({ onStlUpdate, onCompileStateChange }: ChatConsoleProps) {
  const { messages, status, sendMessage } = useChat(onStlUpdate, onCompileStateChange)
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const isBusy = status === 'thinking' || status === 'compiling' || status === 'retrying'

  // Auto-scroll to bottom when messages change or status changes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, status])

  // Auto-resize textarea to fit content
  useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`
    }
  }, [input])

  const handleSend = async () => {
    const trimmed = input.trim()
    if (!trimmed || isBusy) return
    setInput('')
    await sendMessage(trimmed)
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const statusLabel = STATUS_LABELS[status]

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <span style={styles.headerTitle}>CADDEE Chat</span>
      </div>

      {/* Message history */}
      <div style={styles.messageArea}>
        {messages.length === 0 && (
          <div style={styles.emptyState}>
            Describe what you want to build and CADDEE will generate a 3D model.
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {isBusy && (
          <div style={styles.thinkingBubble}>
            <ThinkingDots />
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Status bar */}
      {statusLabel && (
        <div style={styles.statusBar}>
          <span style={styles.statusDot} />
          {statusLabel}
        </div>
      )}

      {/* Input area */}
      <div style={styles.inputArea}>
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe what you want to build..."
          disabled={isBusy}
          rows={1}
          style={{
            ...styles.textarea,
            opacity: isBusy ? 0.5 : 1,
            cursor: isBusy ? 'not-allowed' : 'text',
          }}
        />
        <button
          onClick={handleSend}
          disabled={isBusy || !input.trim()}
          style={{
            ...styles.sendButton,
            opacity: isBusy || !input.trim() ? 0.4 : 1,
            cursor: isBusy || !input.trim() ? 'not-allowed' : 'pointer',
          }}
          title="Send message"
        >
          <SendIcon />
        </button>
      </div>
    </div>
  )
}

/* ---------- Sub-components ---------- */

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user'
  const isError = message.role === 'error'

  const bubbleStyle: React.CSSProperties = isUser
    ? styles.userBubble
    : isError
      ? styles.errorBubble
      : styles.assistantBubble

  const alignStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: isUser ? 'flex-end' : 'flex-start',
    marginBottom: 10,
  }

  return (
    <div style={alignStyle}>
      <div style={bubbleStyle}>
        <div style={styles.bubbleText}>{message.content}</div>
        <div style={styles.timestamp}>
          {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  )
}

function ThinkingDots() {
  return (
    <span style={{ letterSpacing: 2, color: '#888' }}>
      {'...'}
    </span>
  )
}

function SendIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  )
}

/* ---------- Styles ---------- */

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
  messageArea: {
    flex: 1,
    overflowY: 'auto',
    padding: '16px 14px',
    display: 'flex',
    flexDirection: 'column',
  },
  emptyState: {
    color: '#555',
    fontSize: 14,
    textAlign: 'center',
    marginTop: 40,
    lineHeight: 1.5,
    padding: '0 20px',
  },

  // Bubbles
  userBubble: {
    background: '#1e3a5f',
    borderRadius: '14px 14px 4px 14px',
    padding: '10px 14px',
    maxWidth: '85%',
    wordBreak: 'break-word' as const,
  },
  assistantBubble: {
    background: '#1a1a2e',
    borderRadius: '14px 14px 14px 4px',
    padding: '10px 14px',
    maxWidth: '85%',
    wordBreak: 'break-word' as const,
    border: '1px solid #2a2a3e',
  },
  errorBubble: {
    background: '#2e1a1a',
    borderRadius: '14px 14px 14px 4px',
    padding: '10px 14px',
    maxWidth: '85%',
    wordBreak: 'break-word' as const,
    border: '1px solid #5f1e1e',
    color: '#e88',
  },
  bubbleText: {
    fontSize: 14,
    lineHeight: 1.5,
    whiteSpace: 'pre-wrap',
  },
  timestamp: {
    fontSize: 11,
    color: '#555',
    marginTop: 4,
    textAlign: 'right' as const,
  },

  thinkingBubble: {
    display: 'flex',
    justifyContent: 'flex-start',
    marginBottom: 10,
  },

  // Status bar
  statusBar: {
    padding: '6px 16px',
    fontSize: 12,
    color: '#8888aa',
    background: '#13132a',
    borderTop: '1px solid #2a2a3e',
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    flexShrink: 0,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: '50%',
    background: '#5588ff',
    display: 'inline-block',
    animation: 'none', // CSS animations need keyframes; keep it simple
  },

  // Input
  inputArea: {
    padding: '12px 14px',
    borderTop: '1px solid #2a2a3e',
    display: 'flex',
    gap: 8,
    alignItems: 'flex-end',
    flexShrink: 0,
  },
  textarea: {
    flex: 1,
    padding: '10px 14px',
    background: '#1a1a2e',
    border: '1px solid #333',
    borderRadius: 8,
    color: '#ccc',
    fontSize: 14,
    lineHeight: '1.4',
    resize: 'none' as const,
    outline: 'none',
    fontFamily: 'inherit',
    maxHeight: 120,
    overflow: 'auto',
  },
  sendButton: {
    width: 38,
    height: 38,
    borderRadius: 8,
    background: '#2a4a7f',
    border: 'none',
    color: '#fff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
}
