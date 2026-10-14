import { Link, useParams } from 'react-router-dom'
import { ChevronLeft, Package } from 'lucide-react'
import { AgentLogs } from '../components/business/AgentLogs'
import { DecisionCard } from '../components/business/DecisionCard'
import { EntityHero } from '../components/business/EntityHero'
import { PdfViewer } from '../components/business/PdfViewer'
import { ProcessButton } from '../components/business/ProcessButton'
import { StepsTimeline } from '../components/business/StepsTimeline'
import { TrackingTimeline } from '../components/business/TrackingTimeline'
import { Badge, type Tone } from '../components/ui/Badge'
import { ErrorBanner, PageLoader } from '../components/ui/Feedback'
import { useReclamationData } from '../hooks/useDomainData'
import { useTranslation } from '../i18n/LanguageContext'
import { formatDateTime, formatMoney } from '../lib/format'
import { postalApi } from '../services/api'

const DECISION_TONES: Record<string, Tone> = { rembourser: 'success', reexpedier: 'info', rejeter: 'danger', escalader: 'orange' }

export default function PostalDetailPage() {
  const { reclamationId } = useParams<{ reclamationId: string }>()
  const { t, locale } = useTranslation()
  const { data, loading, error, reload } = useReclamationData(reclamationId)

  if (loading) return <PageLoader />
  if (error || !data) {
    return (
      <div className="space-y-3">
        <ErrorBanner onRetry={reload} retryLabel={t('ui.retry')}>{error || t('postal.reclamationNotFound')}</ErrorBanner>
        <Link to="/postal" className="text-sm text-brand-600">{t('postal.backToPostal')}</Link>
      </div>
    )
  }

  const { reclamation: r, status, decision, logs, tracking } = data
  const steps = status?.processing_steps?.length ? status.processing_steps : logs
  const verdict = decision?.initial_decision || decision?.decision

  return (
    <div className="space-y-5">
      <Link to="/postal" className="inline-flex items-center gap-1 text-xs font-medium text-ink-muted hover:text-ink">
        <ChevronLeft className="h-3.5 w-3.5" /> {t('postal.backToPostal')}
      </Link>

      <EntityHero
        number={r.reclamation_number}
        status={r.status}
        icon={<Package className="h-6 w-6" />}
        iconClass="bg-rose-500/10 text-rose-600 dark:text-rose-400"
        kind={<Badge tone="orange">{t(`postal.type_${r.reclamation_type}`)}</Badge>}
        description={(locale === 'en' && r.metadata?.description_en) || r.description}
        fields={[
          { label: t('postal.clientName'), value: r.client_nom },
          { label: t('postal.clientEmail'), value: r.client_email },
          { label: t('postal.trackingNumber'), value: <span className="font-mono">{r.numero_suivi}</span> },
          { label: t('postal.declaredValue'), value: formatMoney(r.valeur_declaree, locale, 2) },
          { label: t('postal.clientPhone'), value: r.client_telephone || '—' },
          { label: t('postal.submittedOn'), value: formatDateTime(r.submitted_at, locale) },
          { label: t('postal.processedIn'), value: r.total_processing_time_ms ? `${(r.total_processing_time_ms / 1000).toFixed(1)} s` : '—' },
        ]}
        actions={['pending', 'rejected', 'processing'].includes(r.status) && (
          <ProcessButton onProcess={() => postalApi.process(r.id)} onStarted={reload} />
        )}
      />

      <div className="grid gap-5 xl:grid-cols-5">
        <div className="space-y-5 xl:col-span-3">
          {decision && verdict && (
            <DecisionCard
              label={t(`postal.decision_${verdict}`)}
              tone={DECISION_TONES[verdict] ?? 'neutral'}
              confidence={decision.initial_confidence ?? decision.confidence}
              reasoning={(locale === 'en' && decision.metadata?.reasoning_en) || decision.initial_reasoning || decision.reasoning}
              manualReview={decision.requires_manual_review}
              model={decision.llm_model}
            />
          )}
          <StepsTimeline
            steps={steps}
            processing={r.status === 'processing'}
            progress={status?.progress_percentage}
            renderOutput={(step) => (
              <details className="mt-2 rounded-lg border border-line bg-surface-muted p-2.5">
                <summary className="cursor-pointer text-xs font-medium text-ink-muted">{t('postal.viewData')}</summary>
                <pre className="mt-2 max-h-56 overflow-auto text-[11px] text-ink-muted">{JSON.stringify(step.output_data, null, 2)}</pre>
              </details>
            )}
          />
          <TrackingTimeline events={tracking} />
          <AgentLogs logs={r.agent_logs ?? []} />
        </div>
        <div className="xl:col-span-2">
          {r.document_path && (
            <div className="xl:sticky xl:top-4">
              <PdfViewer fileName={`${r.reclamation_number}.pdf`} urlFor={(lang) => postalApi.documentUrl(r.id, lang)} />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
