import { Link, useParams } from 'react-router-dom'
import { Building2, ChevronLeft } from 'lucide-react'
import { AgentLogs } from '../components/business/AgentLogs'
import { EntityHero } from '../components/business/EntityHero'
import { PdfViewer } from '../components/business/PdfViewer'
import { ProcessButton } from '../components/business/ProcessButton'
import ReviewChatPanel from '../components/ReviewChatPanel'
import TenderDecision from '../components/tender/TenderDecision'
import TenderProcessingSteps from '../components/tender/TenderProcessingSteps'
import { Badge } from '../components/ui/Badge'
import { Card } from '../components/ui/Card'
import { ErrorBanner, PageLoader } from '../components/ui/Feedback'
import { useTenderData } from '../hooks/useDomainData'
import { useTranslation } from '../i18n/LanguageContext'
import { formatDateTime, formatMoney } from '../lib/format'
import { tendersApi } from '../services/api'

export default function TenderDetailPage() {
  const { tenderId } = useParams<{ tenderId: string }>()
  const { t, locale } = useTranslation()
  const { data, loading, error, reload } = useTenderData(tenderId)

  if (loading) return <PageLoader />
  if (error || !data) {
    return (
      <div className="space-y-3">
        <ErrorBanner onRetry={reload} retryLabel={t('ui.retry')}>{error || t('tenders.tenderNotFound')}</ErrorBanner>
        <Link to="/tenders" className="text-sm text-brand-600">{t('tenders.backToTenders')}</Link>
      </div>
    )
  }

  const { tender, status, decision, logs } = data
  const m = (tender.metadata || {}) as Record<string, any>
  const lots: string[] = m.lots || []
  const requirements: string[] = m.exigences_specifiques || []
  const criteria: Record<string, number> | undefined = m.criteres_attribution
  const delay = m.delai_execution_mois || tender.delai_execution

  return (
    <div className="space-y-5">
      <Link to="/tenders" className="inline-flex items-center gap-1 text-xs font-medium text-ink-muted hover:text-ink">
        <ChevronLeft className="h-3.5 w-3.5" /> {t('tenders.backToTenders')}
      </Link>

      <EntityHero
        number={tender.tender_number}
        status={tender.status}
        icon={<Building2 className="h-6 w-6" />}
        iconClass="bg-amber-500/10 text-amber-600 dark:text-amber-400"
        kind={(m.nature_travaux || tender.tender_type) && <Badge tone="warning">{m.nature_travaux || tender.tender_type}</Badge>}
        title={m.titre || tender.objet_marche}
        description={(locale === 'en' && m.description_en) || m.description}
        fields={[
          { label: t('tenders.maitreOuvrage'), value: m.maitre_ouvrage || tender.maitre_ouvrage || '—' },
          { label: t('tenders.estimatedAmount'), value: formatMoney(m.montant_estime ?? tender.montant_estime, locale) },
          { label: t('tenders.region'), value: [m.region, m.commune].filter(Boolean).join(' · ') || '—' },
          { label: t('tenders.submissionDeadline'), value: m.date_limite_remise || tender.date_limite_reponse || '—' },
          { label: t('tenders.executionDelay'), value: delay ? `${delay} ${t('tenders.months')}` : '—' },
          { label: t('tenders.maitreOeuvre'), value: m.maitre_oeuvre || '—' },
          { label: t('tenders.submittedOn'), value: formatDateTime(tender.submitted_at, locale) },
          { label: t('tenders.processedIn'), value: tender.total_processing_time_ms ? `${(tender.total_processing_time_ms / 1000).toFixed(1)} s` : '—' },
        ]}
        actions={(tender.status === 'pending' || tender.status === 'failed') && (
          <ProcessButton onProcess={() => tendersApi.process(tender.id)} onStarted={reload} />
        )}
      >
        {(criteria || lots.length > 0 || requirements.length > 0) && (
          <div className="space-y-3 border-t border-line px-5 py-4">
            {criteria && (
              <div>
                <p className="label mb-1.5">{t('tenders.awardCriteria')}</p>
                <div className="flex flex-wrap gap-1.5">
                  {Object.entries(criteria).map(([k, v]) => <Badge key={k} tone="info">{k} · {String(v)}%</Badge>)}
                </div>
              </div>
            )}
            {lots.length > 0 && (
              <div>
                <p className="label mb-1.5">{t('tenders.lots')}</p>
                <div className="flex flex-wrap gap-1.5">{lots.map((l) => <span key={l} className="chip">{l}</span>)}</div>
              </div>
            )}
            {requirements.length > 0 && (
              <div>
                <p className="label mb-1.5">{t('tenders.specificRequirements')}</p>
                <div className="flex flex-wrap gap-1.5">{requirements.map((r) => <Badge key={r} tone="danger">{r}</Badge>)}</div>
              </div>
            )}
          </div>
        )}
      </EntityHero>

      <div className="grid gap-5 xl:grid-cols-5">
        <div className="space-y-5 xl:col-span-3">
          {decision && <TenderDecision tender={tender} decision={decision} />}
          <TenderProcessingSteps tender={tender} status={status} logs={logs} />
          <AgentLogs logs={tender.agent_logs ?? []} />
          {tender.status === 'manual_review' && (
            <Card className="legacy p-5">
              <ReviewChatPanel
                entityId={tender.id}
                entityType="tender"
                reviewerId="reviewer"
                reviewerName="Review Agent"
                onActionSubmitted={() => reload()}
              />
            </Card>
          )}
        </div>
        <div className="xl:col-span-2">
          <div className="xl:sticky xl:top-4">
            <PdfViewer fileName={`${tender.tender_number}.pdf`} urlFor={(lang) => tendersApi.documentUrl(tender.id, lang)} />
          </div>
        </div>
      </div>
    </div>
  )
}
