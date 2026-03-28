import { ipcMain, dialog, BrowserWindow } from 'electron'
import { writeFile, readFile } from 'fs/promises'
import { SidecarManager } from './sidecar'
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
}
