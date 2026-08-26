import type { CommonKey } from './zh.ts'

/** de dictionary for the common namespace, checked complete against the zh key set. */
export const de = {
  'ok': 'OK',
  'cancel': 'Abbrechen',
  'close': 'Schließen',
  'copy': 'Kopieren',
  'copied': 'Kopiert',
  'retry': 'Wiederholen',
  'loading': 'Wird geladen…',
  'load.failed': 'Laden fehlgeschlagen',
  'submit': 'Senden',
  'submitting': 'Wird gesendet…',
  'next': 'Weiter',
  'previous': 'Zurück',
  'skip': 'Überspringen',
  'delete': 'Löschen',
  'edit': 'Bearbeiten',
  'save': 'Speichern',
  'search': 'Suchen',
  'more': 'Mehr',
  'collapse': 'Einklappen',
  'expand': 'Erweitern',
  'back': 'Zurück',
  'unknown': 'Unbekannt',
  'none': 'Keine',
  'truncated': 'Abgeschnitten',
} satisfies Record<CommonKey, string>
