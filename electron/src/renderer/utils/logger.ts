/**
 * Renderer-side logger — forwards to main process log file via IPC.
 * Also logs to browser console for DevTools visibility.
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error'

function write(level: LogLevel, component: string, message: string, ...args: unknown[]): void {
  // Format message with args
  let formatted = message
  let argIdx = 0
  formatted = formatted.replace(/%[sd]/g, () => {
    if (argIdx < args.length) {
      return String(args[argIdx++])
    }
    return '%s'
  })
  while (argIdx < args.length) {
    formatted += ' ' + String(args[argIdx++])
  }

  // Console output for DevTools
  const consoleFn = level === 'error' ? console.error : level === 'warn' ? console.warn : console.log
  consoleFn(`[${component}] ${formatted}`)

  // Forward to main process log file
  window.caddee.log(level, component, formatted)
}

export function createLogger(component: string) {
  return {
    debug: (msg: string, ...args: unknown[]) => write('debug', component, msg, ...args),
    info: (msg: string, ...args: unknown[]) => write('info', component, msg, ...args),
    warn: (msg: string, ...args: unknown[]) => write('warn', component, msg, ...args),
    error: (msg: string, ...args: unknown[]) => write('error', component, msg, ...args),
  }
}
