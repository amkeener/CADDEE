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

  // Phase 3 exports
  exportStep: (stlBase64: string): Promise<{ success: boolean; path?: string; error?: string }> => {
    return ipcRenderer.invoke('export:step', stlBase64)
  },
  exportFcstd: (stlBase64: string): Promise<{ success: boolean; path?: string; error?: string }> => {
    return ipcRenderer.invoke('export:fcstd', stlBase64)
  },

  // Import
  importFile: (): Promise<{ success: boolean; filePath?: string }> => {
    return ipcRenderer.invoke('import:file')
  },

  // Menu events
  onMenuImportFile: (callback: () => void): (() => void) => {
    const handler = () => callback()
    ipcRenderer.on('menu:import-file', handler)
    return () => ipcRenderer.removeListener('menu:import-file', handler)
  },
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

  // External links — opens in user's default browser (e.g. logged-in Chrome)
  openExternal: (url: string): void => {
    ipcRenderer.send('shell:open-external', url)
  },

  // API Key management
  getApiKeyStatus: (): Promise<{ configured: boolean; source: 'env' | 'stored' | 'none' }> => {
    return ipcRenderer.invoke('api-key:status')
  },
  saveApiKey: (key: string): Promise<{ success: boolean; error?: string }> => {
    return ipcRenderer.invoke('api-key:save', key)
  },
  clearApiKey: (): Promise<{ success: boolean }> => {
    return ipcRenderer.invoke('api-key:clear')
  },
  onApiKeyMissing: (callback: () => void): (() => void) => {
    const handler = () => callback()
    ipcRenderer.on('api-key:missing', handler)
    return () => ipcRenderer.removeListener('api-key:missing', handler)
  },
}

contextBridge.exposeInMainWorld('caddee', api)

export type CaddeeAPI = typeof api
