const cp = require('child_process')
const REPO = 'D:/Deepseek/dsh-source-code'
const env = Object.assign({}, process.env, {
  DSH_SESSION_ROOT: REPO + '/apps/gui-py/data/sessions',
  DSH_CWD: REPO,
})
const child = cp.spawn('C:\\Program Files\\nodejs\\node.EXE', [
  '--report-on-signal',
  '--report-signal=SIGBREAK',
  '--report-directory=C:/Temp/dsh_rep',
  '--import', 'tsx/esm',
  'packages/examples/jsonrpc-demo/src/bin.ts',
  'apps/gui-py/data/runtime.cordis.yml',
], { cwd: REPO, env, stdio: ['pipe', 'pipe', 'pipe'] })
child.stdout.on('data', d => process.stdout.write('[OUT] ' + d))
child.stderr.on('data', d => process.stderr.write('[ERR] ' + d))
console.log('spawned pid', child.pid)
setTimeout(() => {
  console.log('=== sending SIGBREAK to trigger report ===')
  try { process.kill(child.pid, 'SIGBREAK') } catch (e) { console.log('kill err', e.message) }
}, 12000)
setTimeout(() => { try { child.kill('SIGKILL') } catch (e) {} }, 18000)
