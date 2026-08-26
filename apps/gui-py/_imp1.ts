console.error('[IMP] before import sdk-jsonrpc-server')
const m = await import('@deepseek-ai/dsh-sdk-jsonrpc-server')
console.error('[IMP] after import OK keys=' + Object.keys(m).length)
process.exit(0)
