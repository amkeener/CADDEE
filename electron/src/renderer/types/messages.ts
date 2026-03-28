import type { CaddeeAPI } from '../../preload/index'

/** Local UI chat message (not the IPC type). */
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'error'
  content: string
  timestamp: number
  /** Data-URL-encoded images attached to this message (user messages only). */
  images?: string[]
}

export type ChatStatus = 'idle' | 'thinking' | 'compiling' | 'retrying' | 'error'

declare global {
  interface Window {
    caddee: CaddeeAPI
  }
}
