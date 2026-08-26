import { resolve } from 'node:path'
import { boot, installFailLoud } from '@deepseek-ai/dsh-app-boot'
import { FiberState } from '@deepseek-ai/cordis'

installFailLoud('diag')
const NAME = 'diag'
const configPath = resolve(process.cwd(), 'apps/gui-py/data/runtime.cordis.yml')

process.on('unhandledRejection', (e) => {
  process.stderr.write('DIAG unhandledRejection: ' + (e instanceof Error ? (e.stack ?? e.message) : String(e)) + '\n')
})
process.on('uncaughtException', (e) => {
  process.stderr.write('DIAG uncaughtException: ' + (e instanceof Error ? (e.stack ?? e.message) : String(e)) + '\n')
})

setTimeout(() => {
  try {
    const ctxRef = (globalThis as any).__ctx
    if (!ctxRef) { process.stderr.write('DIAG no ctx captured\n'); return }
    const loader = ctxRef.get('loader')
    if (!loader) { process.stderr.write('DIAG no loader\n'); return }
    process.stderr.write('DIAG entry states @10s:\n')
    for (const entry of loader.entries()) {
      const f = entry.fiber
      const state = f ? (FiberState[f.state] ?? String(f.state)) : 'no-fiber'
      const hasInit = !!(entry as any)._initTask
      const inertia = f ? (f as any).inertia !== undefined : false
      process.stderr.write(`  ${entry.options.id} name=${entry.options.name} state=${state} hasInitTask=${hasInit} disabled=${!!entry.disabled}\n`)
    }
    const tasks = loader.getTasks?.() ?? []
    process.stderr.write(`DIAG pending tasks: ${tasks.length}\n`)
  } catch (e: any) {
    process.stderr.write('DIAG err ' + (e?.stack ?? e) + '\n')
  }
}, 10000)

const ctx = await boot(NAME, configPath, undefined, async (ctx) => {
  (globalThis as any).__ctx = ctx
  ctx.on('loader/entry-init', (entry: any) => {
    process.stderr.write(`DIAG entry-init: ${entry.options.name}\n`)
  })
  ctx.on('loader/entry-dispose', (entry: any) => {
    process.stderr.write(`DIAG entry-dispose: ${entry.options?.name}\n`)
  })
}, undefined)
process.stderr.write('DIAG boot returned, ctx has loader=' + !!ctx.get('loader') + '\n')
