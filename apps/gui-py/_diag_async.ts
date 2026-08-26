import async_hooks from 'node:async_hooks'
import { resolve } from 'node:path'
import { pathToFileURL } from 'node:url'

const stacks = new Map<number, string>()
const types = new Map<number, string>()
const hook = async_hooks.createHook({
  init(asyncId: number, type: string, _trigger: number, _res: unknown) {
    types.set(asyncId, type)
    if (type === 'PROMISE' || type === 'MESSAGEPORT') {
      const e = new Error()
      stacks.set(asyncId, (e.stack || '').split('\n').slice(1).join('\n'))
    }
  },
  destroy(asyncId: number) { stacks.delete(asyncId); types.delete(asyncId) },
})
hook.enable()

setTimeout(() => {
  const markers = ['app-boot', 'mountRootInclude', 'cordis-plugin-loader',
    'EntryTree', 'loadEntry', 'cordis-plugin-include', 'packages/boot',
    'runJsonrpcAgent', 'boot(', 'dsh-app-boot']
  let n = 0
  const seen = new Set<string>()
  for (const [id, stack] of stacks) {
    if (!markers.some(m => stack.includes(m))) continue
    // collapse near-duplicates
    const key = stack.split('\n').slice(0, 4).join('|')
    if (seen.has(key)) continue
    seen.add(key)
    n++
    if (n <= 20) {
      console.error(`DIAG#${n} type=${types.get(id)} id=${id}`)
      for (const ln of stack.split('\n').slice(0, 16)) console.error('DIAGS ' + ln)
      console.error('DIAGS ---')
    }
  }
  console.error(`DIAG runtime-marker live promises/messageports: ${n} (unique ${seen.size})`)
  process.exit(0)
}, 9000)

const entry = pathToFileURL(resolve('packages/examples/jsonrpc-demo/src/bin.ts')).href
await import(entry)
