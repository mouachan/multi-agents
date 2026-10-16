import type { Locale } from '../i18n/translations'

const intlLocale = (locale: Locale) => (locale === 'fr' ? 'fr-FR' : 'en-US')

export function formatDateTime(value: string | null | undefined, locale: Locale): string {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return d.toLocaleString(intlLocale(locale), {
    year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

export function formatDate(value: string | null | undefined, locale: Locale): string {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return d.toLocaleDateString(intlLocale(locale), { year: 'numeric', month: 'short', day: 'numeric' })
}

export function formatTime(value: string | null | undefined, locale: Locale): string {
  if (!value) return ''
  return new Date(value).toLocaleTimeString(intlLocale(locale), { hour: '2-digit', minute: '2-digit' })
}

/** 850 -> "850 ms", 4200 -> "4.2 s", 95000 -> "1 min 35 s" */
export function formatDuration(ms: number | null | undefined): string {
  if (ms == null || Number.isNaN(ms)) return '—'
  if (ms < 1000) return `${Math.round(ms)} ms`
  const s = ms / 1000
  if (s < 60) return `${s.toFixed(s < 10 ? 1 : 0)} s`
  const m = Math.floor(s / 60)
  const rest = Math.round(s % 60)
  return rest ? `${m} min ${rest} s` : `${m} min`
}

export function formatMoney(amount: number | string | null | undefined, locale: Locale, digits = 0, currency = 'EUR'): string {
  const value = typeof amount === 'string' ? Number(amount) : amount
  if (value == null || Number.isNaN(value)) return '—'
  return new Intl.NumberFormat(intlLocale(locale), {
    style: 'currency', currency, maximumFractionDigits: digits,
  }).format(value)
}

export function formatNumber(value: number | null | undefined, locale: Locale): string {
  if (value == null) return '—'
  return new Intl.NumberFormat(intlLocale(locale)).format(value)
}

export function formatPercent(value: number | null | undefined): string {
  if (value == null) return '—'
  const pct = value <= 1 ? value * 100 : value
  return `${Math.round(pct)}%`
}

/** Numeric part of a business number (CLM-2024-0030 -> 20240030) for natural sorting. */
export function numericKey(value: string): number {
  const n = parseInt(value.replace(/\D/g, ''), 10)
  return Number.isNaN(n) ? 0 : n
}
