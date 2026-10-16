import { useNavigate } from 'react-router-dom'
import { Inbox, UserCheck } from 'lucide-react'
import { Badge } from '../components/ui/Badge'
import { Card } from '../components/ui/Card'
import { EmptyState, ErrorBanner, PageLoader } from '../components/ui/Feedback'
import { PageHeader } from '../components/ui/PageHeader'
import { DOMAINS } from '../domains'
import { useResource } from '../hooks/useResource'
import { useTranslation } from '../i18n/LanguageContext'
import { formatDateTime } from '../lib/format'
import { reviewApi } from '../services/api'

/** The cases the agents handed over to a person, in the domains of the user's profile, the oldest first. */
export default function ReviewInboxPage() {
  const { t, locale } = useTranslation()
  const navigate = useNavigate()
  const { data, loading, error, reload } = useResource(() => reviewApi.inbox(), [])

  return (
    <>
      <PageHeader icon={<UserCheck className="h-5 w-5 text-violet-500" />} title={t('review.inboxTitle')} subtitle={t('review.inboxSubtitle')} />
      {error && <ErrorBanner onRetry={reload} retryLabel={t('ui.retry')}>{error}</ErrorBanner>}
      {loading ? <PageLoader /> : !data?.length ? (
        <EmptyState icon={<Inbox className="h-5 w-5" />} title={t('review.inboxEmpty')} className="py-24" />
      ) : (
        <Card className="divide-y divide-line">
          {data.map((item) => {
            const ui = DOMAINS[item.domain]
            const Icon = ui.icon
            return (
              <button key={item.id} type="button" onClick={() => navigate(`${ui.path}/${item.id}`)}
                className="flex w-full items-center gap-4 px-5 py-4 text-left hover:bg-surface-muted/60">
                <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${ui.iconClass}`}><Icon className="h-5 w-5" /></div>
                <div className="min-w-0 flex-1">
                  <p className="font-mono text-sm font-semibold text-ink">{item.number}</p>
                  <p className="truncate text-sm text-ink-muted">{item.reason || '—'}</p>
                </div>
                <div className="hidden shrink-0 items-center gap-3 md:flex">
                  {item.suggestion && (
                    <span className="text-xs text-ink-subtle">
                      {t('review.agentLeans')} <Badge tone={ui.decisionTones[item.suggestion] ?? 'neutral'}>{t(`decision.${item.suggestion}`, item.suggestion)}</Badge>
                    </span>
                  )}
                  {item.confidence != null && <span className="font-mono text-xs text-ink-subtle">{Math.round(item.confidence * 100)}%</span>}
                  <span className="text-xs text-ink-subtle">{formatDateTime(item.waiting_since, locale)}</span>
                </div>
              </button>
            )
          })}
        </Card>
      )}
    </>
  )
}
