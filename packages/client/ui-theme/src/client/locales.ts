/** `settings.theme` namespace dictionaries (the Appearance row's copy). */

/** Simplified Chinese dictionary (the key-set source of truth). */
export const zh = {
  'appearance.title': '外观',
  'appearance.light': '浅色',
  'appearance.dark': '深色',
  'appearance.system': '跟随系统',
} satisfies Record<string, string>

/** The settings.theme namespace key union. */
export type ThemeKey = keyof typeof zh

/** English dictionary, checked complete against the zh key set. */
export const en = {
  'appearance.title': 'Appearance',
  'appearance.light': 'Light',
  'appearance.dark': 'Dark',
  'appearance.system': 'System',
} satisfies Record<ThemeKey, string>

/** Japanese dictionary. */
export const ja = {
  'appearance.title': '外観',
  'appearance.light': 'ライト',
  'appearance.dark': 'ダーク',
  'appearance.system': 'システム設定に従う',
} satisfies Record<ThemeKey, string>

/** German dictionary. */
export const de = {
  'appearance.title': 'Darstellung',
  'appearance.light': 'Hell',
  'appearance.dark': 'Dunkel',
  'appearance.system': 'System',
} satisfies Record<ThemeKey, string>

/** French dictionary. */
export const fr = {
  'appearance.title': 'Apparence',
  'appearance.light': 'Clair',
  'appearance.dark': 'Sombre',
  'appearance.system': 'Système',
} satisfies Record<ThemeKey, string>

/** Literary Chinese (文言) dictionary. */
export const wy = {
  'appearance.title': '觀',
  'appearance.light': '明',
  'appearance.dark': '暗',
  'appearance.system': '從系統',
} satisfies Record<ThemeKey, string>
