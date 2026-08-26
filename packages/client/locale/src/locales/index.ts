/**
 * The common-namespace dictionaries. zh is the source of truth for the key
 * set (Chinese-first repo convention); every other language is checked
 * complete against it — a missing or extra key is a compile error.
 */
export { zh } from './zh.ts'
export { en } from './en.ts'
export { ja } from './ja.ts'
export { de } from './de.ts'
export { fr } from './fr.ts'
export { wy } from './wy.ts'
export type { CommonKey } from './zh.ts'
