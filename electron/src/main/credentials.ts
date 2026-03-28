import { safeStorage } from 'electron'
import { readFileSync, writeFileSync, unlinkSync, existsSync, mkdirSync } from 'fs'
import { join } from 'path'
import { homedir } from 'os'

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
  writeFileSync(CREDENTIALS_PATH, encrypted)
}

export function loadApiKey(): string | null {
  if (!existsSync(CREDENTIALS_PATH)) return null
  try {
    const encrypted = readFileSync(CREDENTIALS_PATH)
    return safeStorage.decryptString(encrypted)
  } catch {
    return null
  }
}

export function clearApiKey(): void {
  if (existsSync(CREDENTIALS_PATH)) {
    unlinkSync(CREDENTIALS_PATH)
  }
}

export function hasApiKey(): boolean {
  return existsSync(CREDENTIALS_PATH)
}
