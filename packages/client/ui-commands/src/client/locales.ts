/** `command` namespace dictionaries (the popupSelect shell's copy). */

/** Simplified Chinese dictionary (the key-set source of truth). */
export const zh = {
  'search.placeholder': '搜索…',
  'search.aria': '筛选选项',
  'status.loading': '正在加载选项…',
  'status.applying': '正在应用…',
  'status.empty': '无选项',
  'overlay.aria': '/{command} 选项',
  'listbox.aria': '/{command} 匹配项',
} satisfies Record<string, string>

/** The command namespace key union. */
export type CommandKey = keyof typeof zh

/** English dictionary, checked complete against the zh key set. */
export const en = {
  'search.placeholder': 'Search…',
  'search.aria': 'Filter options',
  'status.loading': 'Loading options…',
  'status.applying': 'Applying…',
  'status.empty': 'No options',
  'overlay.aria': '/{command} options',
  'listbox.aria': '/{command} matches',
} satisfies Record<CommandKey, string>

/** Japanese dictionary. */
export const ja = {
  'search.placeholder': '検索…',
  'search.aria': 'オプションを絞り込む',
  'status.loading': 'オプションを読み込み中…',
  'status.applying': '適用中…',
  'status.empty': 'オプションなし',
  'overlay.aria': '/{command} のオプション',
  'listbox.aria': '/{command} の候補',
} satisfies Record<CommandKey, string>

/** German dictionary. */
export const de = {
  'search.placeholder': 'Suchen…',
  'search.aria': 'Optionen filtern',
  'status.loading': 'Optionen werden geladen…',
  'status.applying': 'Wird angewendet…',
  'status.empty': 'Keine Optionen',
  'overlay.aria': '/{command} Optionen',
  'listbox.aria': '/{command} Treffer',
} satisfies Record<CommandKey, string>

/** French dictionary. */
export const fr = {
  'search.placeholder': 'Rechercher…',
  'search.aria': 'Filtrer les options',
  'status.loading': 'Chargement des options…',
  'status.applying': 'Application…',
  'status.empty': 'Aucune option',
  'overlay.aria': 'Options /{command}',
  'listbox.aria': 'Correspondances /{command}',
} satisfies Record<CommandKey, string>

/** Literary Chinese (文言) dictionary. */
export const wy = {
  'search.placeholder': '索…',
  'search.aria': '篩選',
  'status.loading': '載選項中…',
  'status.applying': '施用中…',
  'status.empty': '無選項',
  'overlay.aria': '/{command} 選項',
  'listbox.aria': '/{command} 匹',
} satisfies Record<CommandKey, string>
