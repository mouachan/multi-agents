import type { ReactNode } from 'react'
import {
  ArrowRight, Bot, CheckCircle2, ChevronRight, CircleDashed, Clock, Cpu, Fingerprint, Hash, KeyRound,
  Loader2, Lock, Route, ScrollText, Server, ShieldAlert, ShieldCheck, ShieldX, Sparkles, Workflow, Wrench, X, XCircle,
} from 'lucide-react'
import { useTranslation } from '../../i18n/LanguageContext'
import { useNow } from '../../hooks/useNow'
import { useToolDisplay } from '../../hooks/useToolDisplay'
import { agentVisual } from '../../lib/agents'
import { cn } from '../../lib/cn'
import { formatDuration } from '../../lib/format'
import type { ChatMessage, GuardrailsEvent, TraceStep, TurnTrace } from '../../types/chat'
import { Badge, type Tone } from '../ui/Badge'
import { EmptyState } from '../ui/Feedback'
import { IconButton } from '../ui/Button'
import { AgentAvatar } from './AgentAvatar'

// ---------------------------------------------------------------------------
// Small building blocks
// ---------------------------------------------------------------------------
function Section({ icon, title, right, children }: { icon: ReactNode; title: ReactNode; right?: ReactNode; children: ReactNode }) {
  return (
    <section className="rounded-xl border border-line bg-surface p-3">
      <header className="mb-2 flex items-center justify-between gap-2">
        <h4 className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-ink-subtle">
          {icon}
          {title}
        </h4>
        {right}
      </header>
      {children}
    </section>
  )
}

function KV({ k, children, mono }: { k: ReactNode; children: ReactNode; mono?: boolean }) {
  return (
    <div className="flex items-baseline justify-between gap-3 py-0.5 text-xs">
      <span className="shrink-0 text-ink-subtle">{k}</span>
      <span className={cn('min-w-0 truncate text-right text-ink', mono && 'font-mono text-[11px]')}>{children}</span>
    </div>
  )
}

const GUARDRAIL_TONES: Record<string, Tone> = {
  passed: 'success', modified: 'violet', blocked: 'danger', skipped: 'neutral', error: 'warning',
}

function GuardrailBadge({ status }: { status?: string }) {
  const { t } = useTranslation()
  if (!status) return <span className="text-xs text-ink-subtle">—</span>
  const Icon = status === 'blocked' ? ShieldX : status === 'modified' ? Lock : status === 'error' ? ShieldAlert : ShieldCheck
  return (
    <Badge tone={GUARDRAIL_TONES[status] ?? 'neutral'} icon={<Icon className="h-3 w-3" />}>
      {t(`a2a.gr_${status}`)}
    </Badge>
  )
}

const STATE_TONES: Record<string, Tone> = {
  submitted: 'neutral', working: 'info', completed: 'success', failed: 'danger', rejected: 'danger', canceled: 'warning',
}

// ---------------------------------------------------------------------------
// Live topology: Backend -> (JWT-SVID) -> A2A agent -> OGX -> MCP gateway
// ---------------------------------------------------------------------------
function FlowStrip({ trace, streaming }: { trace: TurnTrace; streaming: boolean }) {
  const { t } = useTranslation()
  const runningTool = trace.steps.some((s) => s.kind === 'tool' && s.status === 'running')
  const toolsUsed = trace.steps.some((s) => s.kind === 'tool')
  const generating = streaming && !runningTool && trace.state === 'working'
  const v = agentVisual(trace.agentId)

  const nodes = [
    { key: 'backend', label: t('a2a.node_backend'), icon: <Workflow className="h-3.5 w-3.5" />, active: streaming && !trace.request, done: !!trace.request },
    { key: 'agent', label: trace.agentId ? t(`agentNames.${trace.agentId}`) : t('a2a.node_agent'), icon: <Bot className="h-3.5 w-3.5" />, active: streaming && !!trace.request && !generating && !runningTool, done: !!trace.summary, accent: v.accent.soft },
    { key: 'ogx', label: 'OGX', icon: <Sparkles className="h-3.5 w-3.5" />, active: generating, done: !!trace.firstTextAt },
    { key: 'mcp', label: 'MCP', icon: <Server className="h-3.5 w-3.5" />, active: runningTool, done: toolsUsed && !runningTool },
  ]

  return (
    <div className="flex flex-wrap items-center gap-x-1 gap-y-1.5">
      {nodes.map((n, i) => (
        <div key={n.key} className="flex items-center gap-1">
          <div
            className={cn(
              'flex items-center gap-1.5 rounded-lg border px-2 py-1 text-[11px] font-medium transition-all',
              n.active ? 'border-brand-500/50 bg-brand-500/10 text-brand-700 shadow-glow dark:text-brand-300'
                : n.done ? cn('border-line text-ink', n.accent ?? 'bg-surface-muted') : 'border-dashed border-line text-ink-subtle',
            )}
          >
            {n.active ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : n.icon}
            <span className="max-w-[110px] truncate">{n.label}</span>
          </div>
          {i < nodes.length - 1 && (
            <div className="flex flex-col items-center">
              <ArrowRight className={cn('h-3 w-3', n.done ? 'text-ink-muted' : 'text-ink-subtle/50')} />
              {i === 0 && trace.request?.auth.scheme && trace.request.auth.scheme !== 'none' && (
                <span className="-mt-0.5 text-[8px] font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">SVID</span>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Timeline rows
// ---------------------------------------------------------------------------
function StepRow({ step, isLast, now, startedAt, streaming }: { step: TraceStep; isLast: boolean; now: number; startedAt: number; streaming: boolean }) {
  const { t, locale } = useTranslation()
  const { getToolLabel } = useToolDisplay()

  let icon: ReactNode
  let title: ReactNode
  let detail: ReactNode = null
  let tone = 'bg-surface-muted text-ink-muted ring-line'

  switch (step.kind) {
    case 'routing': {
      icon = <Route className="h-3.5 w-3.5" />
      title = <>{t('a2a.routedTo')} <b>{t(`agentNames.${step.event.agent_id}`)}</b></>
      detail = `${t(`a2a.method_${step.event.method}`)}${step.event.score != null ? ` · ${step.event.score.toFixed(2)}` : ''} · ${step.event.duration_ms} ms`
      tone = 'bg-brand-500/10 text-brand-600 ring-brand-500/25 dark:text-brand-300'
      break
    }
    case 'request': {
      icon = <KeyRound className="h-3.5 w-3.5" />
      title = <>{step.event.method || 'SendStreamingMessage'} → <b>{step.event.agent.name}</b></>
      detail = step.event.auth.scheme !== 'none' ? `${step.event.auth.scheme} · ${step.event.auth.audience ?? ''}` : t('a2a.noAuth')
      tone = 'bg-emerald-500/10 text-emerald-600 ring-emerald-500/25 dark:text-emerald-300'
      break
    }
    case 'state': {
      const st = step.state
      icon = st === 'completed' ? <CheckCircle2 className="h-3.5 w-3.5" />
        : st === 'failed' || st === 'rejected' ? <XCircle className="h-3.5 w-3.5" />
          : st === 'working' ? <Loader2 className={cn('h-3.5 w-3.5', streaming && isLast && 'animate-spin')} />
            : <CircleDashed className="h-3.5 w-3.5" />
      title = <>{t('a2a.task')} <Badge tone={STATE_TONES[st] ?? 'neutral'} className="ml-1">{t(`a2a.state_${st}`)}</Badge></>
      detail = step.taskId ? <span className="font-mono">{step.taskId.slice(0, 8)}…</span> : null
      tone = st === 'completed' ? 'bg-emerald-500/10 text-emerald-600 ring-emerald-500/25 dark:text-emerald-300'
        : st === 'failed' || st === 'rejected' ? 'bg-red-500/10 text-red-600 ring-red-500/25' : 'bg-sky-500/10 text-sky-600 ring-sky-500/25 dark:text-sky-300'
      break
    }
    case 'guardrails': {
      const ev: GuardrailsEvent = step.event
      icon = ev.status === 'blocked' ? <ShieldX className="h-3.5 w-3.5" /> : ev.status === 'modified' ? <Lock className="h-3.5 w-3.5" /> : <ShieldCheck className="h-3.5 w-3.5" />
      title = <>NeMo Guardrails · {t(`a2a.stage_${ev.stage}`)} <span className="ml-1"><GuardrailBadge status={ev.status} /></span></>
      detail = ev.rail || null
      tone = 'bg-violet-500/10 text-violet-600 ring-violet-500/25 dark:text-violet-300'
      break
    }
    case 'tool': {
      const running = step.status === 'running'
      icon = running ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : step.status === 'error' ? <XCircle className="h-3.5 w-3.5" /> : <Wrench className="h-3.5 w-3.5" />
      title = <>{t('a2a.mcpTool')} <b>{getToolLabel(step.name, locale)}</b></>
      const dur = step.doneAt != null ? step.doneAt - step.at : running ? now - startedAt - step.at : null
      detail = [step.server, dur != null ? formatDuration(dur) : null].filter(Boolean).join(' · ')
      tone = step.status === 'error' ? 'bg-red-500/10 text-red-600 ring-red-500/25' : 'bg-amber-500/10 text-amber-600 ring-amber-500/25 dark:text-amber-300'
      break
    }
  }

  return (
    <li className="relative flex gap-3 pb-3 last:pb-0">
      {!isLast && <span className="absolute left-[13px] top-7 h-[calc(100%-1.25rem)] w-px bg-line" />}
      <span className={cn('relative z-10 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg ring-1 ring-inset', tone)}>{icon}</span>
      <div className="min-w-0 flex-1 pt-0.5">
        <div className="flex items-start justify-between gap-2">
          <p className="text-xs leading-snug text-ink">{title}</p>
          <span className="shrink-0 font-mono text-[10px] tabular-nums text-ink-subtle">+{formatDuration(step.at)}</span>
        </div>
        {detail && <p className="mt-0.5 truncate text-[11px] text-ink-subtle">{detail}</p>}
      </div>
    </li>
  )
}

// ---------------------------------------------------------------------------
// Panel
// ---------------------------------------------------------------------------
interface A2APanelProps {
  message: ChatMessage | null
  onClose?: () => void
}

export function A2APanel({ message, onClose }: A2APanelProps) {
  const { t } = useTranslation()
  const trace = message?.trace
  const streaming = !!message?.streaming
  const now = useNow(streaming, 500)

  const header = (
    <div className="flex items-center justify-between border-b border-line px-4 py-3">
      <div className="flex items-center gap-2">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-500/10 text-brand-600 dark:text-brand-300">
          <Workflow className="h-4 w-4" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-ink">{t('a2a.title')}</h3>
          <p className="text-[11px] text-ink-subtle">{t('a2a.subtitle')}</p>
        </div>
      </div>
      {onClose && <IconButton label={t('a2a.hide')} icon={<X className="h-4 w-4" />} onClick={onClose} />}
    </div>
  )

  if (!trace || (trace.steps.length === 0 && !streaming)) {
    return (
      <div className="flex h-full flex-col">
        {header}
        <EmptyState icon={<Workflow className="h-5 w-5" />} title={t('a2a.emptyTitle')} description={t('a2a.emptyText')} className="flex-1" />
      </div>
    )
  }

  const routing = trace.routing
  const req = trace.request
  const summary = trace.summary
  const elapsed = trace.finishedAt ?? now - trace.startedAt
  const generating = streaming && trace.state === 'working' && !trace.steps.some((s) => s.kind === 'tool' && s.status === 'running')
  const lastGuardrail = (stage: string) => {
    const found = trace.steps.filter((s): s is Extract<TraceStep, { kind: 'guardrails' }> => s.kind === 'guardrails' && s.event.stage === stage)
    return found.length ? found[found.length - 1].event.status : undefined
  }
  const gIn = summary?.guardrails?.input?.status ?? lastGuardrail('input')
  const gOut = summary?.guardrails?.output?.status ?? lastGuardrail('output')

  return (
    <div className="flex h-full flex-col">
      {header}
      <div className="flex-1 space-y-3 overflow-y-auto p-3">
        {/* Live topology + elapsed */}
        <div className="rounded-xl border border-line bg-surface-muted/60 p-3">
          <div className="mb-2 flex items-center justify-between">
            <span className="label">{t('a2a.flow')}</span>
            <span className={cn('inline-flex items-center gap-1 font-mono text-[11px] tabular-nums', streaming ? 'text-brand-600 dark:text-brand-300' : 'text-ink-muted')}>
              <Clock className="h-3 w-3" />{formatDuration(elapsed)}
            </span>
          </div>
          <FlowStrip trace={trace} streaming={streaming} />
        </div>

        {/* Routing decision */}
        {routing && (
          <Section
            icon={<Route className="h-3.5 w-3.5" />}
            title={t('a2a.routing')}
            right={<Badge tone="brand">{t(`a2a.method_${routing.method}`)}</Badge>}
          >
            <div className="mb-2 flex items-center gap-2">
              <AgentAvatar agentId={routing.agent_id} size="sm" />
              <span className="text-sm font-medium text-ink">{t(`agentNames.${routing.agent_id}`)}</span>
              <span className="ml-auto font-mono text-[11px] text-ink-subtle">{routing.duration_ms} ms</span>
            </div>
            {routing.candidates.length > 0 && (
              <div className="space-y-1.5">
                {routing.candidates.map((c) => {
                  const pct = Math.max(0, Math.min(1, c.score)) * 100
                  const chosen = c.agent_id === routing.agent_id
                  return (
                    <div key={c.agent_id} className="text-[11px]">
                      <div className="mb-0.5 flex justify-between">
                        <span className={cn(chosen ? 'font-semibold text-ink' : 'text-ink-muted')}>{t(`agentNames.${c.agent_id}`)}</span>
                        <span className="font-mono tabular-nums text-ink-subtle">{c.score.toFixed(3)}</span>
                      </div>
                      <div className="h-1.5 overflow-hidden rounded-full bg-surface-sunken">
                        <div className={cn('h-full rounded-full', chosen ? agentVisual(c.agent_id).accent.dot : 'bg-ink-subtle/40')} style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
            <p className="mt-2 text-[11px] leading-relaxed text-ink-subtle">{t(`a2a.methodHelp_${routing.method}`)}</p>
          </Section>
        )}

        {/* A2A request: agent card + identity */}
        {req && (
          <Section icon={<KeyRound className="h-3.5 w-3.5" />} title={t('a2a.request')} right={<span className="font-mono text-[10px] text-ink-subtle">{req.method}</span>}>
            <div className="mb-2 flex items-center gap-2">
              <AgentAvatar agentId={trace.agentId} size="sm" />
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-ink">{req.agent.name}{req.agent.version && <span className="ml-1 text-[11px] font-normal text-ink-subtle">v{req.agent.version}</span>}</p>
                {req.agent.url && <p className="truncate font-mono text-[10px] text-ink-subtle">{req.agent.url}</p>}
              </div>
            </div>
            {!!req.agent.skills?.length && (
              <div className="mb-2 flex flex-wrap gap-1">
                {req.agent.skills.map((s) => <span key={s} className="rounded-md bg-surface-muted px-1.5 py-0.5 text-[10px] text-ink-muted">{s}</span>)}
              </div>
            )}
            <div className="divide-y divide-line">
              {req.profile && <KV k={t('a2a.profile')}>{req.profile}</KV>}
              {req.mode && <KV k={t('a2a.mode')}>{req.mode}</KV>}
              <KV k={t('a2a.auth')}>
                {req.auth.scheme !== 'none'
                  ? <Badge tone="success" icon={<Fingerprint className="h-3 w-3" />}>{req.auth.scheme}</Badge>
                  : <Badge tone="neutral">{t('a2a.noAuth')}</Badge>}
              </KV>
              {req.auth.audience && <KV k={t('a2a.audience')} mono>{req.auth.audience}</KV>}
              <KV k={t('a2a.caller')} mono>
                {summary?.caller || (summary ? <span className="font-sans text-ink-subtle">{t('a2a.callerNone')}</span> : '…')}
              </KV>
              {trace.taskId && <KV k={t('a2a.taskId')} mono>{trace.taskId}</KV>}
              {trace.contextId && <KV k={t('a2a.contextId')} mono>{trace.contextId}</KV>}
            </div>
          </Section>
        )}

        {/* Timeline */}
        <Section icon={<ScrollText className="h-3.5 w-3.5" />} title={t('a2a.timeline')}>
          <ol>
            {trace.steps.map((step, i) => (
              <StepRow
                key={i}
                step={step}
                isLast={i === trace.steps.length - 1 && !streaming}
                now={now}
                startedAt={trace.startedAt}
                streaming={streaming}
              />
            ))}
            {streaming && (
              <li className="flex items-center gap-3 pt-1">
                <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-500/10 text-brand-600 ring-1 ring-inset ring-brand-500/25 dark:text-brand-300">
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                </span>
                <div className="text-xs text-ink-muted">
                  {generating ? (trace.firstTextAt != null ? t('a2a.streamingText') : t('a2a.generating')) : t('a2a.waiting')}
                  {trace.lastHeartbeatMs != null && (
                    <span className="ml-1 text-ink-subtle">· heartbeat {formatDuration(trace.lastHeartbeatMs)}</span>
                  )}
                </div>
              </li>
            )}
          </ol>
        </Section>

        {/* Summary */}
        {(summary || trace.finishedAt != null) && !streaming && (
          <Section icon={<CheckCircle2 className="h-3.5 w-3.5" />} title={t('a2a.summary')}>
            <div className="divide-y divide-line">
              <KV k={t('a2a.totalDuration')}>{formatDuration(summary?.duration_ms ?? trace.finishedAt)}</KV>
              {summary?.agent_duration_ms != null && <KV k={t('a2a.agentDuration')}>{formatDuration(summary.agent_duration_ms)}</KV>}
              {trace.firstTextAt != null && <KV k={t('a2a.firstText')}>{formatDuration(trace.firstTextAt)}</KV>}
              {trace.modelId && <KV k={<span className="inline-flex items-center gap-1"><Cpu className="h-3 w-3" />{t('a2a.model')}</span>}>{trace.modelId}</KV>}
              {trace.usage?.total_tokens ? (
                <KV k={<span className="inline-flex items-center gap-1"><Hash className="h-3 w-3" />{t('a2a.tokens')}</span>}>
                  {trace.usage.prompt_tokens} + {trace.usage.completion_tokens} = <b>{trace.usage.total_tokens}</b>
                </KV>
              ) : null}
              {summary?.prompt?.name && (
                <KV k={t('a2a.prompt')} mono>
                  {summary.prompt.name}{summary.prompt.version != null && `@v${summary.prompt.version}`}
                  {summary.prompt.source && <span className="ml-1 font-sans text-ink-subtle">({summary.prompt.source})</span>}
                </KV>
              )}
              <KV k={t('a2a.guardIn')}><GuardrailBadge status={gIn} /></KV>
              <KV k={t('a2a.guardOut')}><GuardrailBadge status={gOut} /></KV>
              {summary?.state && <KV k={t('a2a.finalState')}><Badge tone={STATE_TONES[summary.state] ?? 'neutral'}>{t(`a2a.state_${summary.state}`)}</Badge></KV>}
            </div>
          </Section>
        )}

        {message?.error && (
          <div className="flex items-start gap-2 rounded-xl border border-red-500/30 bg-red-500/5 px-3 py-2 text-xs text-red-700 dark:text-red-300">
            <XCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            <span className="break-words">{message.error}</span>
          </div>
        )}

        {message?.stopped && (
          <p className="flex items-center gap-1.5 px-1 text-[11px] text-ink-subtle"><ChevronRight className="h-3 w-3" />{t('conv.stopped')}</p>
        )}
      </div>
    </div>
  )
}
