import { ChildProcess, spawn } from 'child_process'
import { join } from 'path'
import { EventEmitter } from 'events'
import type { SidecarRequest, SidecarResponse } from '../../../shared/messages'

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
      console.error('[sidecar stderr]', data.toString())
    })

    this.process.on('exit', (code) => {
      console.log(`[sidecar] exited with code ${code}`)
      this.process = null
      this.rejectAllPending(new Error(`Sidecar exited with code ${code}`))
    })

    console.log('[sidecar] started')
  }

  stop(): void {
    if (this.process) {
      this.process.kill()
      this.process = null
    }
  }

  async send(request: SidecarRequest): Promise<SidecarResponse> {
    if (!this.process?.stdin) {
      throw new Error('Sidecar not running')
    }

    return new Promise((resolve, reject) => {
      this.pendingCallbacks.set(request.id, { resolve, reject })
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
        console.error('[sidecar] failed to parse:', line)
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
