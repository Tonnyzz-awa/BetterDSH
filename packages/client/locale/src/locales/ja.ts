import type { CommonKey } from './zh.ts'

/** ja dictionary for the common namespace, checked complete against the zh key set. */
export const ja = {
  'ok': '決定',
  'cancel': 'キャンセル',
  'close': '閉じる',
  'copy': 'コピー',
  'copied': 'コピーしました',
  'retry': '再試行',
  'loading': '読み込み中…',
  'load.failed': '読み込みに失敗しました',
  'submit': '送信',
  'submitting': '送信中…',
  'next': '次へ',
  'previous': '前へ',
  'skip': 'スキップ',
  'delete': '削除',
  'edit': '編集',
  'save': '保存',
  'search': '検索',
  'more': 'もっと',
  'collapse': '折りたたむ',
  'expand': '展開',
  'back': '戻る',
  'unknown': '不明',
  'none': 'なし',
  'truncated': '切り捨てられました',
} satisfies Record<CommonKey, string>
