import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ChevronLeft, ExternalLink, UserCheck } from 'lucide-react'
import { DecisionCard } from '../components/business/DecisionCard'
import { EntityHero } from '../components/business/EntityHero'
import { EvidenceCard } from '../components/business/EvidenceCard'
import { PdfViewer } from '../components/business/PdfViewer'
import { ProcessButton } from '../components/business/ProcessButton'
import { StepOutput } from '../components/business/StepOutput'
import { StepsTimeline } from '../components/business/StepsTimeline'
import { ReviewPanel } from '../components/review/ReviewPanel'
import { Button } from '../components/ui/Button'
import { ErrorBanner, PageLoader } from '../components/ui/Feedback'
import { domainUI } from '../domains'
import { useCase } from '../hooks/useCase'
import { useTranslation } from '../i18n/LanguageContext'
import { casesApi } from '../services/api'
import type { Domain } from '../types/case'

const PROCESSABLE = ['pending', 'failed', 'processing']   // "processing" with no job running: a restart

/**
 * One case: its header (src/domains/<domain>.tsx), its decision, the human review when the agent hands it
 * over, the facts of the processing, the processing steps, the cards of its domain, and its document.
 */
export default function CaseDetailPage({ domain }: { domain: Domain }) {
  const ui = domainUI(domain)
  const { id } = useParams<{ id: string }>()
  const { t, locale } = useTranslation()
  const { data, loading, error, reload } = useCase(domain, id)
  const [reviewOpen, setReviewOpen] = useState(false)

  if (loading) return <PageLoader />
  if (error || !data) {
    return (
      <div className="space-y-3">
        <ErrorBanner onRetry={reload} retryLabel={t('ui.retry')}>{error || t('case.notFound')}</ErrorBanner>
        <Link to={ui.path} className="text-sm text-brand-600">{t('case.back')}</Link>
      </div>
    )
  }

  const { case: c, decision } = data
  const hero = ui.hero(c, t, locale)
  const Icon = ui.icon
  const Extras = ui.Extras
  const showReview = !!decision && (c.status === ui.reviewStatus || !!decision.reviewer || reviewOpen)

  return (
    <div className="space-y-5">
      <Link to={ui.path} className="inline-flex items-center gap-1 text-xs font-medium text-ink-muted hover:text-ink">
        <ChevronLeft className="h-3.5 w-3.5" /> {t('case.back')}
      </Link>

      <EntityHero
        number={c.number}
        status={c.status}
        icon={<Icon className="h-6 w-6" />}
        iconClass={ui.iconClass}
        kind={hero.kind}
        title={hero.title}
        description={hero.description}
        fields={hero.fields}
        actions={PROCESSABLE.includes(c.status) && <ProcessButton onProcess={() => casesApi(domain).process(c.id)} onStarted={reload} />}
      >
        {hero.extra}
      </EntityHero>

      <div className="grid gap-5 xl:grid-cols-5">
        <div className="space-y-5 xl:col-span-3">
          {showReview && <ReviewPanel ui={ui} caseId={c.id} onDecided={reload} />}
          {decision && (
            <DecisionCard
              label={t(`decision.${decision.agent.decision}`, decision.agent.decision)}
              tone={ui.decisionTones[decision.agent.decision] ?? 'neutral'}
              confidence={decision.agent.confidence}
              reasoning={(locale === 'en' && decision.reasoning_en) || decision.agent.reasoning}
              manualReview={decision.requires_manual_review}
              model={decision.llm_model}
              extra={!showReview && (
                <Button variant="ghost" size="sm" icon={<UserCheck className="h-4 w-4" />} onClick={() => setReviewOpen(true)}>
                  {t('review.reviewThisDecision')}
                </Button>
              )}
            />
          )}
          <EvidenceCard sections={c.evidence} />
          <StepsTimeline steps={c.processing_steps} processing={c.status === 'processing'} renderOutput={(step) => <StepOutput step={step} />} />
          {Extras && <Extras case={c} />}
          {c.trace?.mlflow_url && (
            <a href={c.trace.mlflow_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs font-medium text-brand-600">
              {t('case.mlflowTrace')} <ExternalLink className="h-3 w-3" />
            </a>
          )}
        </div>
        <div className="xl:col-span-2">
          <div className="xl:sticky xl:top-4">
            <PdfViewer fileName={`${c.number}.pdf`} urlFor={(lang) => casesApi(domain).documentUrl(c.id, lang)} />
          </div>
        </div>
      </div>
    </div>
  )
}
