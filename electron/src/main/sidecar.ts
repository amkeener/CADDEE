import { ChildProcess, spawn } from 'child_process'
import { join } from 'path'
import { EventEmitter } from 'events'
import type { SidecarRequest, SidecarResponse } from '../../../shared/messages'
import { createLogger } from './logger'

const log = createLogger('sidecar')

export class SidecarManager extends EventEmitter {
  private process: ChildProcess | null = null
  private buffer = ''
  private pendingCallbacks = new Map<string, {
    resolve: (value: SidecarResponse) => void
    reject: (error: Error) => void
  }>()

  start(): void {
    const sidecarPath = join(__dirname, '../../../sidecar')

    this.process = spawn('uv', ['run', 'python', '-m', 'caddee.main'], {
      cwd: sidecarPath,
      stdio: ['pipe', 'pipe', 'pipe'],
      env: {
        ...process.env,
        PYTHONUNBUFFERED: '1'
      }
    })

    this.process.stdout?.on('data', (data: Buffer) => {
      this.buffer += data.toString()
      this.processBuffer()
    })

    this.process.stderr?.on('data', (data: Buffer) => {
      const text = data.toString().trim()
      if (text) log.debug('stderr: %s', text)
    })

    this.process.on('exit', (code) => {
      log.warn('Process exited with code %d', code ?? -1)
      this.process = null
      this.rejectAllPending(new Error(`Sidecar exited with code ${code}`))
    })

    log.info('Process started (pid=%d)', this.process.pid ?? 0)
  }

  stop(): void {
    if (this.process) {
      log.info('Stopping sidecar process')
      this.process.kill()
      this.process = null
    }
  }

  async send(request: SidecarRequest): Promise<SidecarResponse> {
    if (!this.process?.stdin) {
      log.error('Cannot send — sidecar not running')
      throw new Error('Sidecar not running')
    }

    log.debug('Sending: id=%s type=%s', request.id.slice(0, 8), request.type)
    const sendTime = Date.now()

    return new Promise((resolve, reject) => {
      this.pendingCallbacks.set(request.id, {
        resolve: (value) => {
          log.debug('Response: id=%s type=%s (%dms)',
            request.id.slice(0, 8), value.type, Date.now() - sendTime)
          resolve(value)
        },
        reject,
      })
      const line = JSON.stringify(request) + '\n'
      this.process!.stdin!.write(line)
    })
  }

  private processBuffer(): void {
    const lines = this.buffer.split('\n')
    this.buffer = lines.pop() ?? ''

    for (const line of lines) {
      if (!line.trim()) continue
      try {
        const response: SidecarResponse = JSON.parse(line)
        const callback = this.pendingCallbacks.get(response.id)
        if (callback) {
          this.pendingCallbacks.delete(response.id)
          callback.resolve(response)
        }
      } catch {
        log.error('Failed to parse response: %s', line.slice(0, 200))
      }
    }
  }

  private rejectAllPending(error: Error): void {
    for (const [id, callback] of this.pendingCallbacks) {
      callback.reject(error)
      this.pendingCallbacks.delete(id)
    }
  }
}
