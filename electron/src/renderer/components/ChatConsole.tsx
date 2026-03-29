import { useRef, useEffect, useState, useCallback, type KeyboardEvent, type DragEvent, type ClipboardEvent, type MutableRefObject } from 'react'
import { useChat } from '../hooks/useChat'
import type { ChatMessage, ChatStatus } from '../types/messages'

const ACCEPTED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
const MAX_IMAGES = 5

interface ChatConsoleProps {
  onStlUpdate: (data: ArrayBuffer | null, scadCode?: string, stlBase64?: string) => void
  onCompileStateChange: (compiling: boolean) => void
  onIteration?: (prompt: string, scadCode: string, stlBase64: string) => void
  iterationCount?: number
  messagesRef?: MutableRefObject<ChatMessage[]>
  setMessagesRef?: MutableRefObject<((msgs: ChatMessage[]) => void) | null>
}

const STATUS_LABELS: Record<ChatStatus, string | null> = {
  idle: null,
  thinking: 'Thinking...',
  compiling: 'Compiling...',
  retrying: 'Compile error (retrying...)',
  error: null,
}

export function ChatConsole({ onStlUpdate, onCompileStateChange, onIteration, iterationCount = 0, messagesRef, setMessagesRef }: ChatConsoleProps) {
  const { messages, status, sendMessage, setMessages } = useChat(onStlUpdate, onCompileStateChange, onIteration)
  const [input, setInput] = useState('')
  const [pendingImages, setPendingImages] = useState<string[]>([])
  const [isDragOver, setIsDragOver] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Sync refs for session restore
  useEffect(() => {
    if (messagesRef) messagesRef.current = messages
  }, [messages, messagesRef])
  useEffect(() => {
    if (setMessagesRef) setMessagesRef.current = setMessages
  }, [setMessages, setMessagesRef])

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

  // --- Image helpers ---

  const addImages = useCallback((files: File[]) => {
    const validFiles = files.filter(f => ACCEPTED_IMAGE_TYPES.includes(f.type))
    if (validFiles.length === 0) return

    for (const file of validFiles) {
      if (pendingImages.length >= MAX_IMAGES) break
      const reader = new FileReader()
      reader.onload = () => {
        const dataUrl = reader.result as string
        setPendingImages(prev => {
          if (prev.length >= MAX_IMAGES) return prev
          return [...prev, dataUrl]
        })
      }
      reader.readAsDataURL(file)
    }
  }, [pendingImages.length])

  const removeImage = useCallback((index: number) => {
    setPendingImages(prev => prev.filter((_, i) => i !== index))
  }, [])

  // --- Event handlers ---

  const handleSend = async () => {
    const trimmed = input.trim()
    if ((!trimmed && pendingImages.length === 0) || isBusy) return
    const images = pendingImages.length > 0 ? [...pendingImages] : undefined
    setInput('')
    setPendingImages([])
    await sendMessage(trimmed || 'What do you see in this image? Generate an OpenSCAD model based on it.', images)
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handlePaste = useCallback((e: ClipboardEvent<HTMLTextAreaElement>) => {
    const items = e.clipboardData?.items
    if (!items) return
    const imageFiles: File[] = []
    for (let i = 0; i < items.length; i++) {
      const item = items[i]
      if (item.kind === 'file' && ACCEPTED_IMAGE_TYPES.includes(item.type)) {
        const file = item.getAsFile()
        if (file) imageFiles.push(file)
      }
    }
    if (imageFiles.length > 0) {
      e.preventDefault()
      addImages(imageFiles)
    }
  }, [addImages])

  const handleDragOver = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragOver(false)
    const files: File[] = []
    if (e.dataTransfer.files) {
      for (let i = 0; i < e.dataTransfer.files.length; i++) {
        files.push(e.dataTransfer.files[i])
      }
    }
    addImages(files)
  }, [addImages])

  const handleFileSelect = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files: File[] = []
    if (e.target.files) {
      for (let i = 0; i < e.target.files.length; i++) {
        files.push(e.target.files[i])
      }
    }
    addImages(files)
    // Reset so the same file can be selected again
    e.target.value = ''
  }, [addImages])

  const statusLabel = STATUS_LABELS[status]

  const canSend = !isBusy && (input.trim().length > 0 || pendingImages.length > 0)

  return (
    <div
      style={{
        ...styles.container,
        ...(isDragOver ? styles.containerDragOver : {}),
      }}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* Header */}
      <div style={styles.header}>
        <span style={styles.headerTitle}>CADDEE Chat</span>
      </div>

      {/* Drag overlay */}
      {isDragOver && (
        <div style={styles.dragOverlay}>
          <span style={styles.dragOverlayText}>Drop images here</span>
        </div>
      )}

      {/* Message history */}
      <div style={styles.messageArea}>
        {messages.length === 0 && (
          <div style={styles.emptyState}>
            Describe what you want to build and CADDEE will generate a 3D model.
            {'\n\n'}You can also attach images — sketches, photos, or technical drawings.
          </div>
        )}
        {messages.map((msg, idx) => {
          // Show iteration divider before each user message (except the first)
          const showDivider = msg.role === 'user' && idx > 0
          const iterNum = messages.slice(0, idx + 1).filter(m => m.role === 'user').length
          return (
            <div key={msg.id}>
              {showDivider && (
                <div style={styles.iterationDivider}>
                  <span style={styles.iterationBadge}>Iteration {iterNum}</span>
                </div>
              )}
              <MessageBubble message={msg} />
            </div>
          )
        })}
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

      {/* Pending image previews */}
      {pendingImages.length > 0 && (
        <div style={styles.imagePreviewStrip}>
          {pendingImages.map((dataUrl, i) => (
            <div key={i} style={styles.imagePreviewItem}>
              <img src={dataUrl} alt={`Attached ${i + 1}`} style={styles.imagePreviewImg} />
              <button
                onClick={() => removeImage(i)}
                style={styles.imageRemoveBtn}
                title="Remove image"
              >
                &times;
              </button>
            </div>
          ))}
          {pendingImages.length < MAX_IMAGES && (
            <div style={styles.imageCount}>
              {pendingImages.length}/{MAX_IMAGES}
            </div>
          )}
        </div>
      )}

      {/* Input area */}
      <div style={styles.inputArea}>
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPTED_IMAGE_TYPES.join(',')}
          multiple
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />
        <button
          onClick={handleFileSelect}
          disabled={isBusy || pendingImages.length >= MAX_IMAGES}
          style={{
            ...styles.attachButton,
            opacity: isBusy || pendingImages.length >= MAX_IMAGES ? 0.3 : 0.7,
            cursor: isBusy || pendingImages.length >= MAX_IMAGES ? 'not-allowed' : 'pointer',
          }}
          title="Attach image (or paste/drag-drop)"
        >
          <PaperclipIcon />
        </button>
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          onPaste={handlePaste}
          placeholder={pendingImages.length > 0 ? 'Add a description (optional)...' : 'Describe what you want to build...'}
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
          disabled={!canSend}
          style={{
            ...styles.sendButton,
            opacity: canSend ? 1 : 0.4,
            cursor: canSend ? 'pointer' : 'not-allowed',
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
        {message.images && message.images.length > 0 && (
          <div style={styles.bubbleImages}>
            {message.images.map((dataUrl, i) => (
              <img key={i} src={dataUrl} alt={`Attached ${i + 1}`} style={styles.bubbleImage} />
            ))}
          </div>
        )}
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

function PaperclipIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48" />
    </svg>
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

  // Iteration grouping
  iterationDivider: {
    display: 'flex',
    alignItems: 'center',
    margin: '16px 0 10px',
    gap: 10,
  },
  iterationBadge: {
    fontSize: 10,
    fontWeight: 600,
    color: '#5588ff',
    textTransform: 'uppercase' as const,
    letterSpacing: 1,
    whiteSpace: 'nowrap' as const,
    padding: '2px 8px',
    background: '#1a2a4a',
    borderRadius: 10,
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
  attachButton: {
    width: 38,
    height: 38,
    borderRadius: 8,
    background: 'transparent',
    border: '1px solid #333',
    color: '#888',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },

  // Drag-and-drop
  containerDragOver: {
    outline: '2px dashed #7c8aff',
    outlineOffset: -2,
  },
  dragOverlay: {
    position: 'absolute' as const,
    inset: 0,
    background: 'rgba(124, 138, 255, 0.08)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 10,
    pointerEvents: 'none' as const,
  },
  dragOverlayText: {
    color: '#7c8aff',
    fontSize: 16,
    fontWeight: 600,
    padding: '12px 24px',
    background: '#1a1a2e',
    borderRadius: 12,
    border: '1px solid #7c8aff',
  },

  // Image preview strip (above input)
  imagePreviewStrip: {
    display: 'flex',
    gap: 8,
    padding: '8px 14px 0',
    alignItems: 'center',
    flexWrap: 'wrap' as const,
    flexShrink: 0,
  },
  imagePreviewItem: {
    position: 'relative' as const,
    width: 56,
    height: 56,
    borderRadius: 8,
    overflow: 'hidden',
    border: '1px solid #333',
    flexShrink: 0,
  },
  imagePreviewImg: {
    width: '100%',
    height: '100%',
    objectFit: 'cover' as const,
    display: 'block',
  },
  imageRemoveBtn: {
    position: 'absolute' as const,
    top: 2,
    right: 2,
    width: 18,
    height: 18,
    borderRadius: '50%',
    background: 'rgba(0,0,0,0.7)',
    border: 'none',
    color: '#fff',
    fontSize: 12,
    lineHeight: '18px',
    textAlign: 'center' as const,
    cursor: 'pointer',
    padding: 0,
  },
  imageCount: {
    fontSize: 11,
    color: '#555',
  },

  // Images in message bubbles
  bubbleImages: {
    display: 'flex',
    gap: 6,
    marginBottom: 8,
    flexWrap: 'wrap' as const,
  },
  bubbleImage: {
    width: 80,
    height: 80,
    objectFit: 'cover' as const,
    borderRadius: 6,
    border: '1px solid #333',
  },
}
