import type { CaddeeAPI } from '../../preload/index'

/** Local UI chat message (not the IPC type). */
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'error'
  content: string
  timestamp: number
}

export type ChatStatus = 'idle' | 'thinking' | 'compiling' | 'retrying' | 'error'

declare global {
  interface Window {
    caddee: CaddeeAPI
  }
}
