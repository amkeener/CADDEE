import { useState, useCallback } from 'react'
import type { ChatMessage, ChatStatus } from '../types/messages'

export interface UseChatReturn {
  messages: ChatMessage[]
  status: ChatStatus
  sendMessage: (text: string) => Promise<void>
  setMessages: (messages: ChatMessage[]) => void
}

export function useChat(
  onStlUpdate: (data: ArrayBuffer | null, scadCode?: string, stlBase64?: string) => void,
  onCompileStateChange: (compiling: boolean) => void,
  onIteration?: (prompt: string, scadCode: string, stlBase64: string) => void,
): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [status, setStatus] = useState<ChatStatus>('idle')

  const sendMessage = useCallback(async (text: string) => {
    const trimmed = text.trim()
    if (!trimmed) return

    // Add user message to history
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: trimmed,
      timestamp: Date.now(),
    }
    setMessages(prev => [...prev, userMsg])

    // Build the IPC request
    const requestId = crypto.randomUUID()
    setStatus('thinking')
    onCompileStateChange(true)

    try {
      const response = await window.caddee.sendToSidecar({
        id: requestId,
        type: 'chat',
        message: trimmed,
      })

      if (response.type === 'chat_response') {
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
  }, [onStlUpdate, onCompileStateChange, onIteration])

  return { messages, status, sendMessage, setMessages }
}
