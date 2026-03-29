import { ipcMain, dialog, BrowserWindow, shell } from 'electron'
import { writeFile, readFile } from 'fs/promises'
import { SidecarManager } from './sidecar'
import { saveApiKey, clearApiKey, hasApiKey } from './credentials'
import { createLogger } from './logger'
import type { SidecarRequest } from '../../../shared/messages'

const log = createLogger('ipc')

export function setupIpcHandlers(sidecar: SidecarManager): void {
  log.info('Registering IPC handlers')

  // Forward renderer logs to the main log file
  ipcMain.on('log:write', (_event, level: string, component: string, message: string) => {
    const rendererLog = createLogger(`renderer:${component}`)
    const fn = level === 'error' ? rendererLog.error
      : level === 'warn' ? rendererLog.warn
      : level === 'debug' ? rendererLog.debug
      : rendererLog.info
    fn(message)
  })

  // Open URLs in the user's default browser (not an Electron window)
  ipcMain.on('shell:open-external', (_event, url: string) => {
    if (url.startsWith('https://')) {
      log.debug('Opening external URL: %s', url)
      shell.openExternal(url)
    }
  })

  ipcMain.handle('sidecar:send', async (_event, request: SidecarRequest) => {
    log.debug('sidecar:send type=%s', request.type)
    return sidecar.send(request)
  })

  ipcMain.handle('sidecar:ping', async () => {
    log.debug('sidecar:ping')
    return { status: 'ok' }
  })

  // --- Export Handlers ---

  ipcMain.handle('export:stl', async (_event, stlBase64: string) => {
    log.info('Export STL requested (%d chars b64)', stlBase64.length)
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
    log.info('STL exported to %s (%d bytes)', result.filePath, buffer.length)
    return { success: true, path: result.filePath }
  })

  ipcMain.handle('export:scad', async (_event, scadCode: string) => {
    log.info('Export SCAD requested (%d chars)', scadCode.length)
    const win = BrowserWindow.getFocusedWindow()
    if (!win) return { success: false }

    const result = await dialog.showSaveDialog(win, {
      title: 'Export OpenSCAD',
      defaultPath: 'model.scad',
      filters: [{ name: 'OpenSCAD Files', extensions: ['scad'] }],
    })

    if (result.canceled || !result.filePath) return { success: false }

    await writeFile(result.filePath, scadCode, 'utf-8')
    log.info('SCAD exported to %s', result.filePath)
    return { success: true, path: result.filePath }
  })

  // --- Session Handlers ---

  ipcMain.handle('session:save', async (_event, sessionJson: string) => {
    log.info('Session save requested (%d chars)', sessionJson.length)
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
    log.info('Session open requested')
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
      log.debug('API key status: env')
      return { configured: true, source: 'env' as const }
    }
    if (hasApiKey()) {
      log.debug('API key status: stored')
      return { configured: true, source: 'stored' as const }
    }
    log.debug('API key status: none')
    return { configured: false, source: 'none' as const }
  })

  ipcMain.handle('api-key:save', async (_event, key: string) => {
    log.info('Saving API key (length=%d)', key.length)
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
    log.info('Clearing stored API key')
    clearApiKey()
    await sidecar.send({
      id: crypto.randomUUID(),
      type: 'set_api_key',
      apiKey: '',
    })
    return { success: true }
  })
}
