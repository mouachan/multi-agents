import {
  Building2, Info, Network, PackageX, ShieldCheck, Truck, type LucideIcon,
} from 'lucide-react'

/**
 * Visual identity of the agents (icons + accent classes). Names and descriptions come
 * from GET /api/v1/agents and the i18n `agentNames.*` keys; this module only maps an
 * agent id to its look. Class strings are static so Tailwind can see them.
 */
export interface AgentAccent {
  solid: string      // avatar / strong fill
  soft: string       // tinted background + text
  text: string       // accent text
  ring: string       // focus / highlight ring
  dot: string        // small status dot
  stroke: string     // SVG stroke (graph)
}

const ACCENTS: Record<string, AgentAccent> = {
  brand: {
    solid: 'bg-brand-600 text-white', soft: 'bg-brand-500/10 text-brand-700 dark:text-brand-300',
    text: 'text-brand-600 dark:text-brand-400', ring: 'ring-brand-500/40', dot: 'bg-brand-500', stroke: 'stroke-brand-500',
  },
  emerald: {
    solid: 'bg-emerald-600 text-white', soft: 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300',
    text: 'text-emerald-600 dark:text-emerald-400', ring: 'ring-emerald-500/40', dot: 'bg-emerald-500', stroke: 'stroke-emerald-500',
  },
  amber: {
    solid: 'bg-amber-500 text-white', soft: 'bg-amber-500/10 text-amber-700 dark:text-amber-300',
    text: 'text-amber-600 dark:text-amber-400', ring: 'ring-amber-500/40', dot: 'bg-amber-500', stroke: 'stroke-amber-500',
  },
  rose: {
    solid: 'bg-rose-600 text-white', soft: 'bg-rose-500/10 text-rose-700 dark:text-rose-300',
    text: 'text-rose-600 dark:text-rose-400', ring: 'ring-rose-500/40', dot: 'bg-rose-500', stroke: 'stroke-rose-500',
  },
  sky: {
    solid: 'bg-sky-600 text-white', soft: 'bg-sky-500/10 text-sky-700 dark:text-sky-300',
    text: 'text-sky-600 dark:text-sky-400', ring: 'ring-sky-500/40', dot: 'bg-sky-500', stroke: 'stroke-sky-500',
  },
  teal: {
    solid: 'bg-teal-600 text-white', soft: 'bg-teal-500/10 text-teal-700 dark:text-teal-300',
    text: 'text-teal-600 dark:text-teal-400', ring: 'ring-teal-500/40', dot: 'bg-teal-500', stroke: 'stroke-teal-500',
  },
}

interface AgentVisual {
  icon: LucideIcon
  accent: AgentAccent
  short: string
  /** Business area of the agent (for the postal profiles sharing one A2A agent) */
  domain: 'orchestrator' | 'claims' | 'tenders' | 'postal'
}

const VISUALS: Record<string, AgentVisual> = {
  orchestrator: { icon: Network, accent: ACCENTS.brand, short: 'HUB', domain: 'orchestrator' },
  claims: { icon: ShieldCheck, accent: ACCENTS.emerald, short: 'SI', domain: 'claims' },
  tenders: { icon: Building2, accent: ACCENTS.amber, short: 'AO', domain: 'tenders' },
  courrier_reclamation: { icon: PackageX, accent: ACCENTS.rose, short: 'CR', domain: 'postal' },
  courrier_info: { icon: Info, accent: ACCENTS.sky, short: 'IP', domain: 'postal' },
  courrier_suivi: { icon: Truck, accent: ACCENTS.teal, short: 'SC', domain: 'postal' },
}

export function agentVisual(agentId?: string | null): AgentVisual {
  return VISUALS[agentId || 'orchestrator'] || VISUALS.orchestrator
}

export const KNOWN_AGENT_IDS = Object.keys(VISUALS).filter((id) => id !== 'orchestrator')

/** MCP servers shown in the topology (keys match the tool-display config). */
export const MCP_SERVERS = ['ocr-server', 'rag-server', 'claims-server', 'tenders-server', 'postal-server', 'tracking-server'] as const

/**
 * MCP server owning a tool. Behind the MCP Gateway every event says "mcp-gateway",
 * so the server is derived from the tool name (same mapping as agents/shared/ogx_client.py).
 */
export function toolServer(tool: string, serverLabel?: string): string {
  if (serverLabel && serverLabel !== 'mcp-gateway') return serverLabel
  if (tool.startsWith('ocr_') || tool === 'list_supported_formats') return 'ocr-server'
  if (tool.startsWith('retrieve_') || tool.includes('knowledge') || tool === 'generate_document_embedding') return 'rag-server'
  if (tool.includes('tracking')) return 'tracking-server'
  if (tool.includes('reclamation')) return 'postal-server'
  if (tool.includes('tender')) return 'tenders-server'
  if (tool.includes('claim')) return 'claims-server'
  return serverLabel || 'mcp-gateway'
}
