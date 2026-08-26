import { resolve } from 'node:path'
import { boot, installFailLoud } from '@deepseek-ai/dsh-app-boot'
import type { PatchOptions } from '@deepseek-ai/cordis-plugin-include'

installFailLoud('diag')
const NAME = 'diag'
const configPath = resolve(process.cwd(), 'apps/gui-py/data/runtime.cordis.yml')

// Which entry ids to DISABLE (via patches) for this bisect run.
const disable = (process.env['DIAG_DISABLE'] ?? '').split(',').filter(Boolean)
const patches: PatchOptions[] = disable.map(id => ({ id, disabled: true }))

const t0 = Date.now()
try {
  const ctx = await boot(NAME, configPath, patches)
  process.stderr.write(`DIAG OK booted in ${Date.now() - t0}ms with disabled=[${disable}]\n`)
} catch (e: any) {
  process.stderr.write(`DIAG FAIL after ${Date.now() - t0}ms disabled=[${disable}]: ${e?.stack ?? e}\n`)
}
process.exit(0)
