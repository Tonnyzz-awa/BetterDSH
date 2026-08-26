/** Shell chrome and General-nav dictionaries; feature rows own their copy. */

/** Simplified Chinese dictionary (the key-set source of truth). */
export const zh = {
  'trigger': '设置',
  'title': '设置',
  'close': '关闭',
  'openDocument': '打开配置文件',
  'openDocument.error': '无法打开配置文件',
  'general.nav': '通用设置',
} satisfies Record<string, string>

/** The settings namespace key union. */
export type SettingsKey = keyof typeof zh

/** English dictionary, checked complete against the zh key set. */
export const en = {
  'trigger': 'Settings',
  'title': 'Settings',
  'close': 'Close',
  'openDocument': 'Open configuration file',
  'openDocument.error': 'Could not open configuration file',
  'general.nav': 'General',
} satisfies Record<SettingsKey, string>

/** Japanese dictionary. */
export const ja = {
  'trigger': '設定',
  'title': '設定',
  'close': '閉じる',
  'openDocument': '設定ファイルを開く',
  'openDocument.error': '設定ファイルを開けませんでした',
  'general.nav': '一般設定',
} satisfies Record<SettingsKey, string>

/** German dictionary. */
export const de = {
  'trigger': 'Einstellungen',
  'title': 'Einstellungen',
  'close': 'Schließen',
  'openDocument': 'Konfigurationsdatei öffnen',
  'openDocument.error': 'Konfigurationsdatei konnte nicht geöffnet werden',
  'general.nav': 'Allgemein',
} satisfies Record<SettingsKey, string>

/** French dictionary. */
export const fr = {
  'trigger': 'Paramètres',
  'title': 'Paramètres',
  'close': 'Fermer',
  'openDocument': 'Ouvrir le fichier de configuration',
  'openDocument.error': 'Impossible d’ouvrir le fichier de configuration',
  'general.nav': 'Général',
} satisfies Record<SettingsKey, string>

/** Literary Chinese (文言) dictionary. */
export const wy = {
  'trigger': '設',
  'title': '設',
  'close': '閉',
  'openDocument': '開配置文件',
  'openDocument.error': '無法開配置文件',
  'general.nav': '常設',
} satisfies Record<SettingsKey, string>
