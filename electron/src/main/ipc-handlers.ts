import { ipcMain } from 'electron'
import { SidecarManager } from './sidecar'
import type { SidecarRequest } from '../../../shared/messages'

export function setupIpcHandlers(sidecar: SidecarManager): void {
  ipcMain.handle('sidecar:send', async (_event, request: SidecarRequest) => {
    return sidecar.send(request)
  })

  ipcMain.handle('sidecar:ping', async () => {
    return { status: 'ok' }
  })
}
