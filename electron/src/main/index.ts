import { app, BrowserWindow, Menu } from 'electron'
import { join } from 'path'
import { setupIpcHandlers } from './ipc-handlers'
import { SidecarManager } from './sidecar'
import { loadApiKey } from './credentials'
import { createLogger } from './logger'

const log = createLogger('app')

let mainWindow: BrowserWindow | null = null
let sidecar: SidecarManager | null = null

function createWindow(): void {
  log.info('Creating main window')
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 900,
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

function buildMenu(): void {
  const template: Electron.MenuItemConstructorOptions[] = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Save Session',
          accelerator: 'CmdOrCtrl+S',
          click: () => mainWindow?.webContents.send('menu:save-session'),
        },
        {
          label: 'Open Session',
          accelerator: 'CmdOrCtrl+O',
          click: () => mainWindow?.webContents.send('menu:open-session'),
        },
        { type: 'separator' },
        {
          label: 'Import CAD File...',
          accelerator: 'CmdOrCtrl+I',
          click: () => mainWindow?.webContents.send('menu:import-file'),
        },
        { type: 'separator' },
        { role: 'quit' },
      ],
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        { role: 'selectAll' },
      ],
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' },
      ],
    },
  ]

  // macOS app menu
  if (process.platform === 'darwin') {
    template.unshift({
      label: app.getName(),
      submenu: [
        { role: 'about' },
        { type: 'separator' },
        { role: 'hide' },
        { role: 'hideOthers' },
        { role: 'unhide' },
        { type: 'separator' },
        { role: 'quit' },
      ],
    })
  }

  Menu.setApplicationMenu(Menu.buildFromTemplate(template))
}

app.whenReady().then(async () => {
  log.info('App ready — starting CADDEE (version=%s, electron=%s)', app.getVersion(), process.versions.electron)

  sidecar = new SidecarManager()
  sidecar.start()

  setupIpcHandlers(sidecar)
  buildMenu()
  createWindow()

  // Send API key to sidecar at startup
  const envKey = process.env.ANTHROPIC_API_KEY
  const storedKey = loadApiKey()
  const apiKey = envKey || storedKey
  const keySource = envKey ? 'env' : storedKey ? 'stored' : 'none'
  log.info('API key source: %s', keySource)

  if (apiKey) {
    try {
      await sidecar.send({
        id: crypto.randomUUID(),
        type: 'set_api_key',
        apiKey: apiKey,
      })
      log.info('API key sent to sidecar')
    } catch {
      log.error('Failed to send API key to sidecar')
    }
  } else {
    log.warn('No API key configured — showing setup modal')
    // Notify renderer that no API key is configured
    mainWindow?.webContents.once('did-finish-load', () => {
      mainWindow?.webContents.send('api-key:missing')
    })
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  log.info('All windows closed')
  sidecar?.stop()
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('before-quit', () => {
  log.info('App quitting')
  sidecar?.stop()
})
