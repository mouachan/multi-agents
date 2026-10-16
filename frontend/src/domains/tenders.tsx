import { Building2 } from 'lucide-react'
import { Badge } from '../components/ui/Badge'
import { StatusBadge } from '../components/ui/StatusBadge'
import { formatDateTime, formatDuration, formatMoney, numericKey } from '../lib/format'
import type { Case } from '../types/case'
import type { DomainUI } from './types'

/** A tender's details are in its metadata (title, budget, region...), set by the seed and data-init */
const meta = (c: Case): Record<string, any> => c.metadata || {}

export const tenders: DomainUI = {
  name: 'tenders',
  path: '/tenders',
  i18n: 'tenders',
  icon: Building2,
  iconClass: 'bg-amber-500/10 text-amber-600 dark:text-amber-400',
  agentId: 'tenders',
  statuses: ['pending', 'processing', 'completed', 'manual_review', 'declined', 'failed'],
  reviewStatus: 'manual_review',
  decisionTones: { go: 'success', no_go: 'danger', a_approfondir: 'warning' },

  columns: (t, locale) => [
    { key: 'number', header: t('tenders.tenderNumber'), sortValue: (c) => numericKey(c.number), cell: (c) => <span className="font-mono text-xs font-semibold">{c.number}</span> },
    { key: 'title', header: t('tenders.objectMarche'), sortValue: (c) => meta(c).titre || '', cell: (c) => (
      <div className="min-w-0">
        <p className="max-w-[420px] truncate font-medium">{meta(c).titre || '—'}</p>
        <p className="max-w-[420px] truncate text-xs text-ink-subtle">{meta(c).maitre_ouvrage || c.entity_id}</p>
      </div>
    ) },
    { key: 'region', header: t('tenders.region'), sortValue: (c) => meta(c).region || '', cell: (c) => (
      <span className="text-ink-muted">{[meta(c).region, meta(c).commune].filter(Boolean).join(' · ') || '—'}</span>
    ) },
    { key: 'amount', header: t('tenders.estimatedAmount'), className: 'text-right', sortValue: (c) => meta(c).montant_estime ?? -1, cell: (c) => (
      <span className="font-medium tabular-nums">{formatMoney(meta(c).montant_estime, locale)}</span>
    ) },
    { key: 'status', header: t('case.status'), sortValue: (c) => c.status, cell: (c) => <StatusBadge status={c.status} /> },
    { key: 'deadline', header: t('tenders.submissionDeadline'), sortValue: (c) => meta(c).date_limite_remise || '', cell: (c) => (
      <span className="text-ink-muted">{meta(c).date_limite_remise || '—'}</span>
    ) },
  ],
  searchText: (c) => [c.number, c.entity_id, meta(c).titre, meta(c).maitre_ouvrage, meta(c).region, meta(c).commune].join(' '),
  extraFilter: (cases, t) => ({
    label: t('ui.allRegions'),
    options: Array.from(new Set(cases.map((c) => meta(c).region).filter(Boolean))).sort().map((v) => ({ value: v, label: v })),
    apply: (c, v) => meta(c).region === v,
  }),

  hero: (c, t, locale) => {
    const m = meta(c)
    const lots: string[] = m.lots || []
    const requirements: string[] = m.exigences_specifiques || []
    const criteria: Record<string, number> | undefined = m.criteres_attribution
    return {
      kind: (m.nature_travaux || c.tender_type) && <Badge tone="warning">{m.nature_travaux || c.tender_type}</Badge>,
      title: m.titre,
      description: (locale === 'en' && m.description_en) || m.description,
      fields: [
        { label: t('tenders.maitreOuvrage'), value: m.maitre_ouvrage || '—' },
        { label: t('tenders.estimatedAmount'), value: formatMoney(m.montant_estime, locale) },
        { label: t('tenders.region'), value: [m.region, m.commune].filter(Boolean).join(' · ') || '—' },
        { label: t('tenders.submissionDeadline'), value: m.date_limite_remise || '—' },
        { label: t('tenders.executionDelay'), value: m.delai_execution_mois ? `${m.delai_execution_mois} ${t('tenders.months')}` : '—' },
        { label: t('tenders.maitreOeuvre'), value: m.maitre_oeuvre || '—' },
        { label: t('case.submittedAt'), value: formatDateTime(c.submitted_at, locale) },
        { label: t('case.duration'), value: formatDuration(c.total_processing_time_ms) },
      ],
      extra: (criteria || lots.length > 0 || requirements.length > 0) && (
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
      ),
    }
  },
}
