import { contextBridge, ipcRenderer } from 'electron'
import type { SidecarRequest, SidecarResponse } from '../../../shared/messages'

const api = {
  sendToSidecar: (request: SidecarRequest): Promise<SidecarResponse> => {
    return ipcRenderer.invoke('sidecar:send', request)
  },
  ping: (): Promise<{ status: string }> => {
    return ipcRenderer.invoke('sidecar:ping')
  },

  // Export
  exportSTL: (stlBase64: string): Promise<{ success: boolean; path?: string }> => {
    return ipcRenderer.invoke('export:stl', stlBase64)
  },
  exportScad: (scadCode: string): Promise<{ success: boolean; path?: string }> => {
    return ipcRenderer.invoke('export:scad', scadCode)
  },

  // Session
  saveSession: (sessionJson: string): Promise<{ success: boolean; path?: string }> => {
    return ipcRenderer.invoke('session:save', sessionJson)
  },
  openSession: (): Promise<{ success: boolean; data?: string }> => {
    return ipcRenderer.invoke('session:open')
  },

  // Menu events
  onMenuSaveSession: (callback: () => void): (() => void) => {
    const handler = () => callback()
    ipcRenderer.on('menu:save-session', handler)
    return () => ipcRenderer.removeListener('menu:save-session', handler)
  },
  onMenuOpenSession: (callback: () => void): (() => void) => {
    const handler = () => callback()
    ipcRenderer.on('menu:open-session', handler)
    return () => ipcRenderer.removeListener('menu:open-session', handler)
  },
}

contextBridge.exposeInMainWorld('caddee', api)

export type CaddeeAPI = typeof api
