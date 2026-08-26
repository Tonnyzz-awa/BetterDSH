import { redactSecrets } from './packages/settings/settings/src/redact.ts'

// 1. object-secret still stripped (regression guard for existing behavior)
const objSchema = { type: 'object', dict: { apiKey: { type: 'string', meta: { role: 'secret' } } } }
const r1 = redactSecrets(objSchema as never, { apiKey: 'x', other: 1 })
console.log('1) object secret ->', JSON.stringify(r1))

// 2. secret reachable through a transform/union node wrapping a structured value
//    MUST now fail closed (throw) instead of leaking.
const structuredSchema = { type: 'transform' }
try {
  redactSecrets(structuredSchema as never, { nested: 'LEAKED_SECRET' })
  console.log('2) transform+structured: NO THROW  <-- BUG')
} catch (e) {
  console.log('2) transform+structured: threw  <-- FIXED ->', (e as Error).message)
}

// 3. scalar value through a transform node must still pass through (no regression)
try {
  const r3 = redactSecrets(structuredSchema as never, 'scalar-value')
  console.log('3) transform+scalar: returned  <-- OK ->', JSON.stringify(r3))
} catch (e) {
  console.log('3) transform+scalar: threw  <-- REGRESSION ->', (e as Error).message)
}

// 4. array value through a non-recursable node must fail closed
try {
  redactSecrets(structuredSchema as never, ['a', 'b'])
  console.log('4) transform+array: NO THROW  <-- BUG')
} catch (e) {
  console.log('4) transform+array: threw  <-- FIXED ->', (e as Error).message)
}
