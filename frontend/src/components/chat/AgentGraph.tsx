import { Network, Server } from 'lucide-react'
import { useTranslation } from '../../i18n/LanguageContext'
import { useToolDisplay } from '../../hooks/useToolDisplay'
import { agentVisual, MCP_SERVERS } from '../../lib/agents'
import { cn } from '../../lib/cn'
import type { AgentInfo } from '../../types/chat'

interface AgentGraphProps {
  agents: AgentInfo[]
  activeAgentId?: string | null
  /** an agent is currently answering (pulse) */
  live?: boolean
  routing?: boolean
  activeServers: Set<string>
  usedServers: Set<string>
  onAgentClick: (agentId: string) => void
}

const POSTAL_PROFILES = ['courrier_reclamation', 'courrier_info', 'courrier_suivi']

function AgentNode({ agentId, active, live, label, tools, onClick }: {
  agentId: string; active: boolean; live: boolean; label: string; tools?: number; onClick: () => void
}) {
  const v = agentVisual(agentId)
  const Icon = v.icon
  return (
    <button
      onClick={onClick}
      title={label}
      className={cn(
        'group flex min-w-0 items-center gap-2 rounded-xl border px-2 py-1.5 text-left transition-all',
        active ? cn('border-transparent ring-2', v.accent.ring, v.accent.soft) : 'border-line bg-surface hover:bg-surface-muted',
      )}
    >
      <span className={cn('relative flex h-6 w-6 shrink-0 items-center justify-center rounded-lg', v.accent.solid)}>
        <Icon className="h-3.5 w-3.5" />
        {active && live && <span className={cn('absolute -right-0.5 -top-0.5 h-2 w-2 animate-ping rounded-full', v.accent.dot)} />}
      </span>
      <span className="min-w-0">
        <span className="block text-[11px] font-semibold leading-tight text-ink">{label}</span>
        {tools != null && <span className="block text-[10px] text-ink-subtle">{tools} MCP</span>}
      </span>
    </button>
  )
}

/** Live topology: orchestrator -> A2A agents (postal = 3 profiles of one agent) -> MCP servers. */
export function AgentGraph({ agents, activeAgentId, live, routing, activeServers, usedServers, onAgentClick }: AgentGraphProps) {
  const { t } = useTranslation()
  const { getServerInfo } = useToolDisplay()
  const tools = (id: string) => agents.find((a) => a.id === id)?.tools.length
  const name = (id: string) => t(`agentNames.${id}`)

  return (
    <div className="space-y-2.5">
      {/* Orchestrator */}
      <div className="flex justify-center">
        <div className={cn(
          'flex items-center gap-2 rounded-xl border px-3 py-1.5 text-xs font-semibold transition-all',
          routing ? 'border-brand-500/50 bg-brand-500/10 text-brand-700 shadow-glow dark:text-brand-300' : 'border-line bg-surface text-ink',
        )}>
          <Network className={cn('h-3.5 w-3.5', routing && 'animate-pulse')} />
          {t('graph.orchestrator')}
        </div>
      </div>
      <div className="mx-auto h-3 w-px bg-line" />

      {/* A2A agents */}
      <div className="grid grid-cols-2 gap-1.5">
        <AgentNode agentId="claims" label={name('claims')} tools={tools('claims')} active={activeAgentId === 'claims'} live={!!live} onClick={() => onAgentClick('claims')} />
        <AgentNode agentId="tenders" label={name('tenders')} tools={tools('tenders')} active={activeAgentId === 'tenders'} live={!!live} onClick={() => onAgentClick('tenders')} />
      </div>
      <div className={cn(
        'rounded-xl border border-dashed p-1.5 transition-colors',
        activeAgentId && POSTAL_PROFILES.includes(activeAgentId) ? 'border-rose-500/40' : 'border-line',
      )}>
        <p className="mb-1 px-1 text-[10px] font-medium uppercase tracking-wide text-ink-subtle">{t('graph.postalAgent')}</p>
        <div className="grid grid-cols-1 gap-1">
          {POSTAL_PROFILES.map((id) => (
            <AgentNode key={id} agentId={id} label={name(id)} active={activeAgentId === id} live={!!live} onClick={() => onAgentClick(id)} />
          ))}
        </div>
      </div>
      <div className="mx-auto h-3 w-px bg-line" />

      {/* MCP servers behind the gateway */}
      <div className="rounded-xl bg-surface-muted p-2">
        <p className="mb-1.5 flex items-center gap-1 text-[10px] font-medium uppercase tracking-wide text-ink-subtle">
          <Server className="h-3 w-3" /> {t('graph.mcpGateway')}
        </p>
        <div className="grid grid-cols-3 gap-1">
          {MCP_SERVERS.map((s) => {
            const running = activeServers.has(s)
            const used = usedServers.has(s)
            return (
              <span
                key={s}
                className={cn(
                  'flex items-center justify-center gap-1 rounded-lg border px-1 py-1 text-[10px] font-medium transition-all',
                  running ? 'border-amber-500/50 bg-amber-500/15 text-amber-700 dark:text-amber-300'
                    : used ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300'
                      : 'border-line bg-surface text-ink-subtle',
                )}
              >
                {running && <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-amber-500" />}
                {getServerInfo(s)?.label ?? s.replace('-server', '')}
              </span>
            )
          })}
        </div>
      </div>
    </div>
  )
}
