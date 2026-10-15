import { useState } from 'react'
import { Box, Cpu, FolderLock, Globe, Play, ShieldCheck, ShieldX, UserRound } from 'lucide-react'
import { SandboxRun } from '../components/sandbox/SandboxRun'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card, CardBody, CardHeader, Field } from '../components/ui/Card'
import { ErrorBanner, PageLoader } from '../components/ui/Feedback'
import { PageHeader } from '../components/ui/PageHeader'
import { useResource } from '../hooks/useResource'
import { useTranslation } from '../i18n/LanguageContext'
import { sandboxApi } from '../services/api'
import type { SandboxDemoResult, SandboxInfo, SandboxScenario } from '../types/sandbox'

const SCENARIOS: { id: SandboxScenario; expect: 'allowed' | 'denied' }[] = [
  { id: 'compute', expect: 'allowed' },
  { id: 'identity', expect: 'allowed' },
  { id: 'network', expect: 'denied' },
  { id: 'write_system', expect: 'denied' },
  { id: 'read_outside', expect: 'denied' },
]

/** The scenario behaved as the policy says: allowed code ran, forbidden actions failed. */
function isolationHolds(r: SandboxDemoResult): boolean {
  return r.expect === 'allowed' ? r.exit_code === 0 && !r.error : r.exit_code !== 0 || !!r.error
}

function PathList({ title, paths, tone }: { title: string; paths: string[]; tone: 'success' | 'warning' }) {
  return (
    <div>
      <p className="label mb-1.5">{title}</p>
      <div className="flex flex-wrap gap-1">
        {paths.length ? paths.map((p) => <Badge key={p} tone={tone}><span className="font-mono">{p}</span></Badge>)
          : <span className="text-xs text-ink-subtle">—</span>}
      </div>
    </div>
  )
}

function PolicyCard({ info }: { info: SandboxInfo }) {
  const { t } = useTranslation()
  const fs = info.policy.filesystem_policy ?? {}
  const network = Object.keys(info.policy.network_policies ?? {})
  const proc = info.policy.process ?? {}

  return (
    <Card>
      <CardHeader icon={<ShieldCheck className="h-4 w-4" />} title={t('sandbox.policyTitle')} subtitle={t('sandbox.policySubtitle')} />
      <CardBody className="grid gap-5 md:grid-cols-3">
        <div className="space-y-3">
          <p className="flex items-center gap-1.5 text-sm font-semibold text-ink"><FolderLock className="h-4 w-4" />{t('sandbox.filesystem')}</p>
          <PathList title={t('sandbox.readWrite')} paths={fs.read_write ?? []} tone="warning" />
          <PathList title={t('sandbox.readOnly')} paths={fs.read_only ?? []} tone="success" />
          <p className="text-xs text-ink-subtle">{t('sandbox.otherPaths')}</p>
          <p className="text-xs text-ink-subtle">Landlock : <b>{info.policy.landlock?.compatibility ?? '—'}</b></p>
        </div>
        <div className="space-y-3">
          <p className="flex items-center gap-1.5 text-sm font-semibold text-ink"><Globe className="h-4 w-4" />{t('sandbox.network')}</p>
          {network.length ? (
            <div className="flex flex-wrap gap-1">{network.map((n) => <Badge key={n} tone="warning">{n}</Badge>)}</div>
          ) : (
            <Badge tone="danger" icon={<ShieldX className="h-3 w-3" />}>{t('sandbox.networkDenyAll')}</Badge>
          )}
          <p className="text-xs text-ink-subtle">{t('sandbox.networkHelp')}</p>
        </div>
        <div className="space-y-3">
          <p className="flex items-center gap-1.5 text-sm font-semibold text-ink"><UserRound className="h-4 w-4" />{t('sandbox.process')}</p>
          <Field label={t('sandbox.runAs')}><span className="font-mono">{proc.run_as_user ?? '—'}:{proc.run_as_group ?? '—'}</span></Field>
          <Field label={t('sandbox.binary')}><span className="font-mono">{info.python}</span></Field>
          <Field label={t('sandbox.timeout')}>{info.max_exec_timeout_s ?? '—'} s</Field>
        </div>
      </CardBody>
      <details className="border-t border-line px-5 py-3">
        <summary className="cursor-pointer text-xs font-medium text-ink-muted">{t('sandbox.rawPolicy')}</summary>
        <pre className="mt-2 max-h-96 overflow-auto rounded-lg border border-line bg-surface-sunken p-3 font-mono text-[11px] text-ink">{info.policy_yaml}</pre>
      </details>
    </Card>
  )
}

function DemoCard() {
  const { t } = useTranslation()
  const [running, setRunning] = useState<SandboxScenario | null>(null)
  const [results, setResults] = useState<Partial<Record<SandboxScenario, SandboxDemoResult>>>({})
  const [error, setError] = useState<string | null>(null)

  const run = async (id: SandboxScenario) => {
    setRunning(id)
    setError(null)
    try {
      const result = await sandboxApi.demo(id)
      setResults((r) => ({ ...r, [id]: result }))
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || t('sandbox.failed'))
    } finally {
      setRunning(null)
    }
  }

  const runAll = async () => {
    for (const s of SCENARIOS) await run(s.id) // one warm sandbox: runs are serialized anyway
  }

  return (
    <Card>
      <CardHeader
        icon={<Play className="h-4 w-4" />}
        title={t('sandbox.demoTitle')}
        subtitle={t('sandbox.demoSubtitle')}
        actions={<Button size="sm" variant="primary" loading={running !== null} onClick={runAll}>{t('sandbox.runAll')}</Button>}
      />
      <CardBody className="space-y-3">
        {error && <ErrorBanner>{error}</ErrorBanner>}
        {SCENARIOS.map(({ id, expect }) => {
          const result = results[id]
          return (
            <div key={id} className="rounded-xl border border-line p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-ink">{t(`sandbox.sc_${id}`)}</p>
                  <p className="text-xs text-ink-subtle">{t(`sandbox.sc_${id}_help`)}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge tone={expect === 'allowed' ? 'success' : 'warning'}>{t(`sandbox.expect_${expect}`)}</Badge>
                  {result && (
                    <Badge tone={isolationHolds(result) ? 'success' : 'danger'}>
                      {isolationHolds(result) ? t('sandbox.verified') : t('sandbox.unexpected')}
                    </Badge>
                  )}
                  <Button size="sm" loading={running === id} disabled={running !== null} onClick={() => run(id)}
                    icon={<Play className="h-3.5 w-3.5" />}>{t('sandbox.run')}</Button>
                </div>
              </div>
              {result && <SandboxRun className="mt-3" code={result.code} result={result} />}
            </div>
          )
        })}
      </CardBody>
    </Card>
  )
}

export default function SandboxPage() {
  const { t } = useTranslation()
  const { data: info, loading, error, reload } = useResource(() => sandboxApi.info(), [])
  const gateway = info?.openshell

  return (
    <div className="space-y-5">
      <PageHeader icon={<Box className="h-5 w-5" />} title={t('sandbox.pageTitle')} subtitle={t('sandbox.pageSubtitle')} />
      {loading && <PageLoader />}
      {error && <ErrorBanner onRetry={reload} retryLabel={t('common.refresh')}>{t('sandbox.unavailable')}</ErrorBanner>}
      {info && (
        <>
          <Card>
            <CardHeader icon={<Cpu className="h-4 w-4" />} title={t('sandbox.statusTitle')} subtitle={t('sandbox.statusSubtitle')}
              actions={<Badge tone={gateway?.status === 'connected' ? 'success' : 'danger'} dot>{gateway?.status ?? '—'}</Badge>} />
            <CardBody className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <Field label={t('sandbox.gateway')}><span className="font-mono text-xs">{info.gateway}</span></Field>
              <Field label={t('sandbox.version')}>{gateway?.version ?? '—'}</Field>
              <Field label={t('sandbox.workspace')}>{info.workspace}</Field>
              <Field label={t('sandbox.warm')}>
                <span className="font-mono text-xs">{info.warm_sandbox ?? t('sandbox.none')}</span>
              </Field>
              <Field label={t('sandbox.image')} className="sm:col-span-2 lg:col-span-4"><span className="font-mono text-xs">{info.image}</span></Field>
            </CardBody>
            <p className="border-t border-line px-5 py-3 text-xs leading-relaxed text-ink-muted">{t('sandbox.howItWorks')}</p>
          </Card>
          <PolicyCard info={info} />
          <DemoCard />
        </>
      )}
    </div>
  )
}
