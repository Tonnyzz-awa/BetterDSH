/** `settings.locale` namespace dictionaries (the Language row's copy). */

/** Simplified Chinese dictionary (the key-set source of truth). */
export const zh = {
  'language.title': '语言',
} satisfies Record<string, string>

/** The settings.locale namespace key union. */
export type SettingsLocaleKey = keyof typeof zh

/** English dictionary, checked complete against the zh key set. */
export const en = {
  'language.title': 'Language',
} satisfies Record<SettingsLocaleKey, string>

/** Japanese dictionary. */
export const ja = {
  'language.title': '言語',
} satisfies Record<SettingsLocaleKey, string>

/** German dictionary. */
export const de = {
  'language.title': 'Sprache',
} satisfies Record<SettingsLocaleKey, string>

/** French dictionary. */
export const fr = {
  'language.title': 'Langue',
} satisfies Record<SettingsLocaleKey, string>

/** Literary Chinese (文言) dictionary. */
export const wy = {
  'language.title': '文言',
} satisfies Record<SettingsLocaleKey, string>
