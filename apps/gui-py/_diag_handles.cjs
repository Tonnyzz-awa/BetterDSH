const cp = require('child_process')
const REPO = 'D:/Deepseek/dsh-source-code'
const env = Object.assign({}, process.env, {
  DSH_SESSION_ROOT: REPO + '/apps/gui-py/data/sessions',
  DSH_CWD: REPO,
})
const child = cp.spawn('C:\\Program Files\\nodejs\\node.EXE', [
  '--inspect=127.0.0.1:0',
  '--import', 'tsx/esm',
  'packages/examples/jsonrpc-demo/src/bin.ts',
  'apps/gui-py/data/runtime.cordis.yml',
], { cwd: REPO, env, stdio: ['pipe', 'pipe', 'pipe'] })

let wsUrl = null
child.stderr.on('data', d => {
  const s = d.toString()
  const m = s.match(/ws:\/\/[^\s]+/)
  if (m && !wsUrl) { wsUrl = m[0]; connect(wsUrl) }
})
let ws, msgId = 0
const pending = new Map()
function send(method, params, resolve) {
  const id = ++msgId
  if (resolve) pending.set(id, resolve)
  ws.send(JSON.stringify({ id, method, params: params ?? {} }))
}
function connect(url) {
  ws = new WebSocket(url)
  ws.onopen = () => {
    send('Runtime.enable')
    setTimeout(() => {
      send('Runtime.evaluate', {
        expression: `(() => {
          const out = [];
          for (const h of process._getActiveHandles()) {
            const o = { type: h.constructor.name };
            try {
              if (h.constructor.name === 'Socket') {
                o.remote = h.remoteAddress + ':' + h.remotePort;
                o.local = h.localAddress + ':' + h.localPort;
                o.readyState = h.readyState;
              } else if (h.constructor.name === 'MessagePort') {
                o.active = h.active;
              } else if (h.constructor.name === 'ChildProcess') {
                o.spawnfile = h.spawnfile; o.pid = h.pid;
              } else if (h.constructor.name === 'Server') {
                o.listening = h.listening;
              } else if (h.constructor.name === 'Timer' || h.constructor.name === 'Timeout') {
                o._idleTimeout = h._idleTimeout;
              } else if (h.constructor.name === 'Pipe') {
                o.fd = h.fd;
              }
            } catch (e) { o.err = String(e) }
            out.push(o)
          }
          return JSON.stringify(out, null, 2);
        })()`,
        returnByValue: true,
      }, (res) => {
        console.log('RAW:', JSON.stringify(res).slice(0, 2000))
        try { child.kill('SIGKILL') } catch (e) {}
        process.exit(0)
      })
    }, 8000)
  }
  ws.onerror = (e) => console.log('WS error', e.message || e)
}
