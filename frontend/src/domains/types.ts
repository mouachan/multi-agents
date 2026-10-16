import type { ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'
import type { Column } from '../components/business/EntityTable'
import type { Tone } from '../components/ui/Badge'
import type { Locale } from '../i18n/translations'
import type { Case, Domain } from '../types/case'

export type Translate = (key: string) => string

/**
 * How a business domain is shown — the UI side of backend/app/domains (one file per domain here).
 * The list page, the case page and the review panel are shared; only what differs is declared.
 */
export interface DomainUI {
  name: Domain
  path: string                  // page of the domain ('/claims'); a case is <path>/<id>
  i18n: string                  // section of the translations for the domain's own labels
  icon: LucideIcon
  iconClass: string             // colors of the icon tile
  agentId: string               // chat profile proposed from the home page
  /** status filter of the list, and the status of the cases waiting for a reviewer */
  statuses: string[]
  reviewStatus: string
  /** color of each decision value (decision.<value> gives its label) */
  decisionTones: Record<string, Tone>

  /** list page: columns, text searched, optional extra filter (type, region...) */
  columns: (t: Translate, locale: Locale) => Column<Case>[]
  searchText: (c: Case) => string
  extraFilter?: (cases: Case[], t: Translate) => { label: string; options: { value: string; label: string }[]; apply: (c: Case, value: string) => boolean }

  /** case page: the header (type badge, title, description, key fields, extra block) */
  hero: (c: Case, t: Translate, locale: Locale) => {
    kind?: ReactNode
    title?: ReactNode
    description?: ReactNode
    fields: { label: ReactNode; value: ReactNode }[]
    extra?: ReactNode
  }
  /** case page: cards only this domain has (tracking timeline, personal data found...) */
  Extras?: (props: { case: Case }) => JSX.Element | null
}
