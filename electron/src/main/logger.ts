/**
 * CADDEE Logger — file-based logging with rotation for the Electron main process.
 *
 * Logs to ~/.caddee/logs/electron.log with automatic rotation (5 MB max, 3 backups).
 * Also outputs to console for dev tools visibility.
 */

import { appendFileSync, existsSync, mkdirSync, renameSync, statSync } from 'fs'
import { join } from 'path'
import { homedir } from 'os'

const LOG_DIR = join(homedir(), '.caddee', 'logs')
const LOG_PATH = join(LOG_DIR, 'electron.log')
const MAX_SIZE = 5 * 1024 * 1024 // 5 MB
const MAX_BACKUPS = 3

type LogLevel = 'debug' | 'info' | 'warn' | 'error'

const LEVEL_ORDER: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
}

let currentLevel: LogLevel = 'debug'

function ensureLogDir(): void {
  if (!existsSync(LOG_DIR)) {
    mkdirSync(LOG_DIR, { recursive: true })
  }
}

function rotate(): void {
  try {
    if (!existsSync(LOG_PATH)) return
    const stats = statSync(LOG_PATH)
    if (stats.size < MAX_SIZE) return

    // Shift backup files: .3 -> delete, .2 -> .3, .1 -> .2, current -> .1
    for (let i = MAX_BACKUPS; i >= 1; i--) {
      const from = i === 1 ? LOG_PATH : `${LOG_PATH}.${i - 1}`
      const to = `${LOG_PATH}.${i}`
      if (existsSync(from)) {
        if (i === MAX_BACKUPS && existsSync(to)) {
          // oldest backup — just overwrite
        }
        renameSync(from, to)
      }
    }
  } catch {
    // Rotation failure shouldn't crash the app
  }
}

function formatTimestamp(): string {
  const now = new Date()
  return now.toISOString().replace('T', ' ').replace('Z', '')
}

function write(level: LogLevel, component: string, message: string, ...args: unknown[]): void {
  if (LEVEL_ORDER[level] < LEVEL_ORDER[currentLevel]) return

  // Format message with args (simple %s/%d substitution)
  let formatted = message
  let argIdx = 0
  formatted = formatted.replace(/%[sd]/g, () => {
    if (argIdx < args.length) {
      return String(args[argIdx++])
    }
    return '%s'
  })
  // Append remaining args
  while (argIdx < args.length) {
    formatted += ' ' + String(args[argIdx++])
  }

  const line = `${formatTimestamp()} [${level.toUpperCase().padEnd(5)}] ${component}: ${formatted}\n`

  // Console output
  const consoleFn = level === 'error' ? console.error : level === 'warn' ? console.warn : console.log
  consoleFn(`[${component}] ${formatted}`)

  // File output
  try {
    ensureLogDir()
    rotate()
    appendFileSync(LOG_PATH, line, 'utf-8')
  } catch {
    // File write failure shouldn't crash the app
  }
}

export function setLogLevel(level: LogLevel): void {
  currentLevel = level
}

export function createLogger(component: string) {
  return {
    debug: (msg: string, ...args: unknown[]) => write('debug', component, msg, ...args),
    info: (msg: string, ...args: unknown[]) => write('info', component, msg, ...args),
    warn: (msg: string, ...args: unknown[]) => write('warn', component, msg, ...args),
    error: (msg: string, ...args: unknown[]) => write('error', component, msg, ...args),
  }
}

export const log = createLogger('main')
