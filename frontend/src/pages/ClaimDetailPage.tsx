import { Link, useParams } from 'react-router-dom'
import { ChevronLeft, ShieldCheck } from 'lucide-react'
import { AgentLogs } from '../components/business/AgentLogs'
import { EntityHero } from '../components/business/EntityHero'
import { PdfViewer } from '../components/business/PdfViewer'
import { PiiDetections } from '../components/business/PiiDetections'
import { ProcessButton } from '../components/business/ProcessButton'
import { StepsTimeline } from '../components/business/StepsTimeline'
import ClaimDecision from '../components/claim/ClaimDecision'
import StepOutputDisplay from '../components/claim/StepOutputDisplay'
import ReviewChatPanel from '../components/ReviewChatPanel'
import { Badge } from '../components/ui/Badge'
import { Card } from '../components/ui/Card'
import { ErrorBanner, PageLoader } from '../components/ui/Feedback'
import { useClaimData } from '../hooks/useDomainData'
import { useTranslation } from '../i18n/LanguageContext'
import { formatDateTime, formatDuration } from '../lib/format'
import { claimsApi } from '../services/api'

export default function ClaimDetailPage() {
  const { claimId } = useParams<{ claimId: string }>()
  const { t, locale } = useTranslation()
  const { data, loading, error, reload } = useClaimData(claimId)

  if (loading) return <PageLoader />
  if (error || !data) {
    return (
      <div className="space-y-3">
        <ErrorBanner onRetry={reload} retryLabel={t('ui.retry')}>{error || t('claims.claimNotFound')}</ErrorBanner>
        <Link to="/claims" className="text-sm text-brand-600">{t('claims.backToClaims')}</Link>
      </div>
    )
  }

  const { claim, status, decision, logs, detections } = data
  const processing = claim.status === 'processing'
  const steps = status?.processing_steps?.length ? status.processing_steps : logs
  const ocr = logs.find((s) => s.step_name === 'ocr' || s.step_name === 'ocr_document')?.output_data?.structured_data?.fields
  const description = (locale === 'en' && claim.metadata?.description_en) || claim.metadata?.description

  return (
    <div className="space-y-5">
      <Link to="/claims" className="inline-flex items-center gap-1 text-xs font-medium text-ink-muted hover:text-ink">
        <ChevronLeft className="h-3.5 w-3.5" /> {t('claims.backToClaims')}
      </Link>

      <EntityHero
        number={claim.claim_number}
        status={claim.status}
        icon={<ShieldCheck className="h-6 w-6" />}
        iconClass="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
        kind={claim.claim_type && <Badge tone="info">{claim.claim_type}</Badge>}
        title={ocr?.diagnosis?.value || ocr?.service?.value}
        description={description}
        fields={[
          { label: t('claims.claimant'), value: claim.user_name || claim.user_id },
          { label: t('claims.submittedAt'), value: formatDateTime(claim.submitted_at, locale) },
          { label: t('claims.processed'), value: formatDateTime(claim.processed_at, locale) },
          { label: t('claims.duration'), value: formatDuration(claim.total_processing_time_ms) },
        ]}
        actions={['pending', 'failed', 'processing'].includes(claim.status) && (
          <ProcessButton onProcess={() => claimsApi.process(claim.id)} onStarted={reload} />
        )}
      />

      <div className="grid gap-5 xl:grid-cols-5">
        <div className="space-y-5 xl:col-span-3">
          {decision && <ClaimDecision claim={claim} decision={decision} />}
          <StepsTimeline
            steps={steps}
            processing={processing}
            progress={status?.progress_percentage}
            renderOutput={(step) => <StepOutputDisplay stepName={step.step_name} outputData={step.output_data} />}
          />
          <PiiDetections detections={detections} />
          <AgentLogs logs={claim.agent_logs ?? []} />
          {claim.status === 'manual_review' && (
            <Card className="legacy p-5">
              <ReviewChatPanel
                entityId={claim.id}
                entityType="claim"
                reviewerId="reviewer"
                reviewerName="Review Agent"
                onActionSubmitted={() => reload()}
              />
            </Card>
          )}
        </div>
        <div className="xl:col-span-2">
          <div className="xl:sticky xl:top-4">
            <PdfViewer fileName={`${claim.claim_number}.pdf`} urlFor={(lang) => claimsApi.documentUrl(claim.id, lang)} />
          </div>
        </div>
      </div>
    </div>
  )
}
