import { resolve } from 'node:path'
import { pathToFileURL } from 'node:url'

setTimeout(() => {
  try {
    const proc = process as any
    const handles = proc._getActiveHandles().map((h: any) => {
      const o: any = { type: h.constructor?.name }
      try {
        const t = h.constructor?.name
        if (t === 'Socket') {
          o.remote = (h.remoteAddress ?? '?') + ':' + (h.remotePort ?? '?')
          o.local = (h.localAddress ?? '?') + ':' + (h.localPort ?? '?')
          o.readyState = h.readyState
        } else if (t === 'MessagePort') {
          o.active = h.active
          o.hasRef = h.hasRef?.()
        } else if (t === 'Timer' || t === 'Timeout' || t === 'Immediate') {
          o._idleTimeout = h._idleTimeout
        } else if (t === 'ChildProcess') {
          o.spawnfile = h.spawnfile; o.pid = h.pid
        } else if (t === 'Server') {
          o.listening = h.listening
        }
      } catch (e: any) { o.err = String(e) }
      return o
    })
    const reqs = proc._getActiveRequests().map((r: any) => r.constructor?.name)
    console.error('DIAG handles=' + JSON.stringify(handles))
    console.error('DIAG requests=' + JSON.stringify(reqs))
  } catch (e: any) {
    console.error('DIAG err ' + (e?.stack ?? e))
  }
}, 9000)

const entry = pathToFileURL(resolve('packages/examples/jsonrpc-demo/src/bin.ts')).href
await import(entry)
