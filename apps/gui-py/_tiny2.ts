const greeting: string = 'hello-tsx'
const m = await import('node:path')
console.log(greeting, 'sep=', m.sep)
process.exit(0)
