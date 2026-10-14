import { useCallback, useEffect, useState } from 'react'
import { Download, ExternalLink, FileText, FileX, Maximize2, Minimize2 } from 'lucide-react'
import { useTranslation } from '../../i18n/LanguageContext'
import { cn } from '../../lib/cn'
import { Button, IconButton } from '../ui/Button'
import { Card } from '../ui/Card'
import { EmptyState } from '../ui/Feedback'

interface PdfViewerProps {
  /** builds the document URL for a language */
  urlFor: (lang: 'fr' | 'en') => string
  fileName: string
  className?: string
}

type State = { status: 'loading' } | { status: 'ready'; blobUrl: string } | { status: 'error'; message: string }

/**
 * Embedded PDF with FR/EN switch, open-in-tab and download. The document is fetched
 * first (blob URL) so a missing file shows a clean message instead of the API error JSON.
 */
export function PdfViewer({ urlFor, fileName, className }: PdfViewerProps) {
  const { t, locale } = useTranslation()
  const [lang, setLang] = useState<'fr' | 'en'>(locale)
  const [tall, setTall] = useState(false)
  const [state, setState] = useState<State>({ status: 'loading' })
  const [attempt, setAttempt] = useState(0)
  const url = urlFor(lang)

  useEffect(() => setLang(locale), [locale])

  useEffect(() => {
    let blobUrl: string | null = null
    let cancelled = false
    setState({ status: 'loading' })
    fetch(url)
      .then(async (res) => {
        const type = res.headers.get('content-type') || ''
        if (!res.ok || !type.includes('pdf')) {
          let detail = `HTTP ${res.status}`
          try { detail = (await res.json()).detail || detail } catch { /* not JSON */ }
          throw new Error(detail)
        }
        const blob = await res.blob()
        if (cancelled) return
        blobUrl = URL.createObjectURL(blob)
        setState({ status: 'ready', blobUrl })
      })
      .catch((err: Error) => !cancelled && setState({ status: 'error', message: err.message }))
    return () => {
      cancelled = true
      if (blobUrl) URL.revokeObjectURL(blobUrl)
    }
  }, [url, attempt])

  const retry = useCallback(() => setAttempt((a) => a + 1), [])

  return (
    <Card className={cn('flex flex-col overflow-hidden', className)}>
      <div className="flex items-center justify-between gap-2 border-b border-line px-3 py-2">
        <div className="flex min-w-0 items-center gap-2">
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-red-500/10 text-red-600 dark:text-red-400">
            <FileText className="h-4 w-4" />
          </div>
          <span className="truncate text-xs font-medium text-ink">{fileName}</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="flex rounded-lg border border-line bg-surface-muted p-0.5">
            {(['fr', 'en'] as const).map((l) => (
              <button
                key={l}
                onClick={() => setLang(l)}
                className={cn(
                  'rounded-md px-1.5 py-0.5 text-[10px] font-semibold uppercase',
                  lang === l ? 'bg-surface text-ink shadow-sm' : 'text-ink-subtle hover:text-ink',
                )}
              >
                {l}
              </button>
            ))}
          </div>
          <IconButton label={tall ? t('pdf.shrink') : t('pdf.expand')} icon={tall ? <Minimize2 className="h-3.5 w-3.5" /> : <Maximize2 className="h-3.5 w-3.5" />} onClick={() => setTall(!tall)} />
          <a href={url} target="_blank" rel="noopener noreferrer" title={t('pdf.open')} className="flex h-8 w-8 items-center justify-center rounded-lg text-ink-muted hover:bg-surface-muted hover:text-ink">
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
          {state.status === 'ready' && (
            <a href={state.blobUrl} download={fileName} title={t('pdf.download')} className="flex h-8 w-8 items-center justify-center rounded-lg text-ink-muted hover:bg-surface-muted hover:text-ink">
              <Download className="h-3.5 w-3.5" />
            </a>
          )}
        </div>
      </div>
      <div className={cn('relative bg-surface-sunken', tall ? 'h-[85vh]' : 'h-[640px]')}>
        {state.status === 'loading' && (
          <div className="absolute inset-0 flex flex-col gap-3 p-6">
            <div className="skeleton h-5 w-2/3" />
            <div className="skeleton h-3 w-full" />
            <div className="skeleton h-3 w-5/6" />
            <div className="skeleton h-3 w-4/6" />
            <div className="skeleton mt-4 h-40 w-full" />
          </div>
        )}
        {state.status === 'error' && (
          <EmptyState
            className="h-full"
            icon={<FileX className="h-5 w-5" />}
            title={t('pdf.unavailable')}
            description={`${t('pdf.unavailableHelp')} (${state.message})`}
            action={<Button size="sm" onClick={retry}>{t('ui.retry')}</Button>}
          />
        )}
        {state.status === 'ready' && <iframe src={state.blobUrl} title={fileName} className="h-full w-full" />}
      </div>
    </Card>
  )
}
