import { Fragment, type ReactNode } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Lock } from 'lucide-react'
import { cn } from '../../lib/cn'
import { useTranslation } from '../../i18n/LanguageContext'

// ---------------------------------------------------------------------------
// PII placeholders written by NeMo Guardrails: [IBAN_CODE], [EMAIL_ADDRESS]...
// (older agents used <IBAN_CODE>, which react-markdown would drop as raw HTML)
// ---------------------------------------------------------------------------
const PII_BRACKET = /\[([A-Z][A-Z0-9_]{2,})\](?!\()/g
const PII_ANGLE = /<([A-Z][A-Z0-9_]{2,})>/g
const PII_ANY = /\[([A-Z][A-Z0-9_]{2,})\](?!\()|<([A-Z][A-Z0-9_]{2,})>/g
const PII_CODE_PREFIX = 'pii:'

const PII_LABELS: Record<string, { fr: string; en: string }> = {
  PERSON: { fr: 'Personne', en: 'Person' },
  EMAIL_ADDRESS: { fr: 'E-mail', en: 'Email' },
  PHONE_NUMBER: { fr: 'Téléphone', en: 'Phone' },
  FR_PHONE: { fr: 'Téléphone', en: 'Phone' },
  IBAN_CODE: { fr: 'IBAN', en: 'IBAN' },
  FR_IBAN: { fr: 'IBAN', en: 'IBAN' },
  FR_NIR: { fr: 'N° sécu', en: 'Social security no.' },
  FR_PLATE: { fr: 'Immatriculation', en: 'Licence plate' },
  CREDIT_CARD: { fr: 'Carte bancaire', en: 'Credit card' },
  LOCATION: { fr: 'Lieu', en: 'Location' },
  DATE_TIME: { fr: 'Date', en: 'Date' },
  IP_ADDRESS: { fr: 'Adresse IP', en: 'IP address' },
  URL: { fr: 'URL', en: 'URL' },
}

function piiLabel(entity: string, locale: 'fr' | 'en'): string {
  const known = PII_LABELS[entity]
  if (known) return known[locale]
  return entity.toLowerCase().replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase())
}

/** Small "masked by NeMo Guardrails" badge for one PII entity. */
export function PiiBadge({ entity }: { entity: string }) {
  const { t, locale } = useTranslation()
  return (
    <span
      title={`${t('pii.masked')} — ${entity}`}
      className="mx-0.5 inline-flex translate-y-[-1px] items-center gap-1 rounded-md bg-violet-500/10 px-1.5 py-px align-middle text-[11px] font-semibold text-violet-700 ring-1 ring-inset ring-violet-500/25 dark:text-violet-300"
    >
      <Lock className="h-3 w-3" />
      {piiLabel(entity, locale)}
    </span>
  )
}

/** Plain text (no markdown) with PII placeholders rendered as badges. */
export function MaskedText({ text, className }: { text: string; className?: string }) {
  const parts: ReactNode[] = []
  let last = 0
  for (const m of text.matchAll(PII_ANY)) {
    const idx = m.index ?? 0
    if (idx > last) parts.push(text.slice(last, idx))
    parts.push(<PiiBadge key={idx} entity={m[1] || m[2]} />)
    last = idx + m[0].length
  }
  if (last < text.length) parts.push(text.slice(last))
  return <span className={className}>{parts.map((p, i) => <Fragment key={i}>{p}</Fragment>)}</span>
}

/** Turn PII placeholders into inline-code tokens the `code` renderer turns into badges. */
function protectPii(markdown: string): string {
  return markdown
    .replace(PII_BRACKET, (_m, e) => `\`${PII_CODE_PREFIX}${e}\``)
    .replace(PII_ANGLE, (_m, e) => `\`${PII_CODE_PREFIX}${e}\``)
}

/** Markdown with GFM tables/lists, styled by @tailwindcss/typography (dark aware). */
export function Markdown({ children, className }: { children: string; className?: string }) {
  return (
    <div
      className={cn(
        'prose prose-sm max-w-none dark:prose-invert',
        'prose-p:my-1.5 prose-p:leading-relaxed prose-headings:mb-2 prose-headings:mt-3 prose-headings:font-semibold',
        'prose-ul:my-1.5 prose-ol:my-1.5 prose-li:my-0.5 prose-a:text-brand-600 dark:prose-a:text-brand-400',
        'prose-table:my-2 prose-table:text-xs prose-th:bg-surface-muted prose-th:px-2 prose-th:py-1.5 prose-td:px-2 prose-td:py-1.5',
        'prose-code:rounded prose-code:bg-surface-muted prose-code:px-1 prose-code:py-0.5 prose-code:before:content-none prose-code:after:content-none',
        'prose-pre:bg-surface-sunken prose-pre:text-ink',
        className,
      )}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto rounded-lg border border-line"><table className="!my-0">{children}</table></div>
          ),
          code: ({ children, className: codeClass }) => {
            const text = String(children ?? '')
            if (!codeClass && text.startsWith(PII_CODE_PREFIX)) {
              return <PiiBadge entity={text.slice(PII_CODE_PREFIX.length)} />
            }
            return <code className={codeClass}>{children}</code>
          },
        }}
      >
        {protectPii(children)}
      </ReactMarkdown>
    </div>
  )
}
