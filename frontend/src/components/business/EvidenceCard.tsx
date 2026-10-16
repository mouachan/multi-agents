import { ClipboardList } from 'lucide-react'
import { useTranslation } from '../../i18n/LanguageContext'
import { formatMoney } from '../../lib/format'
import type { EvidenceSection, Fact } from '../../types/case'
import { Badge } from '../ui/Badge'
import { Card, CardHeader } from '../ui/Card'

/** Value of a fact: yes/no, amounts with their currency, the rest as is */
function FactValue({ fact }: { fact: Fact }) {
  const { t, locale } = useTranslation()
  if (typeof fact.value === 'boolean') {
    return <Badge tone={fact.value ? 'success' : 'danger'}>{t(fact.value ? 'ui.yes' : 'ui.no')}</Badge>
  }
  if (typeof fact.value === 'number' && ['EUR', 'USD'].includes(fact.unit || '')) {
    return <span className="tabular-nums">{formatMoney(fact.value, locale, 2, fact.unit)}</span>
  }
  return <span>{String(fact.value)}{fact.unit && fact.unit !== 'EUR' && fact.unit !== 'USD' ? ` ${fact.unit}` : ''}</span>
}

/**
 * The facts of the last processing, taken from the agent's tool outputs without any LLM
 * (backend: the domain's evidence()) — what the decision relies on, checkable by a person.
 */
export function EvidenceCard({ sections }: { sections: EvidenceSection[] }) {
  const { t } = useTranslation()
  const shown = sections.filter((s) => s.facts.length || s.items.length)
  if (!shown.length) return null
  return (
    <Card>
      <CardHeader icon={<ClipboardList className="h-4 w-4" />} title={t('evidence.title')} subtitle={t('evidence.subtitle')} />
      <div className="space-y-5 p-5">
        {shown.map((section) => (
          <section key={section.key}>
            <p className="label mb-2">{t(`evidence.${section.key}`)}</p>
            {section.facts.length > 0 && (
              <dl className="grid grid-cols-2 gap-x-6 gap-y-2 md:grid-cols-3">
                {section.facts.map((fact) => (
                  <div key={fact.key} className="min-w-0">
                    <dt className="text-[11px] text-ink-subtle">{t(`evidence.fact_${fact.key}`)}</dt>
                    <dd className="truncate text-sm font-medium text-ink"><FactValue fact={fact} /></dd>
                  </div>
                ))}
              </dl>
            )}
            {section.items.length > 0 && (
              <ul className="mt-2 divide-y divide-line rounded-xl border border-line">
                {section.items.map((item, i) => (
                  <li key={i} className="flex items-center justify-between gap-3 px-3 py-2">
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-ink">{item.title}</p>
                      {item.detail && <p className="truncate text-xs text-ink-subtle">{item.detail}</p>}
                    </div>
                    <div className="flex shrink-0 items-center gap-2">
                      {item.badge && <Badge>{t(`decision.${item.badge}`, item.badge)}</Badge>}
                      {item.score != null && <span className="font-mono text-[11px] text-ink-subtle">{item.score.toFixed(2)}</span>}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        ))}
      </div>
    </Card>
  )
}
