import { useMemo, useState, type ReactNode } from 'react'
import { ArrowDown, ArrowUp, ChevronLeft, ChevronRight, ChevronsUpDown, RefreshCw, Search, X } from 'lucide-react'
import { useTranslation } from '../../i18n/LanguageContext'
import { cn } from '../../lib/cn'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'
import { EmptyState, ErrorBanner } from '../ui/Feedback'
import { KpiCard } from '../ui/KpiCard'

export interface Column<T> {
  key: string
  header: ReactNode
  cell: (row: T) => ReactNode
  /** value used to sort this column (omit = not sortable) */
  sortValue?: (row: T) => string | number
  className?: string
}

export interface Kpi {
  key: string
  label: ReactNode
  value: ReactNode
  hint?: ReactNode
  icon: ReactNode
  accent: string
  /** status filter applied when the card is clicked */
  status?: string
}

interface EntityTableProps<T> {
  rows: T[]
  loading: boolean
  error?: string | null
  onRetry: () => void
  columns: Column<T>[]
  rowKey: (row: T) => string
  onRowClick: (row: T) => void
  statusOf: (row: T) => string
  statusOptions: { value: string; label: string }[]
  searchText: (row: T) => string
  searchPlaceholder: string
  kpis: Kpi[]
  defaultSort: { key: string; dir: 'asc' | 'desc' }
  extraFilter?: { label: string; options: { value: string; label: string }[]; apply: (row: T, value: string) => boolean }
  pageSize?: number
}

export function EntityTable<T>({
  rows, loading, error, onRetry, columns, rowKey, onRowClick, statusOf, statusOptions, searchText,
  searchPlaceholder, kpis, defaultSort, extraFilter, pageSize = 12,
}: EntityTableProps<T>) {
  const { t } = useTranslation()
  const [query, setQuery] = useState('')
  const [status, setStatus] = useState('')
  const [extra, setExtra] = useState('')
  const [sort, setSort] = useState(defaultSort)
  const [page, setPage] = useState(1)

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    let out = rows.filter((r) =>
      (!status || statusOf(r) === status)
      && (!q || searchText(r).toLowerCase().includes(q))
      && (!extra || !extraFilter || extraFilter.apply(r, extra)))
    const col = columns.find((c) => c.key === sort.key)
    if (col?.sortValue) {
      const sv = col.sortValue
      out = [...out].sort((a, b) => {
        const va = sv(a)
        const vb = sv(b)
        const cmp = typeof va === 'number' && typeof vb === 'number' ? va - vb : String(va).localeCompare(String(vb))
        return sort.dir === 'asc' ? cmp : -cmp
      })
    }
    return out
  }, [rows, query, status, extra, sort, columns, statusOf, searchText, extraFilter])

  const pages = Math.max(1, Math.ceil(filtered.length / pageSize))
  const current = Math.min(page, pages)
  const visible = filtered.slice((current - 1) * pageSize, current * pageSize)

  const toggleSort = (key: string) => {
    setSort((s) => (s.key === key ? { key, dir: s.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: 'asc' }))
    setPage(1)
  }
  const pickStatus = (value: string) => {
    setStatus((s) => (s === value ? '' : value))
    setPage(1)
  }

  return (
    <div className="space-y-5">
      {/* KPIs */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {kpis.map((k) => (
          <KpiCard
            key={k.key}
            label={k.label}
            value={loading ? <span className="skeleton inline-block h-6 w-10 align-middle" /> : k.value}
            hint={k.hint}
            icon={k.icon}
            accent={k.accent}
            active={!!k.status && status === k.status}
            onClick={k.status !== undefined ? () => pickStatus(k.status!) : undefined}
          />
        ))}
      </div>

      <Card className="overflow-hidden">
        {/* Toolbar */}
        <div className="flex flex-wrap items-center gap-2 border-b border-line p-3">
          <div className="relative min-w-[220px] flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-subtle" />
            <input
              value={query}
              onChange={(e) => { setQuery(e.target.value); setPage(1) }}
              placeholder={searchPlaceholder}
              className="input pl-9"
            />
            {query && (
              <button onClick={() => setQuery('')} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-ink-subtle hover:text-ink">
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
          {extraFilter && (
            <select
              value={extra}
              onChange={(e) => { setExtra(e.target.value); setPage(1) }}
              className="input w-auto"
              aria-label={extraFilter.label}
            >
              <option value="">{extraFilter.label}</option>
              {extraFilter.options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          )}
          <Button icon={<RefreshCw className={cn('h-4 w-4', loading && 'animate-spin')} />} onClick={onRetry}>
            {t('common.refresh')}
          </Button>
        </div>
        <div className="flex flex-wrap gap-1.5 border-b border-line px-3 py-2">
          <button onClick={() => pickStatus('')} className={cn('chip', !status && 'border-brand-500/40 bg-brand-500/10 text-brand-700 dark:text-brand-300')}>
            {t('ui.all')} <span className="text-ink-subtle">{rows.length}</span>
          </button>
          {statusOptions.map((o) => {
            const count = rows.filter((r) => statusOf(r) === o.value).length
            if (!count) return null
            return (
              <button
                key={o.value}
                onClick={() => pickStatus(o.value)}
                className={cn('chip', status === o.value && 'border-brand-500/40 bg-brand-500/10 text-brand-700 dark:text-brand-300')}
              >
                {o.label} <span className="text-ink-subtle">{count}</span>
              </button>
            )
          })}
        </div>

        {error ? (
          <div className="p-4"><ErrorBanner onRetry={onRetry} retryLabel={t('ui.retry')}>{error}</ErrorBanner></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-surface-muted/60">
                <tr>
                  {columns.map((c) => (
                    <th key={c.key} className={cn('whitespace-nowrap px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-ink-subtle', c.className)}>
                      {c.sortValue ? (
                        <button onClick={() => toggleSort(c.key)} className="inline-flex items-center gap-1 hover:text-ink">
                          {c.header}
                          {sort.key === c.key
                            ? (sort.dir === 'asc' ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />)
                            : <ChevronsUpDown className="h-3 w-3 opacity-40" />}
                        </button>
                      ) : c.header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {loading
                  ? Array.from({ length: 6 }).map((_, i) => (
                    <tr key={i}>
                      {columns.map((c) => <td key={c.key} className="px-4 py-3.5"><div className="skeleton h-3.5 w-3/4" /></td>)}
                    </tr>
                  ))
                  : visible.map((row) => (
                    <tr
                      key={rowKey(row)}
                      onClick={() => onRowClick(row)}
                      className="cursor-pointer transition-colors hover:bg-surface-muted/70"
                    >
                      {columns.map((c) => (
                        <td key={c.key} className={cn('px-4 py-3 align-middle text-ink', c.className)}>{c.cell(row)}</td>
                      ))}
                    </tr>
                  ))}
              </tbody>
            </table>
            {!loading && filtered.length === 0 && (
              <EmptyState title={t('ui.noResults')} description={t('ui.adjustFilters')} />
            )}
          </div>
        )}

        {/* Pagination */}
        {!loading && filtered.length > pageSize && (
          <div className="flex items-center justify-between border-t border-line px-4 py-2.5 text-xs text-ink-muted">
            <span>
              {(current - 1) * pageSize + 1}–{Math.min(current * pageSize, filtered.length)} {t('common.of')} {filtered.length}
            </span>
            <div className="flex items-center gap-1">
              <Button size="xs" variant="ghost" icon={<ChevronLeft className="h-3.5 w-3.5" />} disabled={current <= 1} onClick={() => setPage(current - 1)}>
                {t('common.previous')}
              </Button>
              <span className="px-2 tabular-nums">{current} / {pages}</span>
              <Button size="xs" variant="ghost" disabled={current >= pages} onClick={() => setPage(current + 1)}>
                {t('common.next')} <ChevronRight className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  )
}
