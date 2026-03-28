import { app, BrowserWindow } from 'electron'
import { join } from 'path'
import { setupIpcHandlers } from './ipc-handlers'
import { SidecarManager } from './sidecar'

let mainWindow: BrowserWindow | null = null
let sidecar: SidecarManager | null = null

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 800,
    minHeight: 600,
    title: 'CADDEE',
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
        sandbox: false,
      contextIsolation: true,
      nodeIntegration: false
    }
  })

  if (process.env.ELECTRON_RENDERER_URL) {
    mainWindow.loadURL(process.env.ELECTRON_RENDERER_URL)
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

app.whenReady().then(() => {
  sidecar = new SidecarManager()
  sidecar.start()

  setupIpcHandlers(sidecar)
  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  sidecar?.stop()
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('before-quit', () => {
  sidecar?.stop()
})
