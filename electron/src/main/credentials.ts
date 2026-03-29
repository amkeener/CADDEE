import { safeStorage } from 'electron'
import { readFileSync, writeFileSync, unlinkSync, existsSync, mkdirSync } from 'fs'
import { join } from 'path'
import { homedir } from 'os'
import { createLogger } from './logger'

const log = createLogger('credentials')

const CADDEE_DIR = join(homedir(), '.caddee')
const CREDENTIALS_PATH = join(CADDEE_DIR, 'credentials')

function ensureDir(): void {
  if (!existsSync(CADDEE_DIR)) {
    mkdirSync(CADDEE_DIR, { recursive: true })
  }
}

export function saveApiKey(key: string): void {
  ensureDir()
  const encrypted = safeStorage.encryptString(key)
  writeFileSync(CREDENTIALS_PATH, encrypted, { mode: 0o600 })
  log.info('API key saved to %s (%d bytes encrypted)', CREDENTIALS_PATH, encrypted.length)
}

export function loadApiKey(): string | null {
  if (!existsSync(CREDENTIALS_PATH)) {
    log.debug('No stored credentials found at %s', CREDENTIALS_PATH)
    return null
  }
  try {
    const encrypted = readFileSync(CREDENTIALS_PATH)
    const key = safeStorage.decryptString(encrypted)
    log.info('Loaded stored API key (%d chars)', key.length)
    return key
  } catch (err) {
    log.error('Failed to decrypt stored credentials: %s', err)
    return null
  }
}

export function clearApiKey(): void {
  if (existsSync(CREDENTIALS_PATH)) {
    unlinkSync(CREDENTIALS_PATH)
    log.info('Stored API key cleared')
  }
}

export function hasApiKey(): boolean {
  return existsSync(CREDENTIALS_PATH)
}
