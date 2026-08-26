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

const scripts = new Map()
let wsUrl = null
child.stderr.on('data', d => {
  const s = d.toString()
  process.stderr.write('[ERR] ' + s)
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
    send('Debugger.enable')
    send('Debugger.setAsyncCallStackDepth', { maxDepth: 32 })
    setTimeout(() => {
      send('Runtime.evaluate', {
        expression: `(() => {
          const h = (process._getActiveHandles() || []).map(x => x.constructor.name);
          const byH = {}; h.forEach(n => byH[n] = (byH[n]||0)+1);
          return JSON.stringify(byH);
        })()`,
        returnByValue: true,
      }, (res) => {
        console.log('ACTIVE HANDLES:', res && res.result && res.result.result && res.result.result.value)
        console.log('=== pause ===')
        send('Debugger.pause')
      })
    }, 8000)
  }
  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data)
    if (msg.id && pending.has(msg.id)) { const r = pending.get(msg.id); pending.delete(msg.id); r(msg) }
    else if (msg.method === 'Debugger.scriptParsed') {
      scripts.set(String(msg.params.scriptId), msg.params.url)
    }
    else if (msg.method === 'Debugger.paused') {
      console.log('=== PAUSED. frames:', msg.params.callFrames.length, 'hasAsync:', !!msg.params.asyncStackTrace)
      for (const f of msg.params.callFrames) {
        const url = scripts.get(String(f.location.scriptId)) || f.url || '(unknown)'
        console.log('  ', f.functionName || '(anon)', url + ':' + (f.location.lineNumber + 1))
      }
      if (msg.params.asyncStackTrace) {
        console.log('--- asyncStackTrace ---')
        let st = msg.params.asyncStackTrace
        while (st) {
          for (const f of st.callFrames) {
            console.log('  (async)', f.functionName || '(anon)', (f.url || '') + ':' + (f.location.lineNumber + 1))
          }
          st = st.parent
        }
      }
    }
  }
  ws.onerror = (e) => console.log('WS error', e.message || e)
  setTimeout(() => { try { child.kill('SIGKILL') } catch (e) {}; process.exit(0) }, 16000)
}
