import { contextBridge, ipcRenderer } from 'electron'
import type { SidecarRequest, SidecarResponse } from '../../../shared/messages'

const api = {
  sendToSidecar: (request: SidecarRequest): Promise<SidecarResponse> => {
    return ipcRenderer.invoke('sidecar:send', request)
  },
  ping: (): Promise<{ status: string }> => {
    return ipcRenderer.invoke('sidecar:ping')
  }
}

contextBridge.exposeInMainWorld('caddee', api)

export type CaddeeAPI = typeof api
