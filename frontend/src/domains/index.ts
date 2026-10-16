/** The business domains as the UI shows them (see types.ts). Register a new domain in DOMAINS. */
import type { Domain } from '../types/case'
import { claims } from './claims'
import { postal } from './postal'
import { tenders } from './tenders'
import type { DomainUI } from './types'

export const DOMAINS: Record<Domain, DomainUI> = { claims, tenders, postal }

export const domainUI = (name: Domain): DomainUI => DOMAINS[name]

export type { DomainUI } from './types'
