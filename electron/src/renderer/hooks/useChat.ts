import { useState, useCallback } from 'react'
import type { ChatMessage, ChatStatus } from '../types/messages'
import { createLogger } from '../utils/logger'

const log = createLogger('chat')

export interface UseChatReturn {
  messages: ChatMessage[]
  status: ChatStatus
  sendMessage: (text: string, images?: string[]) => Promise<void>
  setMessages: (messages: ChatMessage[]) => void
}

export function useChat(
  onStlUpdate: (data: ArrayBuffer | null, scadCode?: string, stlBase64?: string) => void,
  onCompileStateChange: (compiling: boolean) => void,
  onIteration?: (prompt: string, scadCode: string, stlBase64: string) => void,
  currentStlBase64?: string,
): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [status, setStatus] = useState<ChatStatus>('idle')

  const sendMessage = useCallback(async (text: string, images?: string[]) => {
    const trimmed = text.trim()
    if (!trimmed) return

    // Add user message to history (with image references for display)
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: trimmed,
      timestamp: Date.now(),
      images: images && images.length > 0 ? images : undefined,
    }
    setMessages(prev => [...prev, userMsg])

    // Build the IPC request
    const requestId = crypto.randomUUID()
    log.info('Sending chat: %d chars, %d images', trimmed.length, images?.length ?? 0)
    setStatus('thinking')
    onCompileStateChange(true)

    try {
      const t0 = performance.now()
      const response = await window.caddee.sendToSidecar({
        id: requestId,
        type: 'chat',
        message: trimmed,
        images: images && images.length > 0 ? images : undefined,
        stlBase64: currentStlBase64 || undefined,
      })

      const elapsed = ((performance.now() - t0) / 1000).toFixed(1)

      if (response.type === 'chat_response') {
        log.info('Chat response received in %ss (stl=%s)', elapsed, response.stlBase64 ? 'yes' : 'no')
        // Successful generation
        const assistantMsg: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: response.message,
          timestamp: Date.now(),
        }
        setMessages(prev => [...prev, assistantMsg])

        // Decode base64 STL to ArrayBuffer
        if (response.stlBase64) {
          const binary = atob(response.stlBase64)
          const bytes = new Uint8Array(binary.length)
          for (let i = 0; i < binary.length; i++) {
            bytes[i] = binary.charCodeAt(i)
          }
          onStlUpdate(bytes.buffer, response.scadCode, response.stlBase64)
          // Notify parent of new iteration (short delay so viewport renders for thumbnail)
          if (onIteration && response.scadCode) {
            setTimeout(() => onIteration(trimmed, response.scadCode, response.stlBase64), 100)
          }
        }

        setStatus('idle')
      } else if (response.type === 'chat_error') {
        log.error('Chat error in %ss: %s', elapsed, response.error)
        const errorContent = response.compileError
          ? `${response.error}\n\nCompile error:\n${response.compileError}`
          : response.error

        const errorMsg: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'error',
          content: errorContent,
          timestamp: Date.now(),
        }
        setMessages(prev => [...prev, errorMsg])
        setStatus('error')
      } else if (response.type === 'error') {
        const errorMsg: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'error',
          content: response.error,
          timestamp: Date.now(),
        }
        setMessages(prev => [...prev, errorMsg])
        setStatus('error')
      }
    } catch (err) {
      log.error('Chat exception: %s', err instanceof Error ? err.message : String(err))
      const errorMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'error',
        content: err instanceof Error ? err.message : 'An unexpected error occurred',
        timestamp: Date.now(),
      }
      setMessages(prev => [...prev, errorMsg])
      setStatus('error')
    } finally {
      onCompileStateChange(false)
    }
  }, [onStlUpdate, onCompileStateChange, onIteration, currentStlBase64])

  return { messages, status, sendMessage, setMessages }
}
