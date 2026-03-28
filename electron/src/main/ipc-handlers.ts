import { ipcMain, dialog, BrowserWindow } from 'electron'
import { writeFile, readFile } from 'fs/promises'
import { SidecarManager } from './sidecar'
import { saveApiKey, clearApiKey, hasApiKey } from './credentials'
import type { SidecarRequest } from '../../../shared/messages'

export function setupIpcHandlers(sidecar: SidecarManager): void {
  ipcMain.handle('sidecar:send', async (_event, request: SidecarRequest) => {
    return sidecar.send(request)
  })

  ipcMain.handle('sidecar:ping', async () => {
    return { status: 'ok' }
  })

  // --- Export Handlers ---

  ipcMain.handle('export:stl', async (_event, stlBase64: string) => {
    const win = BrowserWindow.getFocusedWindow()
    if (!win) return { success: false }

    const result = await dialog.showSaveDialog(win, {
      title: 'Export STL',
      defaultPath: 'model.stl',
      filters: [{ name: 'STL Files', extensions: ['stl'] }],
    })

    if (result.canceled || !result.filePath) return { success: false }

    const buffer = Buffer.from(stlBase64, 'base64')
    await writeFile(result.filePath, buffer)
    return { success: true, path: result.filePath }
  })

  ipcMain.handle('export:scad', async (_event, scadCode: string) => {
    const win = BrowserWindow.getFocusedWindow()
    if (!win) return { success: false }

    const result = await dialog.showSaveDialog(win, {
      title: 'Export OpenSCAD',
      defaultPath: 'model.scad',
      filters: [{ name: 'OpenSCAD Files', extensions: ['scad'] }],
    })

    if (result.canceled || !result.filePath) return { success: false }

    await writeFile(result.filePath, scadCode, 'utf-8')
    return { success: true, path: result.filePath }
  })

  // --- Session Handlers ---

  ipcMain.handle('session:save', async (_event, sessionJson: string) => {
    const win = BrowserWindow.getFocusedWindow()
    if (!win) return { success: false }

    const result = await dialog.showSaveDialog(win, {
      title: 'Save Session',
      defaultPath: 'design.cad-session',
      filters: [{ name: 'CADDEE Session', extensions: ['cad-session'] }],
    })

    if (result.canceled || !result.filePath) return { success: false }

    await writeFile(result.filePath, sessionJson, 'utf-8')
    return { success: true, path: result.filePath }
  })

  ipcMain.handle('session:open', async () => {
    const win = BrowserWindow.getFocusedWindow()
    if (!win) return { success: false }

    const result = await dialog.showOpenDialog(win, {
      title: 'Open Session',
      filters: [{ name: 'CADDEE Session', extensions: ['cad-session'] }],
      properties: ['openFile'],
    })

    if (result.canceled || result.filePaths.length === 0) return { success: false }

    const data = await readFile(result.filePaths[0], 'utf-8')
    return { success: true, data }
  })

  // --- STEP / FCStd Export Handlers (Phase 3) ---

  ipcMain.handle('export:step', async (_event, stlBase64: string) => {
    const win = BrowserWindow.getFocusedWindow()
    if (!win) return { success: false }

    const result = await dialog.showSaveDialog(win, {
      title: 'Export STEP',
      defaultPath: 'model.step',
      filters: [{ name: 'STEP Files', extensions: ['step', 'stp'] }],
    })

    if (result.canceled || !result.filePath) return { success: false }

    const response = await sidecar.send({
      id: crypto.randomUUID(),
      type: 'export_step',
      stlBase64,
      outputPath: result.filePath,
    })

    if (response.type === 'export_result') {
      return { success: response.success, path: result.filePath, error: response.error }
    }
    return { success: false, error: 'Unexpected response' }
  })

  ipcMain.handle('export:fcstd', async (_event, stlBase64: string) => {
    const win = BrowserWindow.getFocusedWindow()
    if (!win) return { success: false }

    const result = await dialog.showSaveDialog(win, {
      title: 'Export FreeCAD Document',
      defaultPath: 'model.FCStd',
      filters: [{ name: 'FreeCAD Documents', extensions: ['FCStd'] }],
    })

    if (result.canceled || !result.filePath) return { success: false }

    const response = await sidecar.send({
      id: crypto.randomUUID(),
      type: 'export_fcstd',
      stlBase64,
      outputPath: result.filePath,
    })

    if (response.type === 'export_result') {
      return { success: response.success, path: result.filePath, error: response.error }
    }
    return { success: false, error: 'Unexpected response' }
  })

  // --- Import Handler (Phase 3) ---

  ipcMain.handle('import:file', async () => {
    const win = BrowserWindow.getFocusedWindow()
    if (!win) return { success: false }

    const result = await dialog.showOpenDialog(win, {
      title: 'Import CAD File',
      filters: [
        { name: 'CAD Files', extensions: ['stl', 'scad', 'step', 'stp', 'FCStd'] },
        { name: 'All Files', extensions: ['*'] },
      ],
      properties: ['openFile'],
    })

    if (result.canceled || result.filePaths.length === 0) return { success: false }

    return { success: true, filePath: result.filePaths[0] }
  })

  // --- API Key Handlers ---

  ipcMain.handle('api-key:status', async () => {
    if (process.env.ANTHROPIC_API_KEY) {
      return { configured: true, source: 'env' as const }
    }
    if (hasApiKey()) {
      return { configured: true, source: 'stored' as const }
    }
    return { configured: false, source: 'none' as const }
  })

  ipcMain.handle('api-key:save', async (_event, key: string) => {
    const response = await sidecar.send({
      id: crypto.randomUUID(),
      type: 'set_api_key',
      apiKey: key,
    })

    if (response.type === 'api_key_set' && response.success) {
      saveApiKey(key)
      return { success: true }
    }

    const error = response.type === 'api_key_set' ? response.error : 'Unexpected response'
    return { success: false, error }
  })

  ipcMain.handle('api-key:clear', async () => {
    clearApiKey()
    await sidecar.send({
      id: crypto.randomUUID(),
      type: 'set_api_key',
      apiKey: '',
    })
    return { success: true }
  })
}
