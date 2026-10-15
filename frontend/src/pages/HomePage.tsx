import { useState, type FormEvent, type ReactNode } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  ArrowRight, Building2, CheckCircle2, Clock, Fingerprint, FlaskConical, Network, Package, Server, ShieldCheck, Sparkles, UserCheck,
} from 'lucide-react'
import { AgentAvatar } from '../components/chat/AgentAvatar'
import { Card } from '../components/ui/Card'
import { useResource } from '../hooks/useResource'
import { useTranslation } from '../i18n/LanguageContext'
import { cn } from '../lib/cn'
import { useAuth } from '../auth/AuthContext'
import { claimsApi, postalApi, tendersApi } from '../services/api'

interface DomainStats { total: number; pending: number; review: number; completed: number }

function DomainCard({ to, agentId, icon, accent, title, description, stats, loading }: {
  to: string; agentId: string; icon: ReactNode; accent: string; title: string; description: string; stats?: DomainStats; loading: boolean
}) {
  const { t } = useTranslation()
  const cell = (label: string, value: number | undefined, Icon: typeof Clock) => (
    <div className="rounded-xl bg-surface-muted px-3 py-2">
      <p className="flex items-center gap-1 text-[11px] text-ink-subtle"><Icon className="h-3 w-3" />{label}</p>
      <p className="text-lg font-semibold tabular-nums text-ink">{loading ? <span className="skeleton inline-block h-5 w-8" /> : value ?? '—'}</p>
    </div>
  )
  return (
    <Card className="flex flex-col p-5">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className={cn('flex h-11 w-11 items-center justify-center rounded-2xl', accent)}>{icon}</div>
        <Link to={`/chat?agent=${agentId}`} className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs font-medium text-ink-muted hover:bg-surface-muted hover:text-ink">
          <AgentAvatar agentId={agentId} size="sm" /> {t('dash.askAgent')}
        </Link>
      </div>
      <h3 className="text-base font-semibold text-ink">{title}</h3>
      <p className="mt-1 text-sm text-ink-muted">{description}</p>
      <div className="mt-4 grid grid-cols-3 gap-2">
        {cell(t('status.pending'), stats?.pending, Clock)}
        {cell(t('status.manual_review'), stats?.review, UserCheck)}
        {cell(t('status.completed'), stats?.completed, CheckCircle2)}
      </div>
      <Link to={to} className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-brand-600 hover:text-brand-700 dark:text-brand-400">
        {t('dash.open')} ({loading ? '…' : stats?.total ?? 0}) <ArrowRight className="h-4 w-4" />
      </Link>
    </Card>
  )
}

const PLATFORM = [
  { key: 'ogx', icon: Sparkles },
  { key: 'a2a', icon: Network },
  { key: 'mcp', icon: Server },
  { key: 'guardrails', icon: ShieldCheck },
  { key: 'mlflow', icon: FlaskConical },
  { key: 'spiffe', icon: Fingerprint },
]

export default function HomePage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [prompt, setPrompt] = useState('')
  const { can } = useAuth()
  // Statistics of the domains the user may use only (the others answer 403)
  const { data, loading } = useResource(async () => {
    const ifAllowed = <T,>(allowed: boolean, load: () => Promise<T>) =>
      allowed ? load() : Promise.reject(new Error('no access'))
    const [c, tn, p] = await Promise.allSettled([
      ifAllowed(can('claims'), claimsApi.statistics),
      ifAllowed(can('tenders'), tendersApi.statistics),
      ifAllowed(can('postal'), postalApi.statistics),
    ])
    return {
      claims: c.status === 'fulfilled' ? { total: c.value.total_claims, pending: c.value.pending_claims, review: c.value.manual_review_claims, completed: c.value.completed_claims } : undefined,
      tenders: tn.status === 'fulfilled' ? { total: tn.value.total_tenders, pending: tn.value.pending_tenders, review: tn.value.manual_review_tenders, completed: tn.value.completed_tenders } : undefined,
      postal: p.status === 'fulfilled' ? { total: p.value.total, pending: p.value.by_status?.pending ?? 0, review: (p.value.by_status?.manual_review ?? 0) + (p.value.by_status?.escalated ?? 0), completed: p.value.by_status?.completed ?? 0 } : undefined,
    }
  }, [])

  const start = (e: FormEvent) => {
    e.preventDefault()
    if (prompt.trim()) navigate('/chat', { state: { prompt: prompt.trim() } })
  }

  return (
    <div className="space-y-6">
      {/* Hero */}
      <div className="relative overflow-hidden rounded-3xl border border-line bg-gradient-to-br from-brand-600 via-brand-700 to-indigo-900 p-8 text-white shadow-elevated">
        <div className="pointer-events-none absolute -right-20 -top-20 h-72 w-72 rounded-full bg-white/10 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-24 left-1/3 h-64 w-64 rounded-full bg-redhat/20 blur-3xl" />
        <p className="mb-2 inline-flex items-center gap-1.5 rounded-full bg-white/10 px-3 py-1 text-xs font-medium ring-1 ring-white/20">
          <Sparkles className="h-3.5 w-3.5" /> Red Hat OpenShift AI 3.5
        </p>
        <h1 className="max-w-2xl text-3xl font-semibold tracking-tight">{t('home.title')}</h1>
        <p className="mt-2 max-w-2xl text-sm text-white/75">{t('home.subtitle')}</p>
        <form onSubmit={start} className="mt-6 flex max-w-2xl gap-2 rounded-2xl bg-white/10 p-1.5 ring-1 ring-white/20 backdrop-blur">
          <input
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder={t('home.placeholder')}
            className="flex-1 bg-transparent px-3 text-sm text-white placeholder:text-white/50 focus:outline-none"
          />
          <button type="submit" className="inline-flex items-center gap-1.5 rounded-xl bg-white px-4 py-2 text-sm font-semibold text-brand-700 transition-colors hover:bg-white/90">
            {t('home.start')} <ArrowRight className="h-4 w-4" />
          </button>
        </form>
      </div>

      {/* Domains */}
      <div className="grid gap-4 lg:grid-cols-3">
        {can('claims') && <DomainCard to="/claims" agentId="claims" icon={<ShieldCheck className="h-5 w-5" />} accent="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
          title={t('nav.claims')} description={t('dash.claimsDesc')} stats={data?.claims} loading={loading} />}
        {can('tenders') && <DomainCard to="/tenders" agentId="tenders" icon={<Building2 className="h-5 w-5" />} accent="bg-amber-500/10 text-amber-600 dark:text-amber-400"
          title={t('nav.tenders')} description={t('dash.tendersDesc')} stats={data?.tenders} loading={loading} />}
        {can('postal') && <DomainCard to="/postal" agentId="courrier_reclamation" icon={<Package className="h-5 w-5" />} accent="bg-rose-500/10 text-rose-600 dark:text-rose-400"
          title={t('nav.postal')} description={t('dash.postalDesc')} stats={data?.postal} loading={loading} />}
      </div>

      {/* Platform */}
      <div>
        <h2 className="mb-3 text-sm font-semibold text-ink">{t('dash.platform')}</h2>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
          {PLATFORM.map(({ key, icon: Icon }) => (
            <Card key={key} className="p-4">
              <Icon className="mb-2 h-5 w-5 text-brand-500" />
              <p className="text-sm font-semibold text-ink">{t(`dash.p_${key}`)}</p>
              <p className="mt-0.5 text-xs leading-relaxed text-ink-muted">{t(`dash.p_${key}_desc`)}</p>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}
