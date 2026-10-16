import { useState, type FormEvent } from 'react'
import { Gauge, RefreshCw, ShieldCheck, UserCog, UserPlus, Wrench } from 'lucide-react'
import { useAuth } from '../../auth/AuthContext'
import { useResource } from '../../hooks/useResource'
import { useToolDisplay } from '../../hooks/useToolDisplay'
import { useTranslation } from '../../i18n/LanguageContext'
import { agentVisual } from '../../lib/agents'
import { cn } from '../../lib/cn'
import { adminApi, type AccessProfile, type ManagedUser } from '../../services/api'
import { Badge } from '../ui/Badge'
import { Button, IconButton } from '../ui/Button'
import { Card, CardHeader } from '../ui/Card'
import { ErrorBanner, Spinner } from '../ui/Feedback'

/** Agent giving its colour to a domain (the postal profiles share one A2A agent) */
const DOMAIN_AGENT: Record<string, string> = { claims: 'claims', tenders: 'tenders', postal: 'courrier_suivi' }

function upsert(users: ManagedUser[], user: ManagedUser): ManagedUser[] {
  return [...users.filter((u) => u.username !== user.username), user].sort((a, b) => a.username.localeCompare(b.username))
}

function ProfileLegend({ profile }: { profile: AccessProfile }) {
  const { t, locale } = useTranslation()
  const { getToolLabel } = useToolDisplay()
  const quota = profile.tokenQuota
  return (
    <div className="rounded-xl border border-line px-3 py-2">
      <div className="flex items-center gap-1.5 text-sm font-semibold text-ink">
        {profile.admin && <ShieldCheck className="h-3.5 w-3.5 text-brand-500" />}
        {profile.displayName}
      </div>
      <p className="font-mono text-[10px] text-ink-subtle">{profile.group}</p>
      <div className="mt-1.5 flex flex-wrap gap-1">
        {profile.agents.map((domain) => (
          <span key={domain} className={cn('rounded-md px-1.5 py-0.5 text-[10px] font-medium', agentVisual(DOMAIN_AGENT[domain]).accent.soft)}>
            {t(`nav.${domain}`)}
          </span>
        ))}
        {profile.admin && <Badge tone="brand">{t('nav.admin')}</Badge>}
      </div>
      <details className="mt-1.5 text-[11px] text-ink-muted">
        <summary className="flex cursor-pointer items-center gap-1">
          <Wrench className="h-3 w-3" /> {t('adm.accessTools').replace('{count}', String(profile.tools.length))}
        </summary>
        <p className="mt-1 leading-relaxed">{profile.tools.map((name) => getToolLabel(name, locale)).join(' · ') || '—'}</p>
      </details>
      <p className="mt-1 flex items-center gap-1 text-[11px] text-ink-muted" title={t('adm.accessQuotaHint')}>
        <Gauge className="h-3 w-3" />
        {quota
          ? t('adm.accessQuota').replace('{limit}', quota.limit.toLocaleString(locale)).replace('{window}', quota.window)
          : t('adm.accessQuotaDefault')}
      </p>
    </div>
  )
}

/**
 * Users and their access profiles. A profile is an OpenShift group: a checked box makes the user
 * a member (backend/app/services/access_profiles.py) and OpenShift RBAC grants the profile's
 * agents and MCP tools, within a few seconds (OpenShift token cache).
 */
export function UserProfiles() {
  const { t } = useTranslation()
  const { user: me } = useAuth()
  const { data, loading, error, reload, setData } = useResource(() => adminApi.users(), [])
  const [saving, setSaving] = useState<string | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [newUser, setNewUser] = useState('')
  const profiles = data?.profiles ?? []
  const isAdminProfile = (id: string) => profiles.some((p) => p.id === id && p.admin)

  const save = async (username: string, wanted: string[]) => {
    setSaving(username)
    setSaveError(null)
    try {
      const updated = await adminApi.setProfiles(username, wanted)
      setData((d) => d && { ...d, users: upsert(d.users, updated) })
    } catch (err: any) {
      setSaveError(err?.response?.data?.detail || err?.message || t('adm.accessSaveFailed'))
    } finally {
      setSaving(null)
    }
  }

  const toggle = (u: ManagedUser, id: string) =>
    save(u.username, u.profiles.includes(id) ? u.profiles.filter((p) => p !== id) : [...u.profiles, id])

  /** Your own last administrator profile cannot be removed (no lock-out) */
  const locked = (u: ManagedUser, id: string) =>
    u.username === me.username && isAdminProfile(id) && u.profiles.filter(isAdminProfile).length === 1 && u.profiles.includes(id)

  const add = (e: FormEvent) => {
    e.preventDefault()
    const username = newUser.trim()
    if (!username || !data) return
    if (!data.users.some((u) => u.username === username)) setData({ ...data, users: upsert(data.users, { username, profiles: [] }) })
    setNewUser('')
  }

  return (
    <Card>
      <CardHeader
        icon={<UserCog className="h-4 w-4" />}
        title={t('adm.accessTitle')}
        subtitle={t('adm.accessSubtitle')}
        actions={<IconButton label={t('common.refresh')} icon={<RefreshCw className="h-4 w-4" />} onClick={reload} />}
      />
      <div className="space-y-4 p-5">
        {error && <ErrorBanner onRetry={reload} retryLabel={t('ui.retry')}>{error}</ErrorBanner>}
        {saveError && <ErrorBanner>{saveError}</ErrorBanner>}

        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          {profiles.map((p) => <ProfileLegend key={p.id} profile={p} />)}
        </div>

        <form onSubmit={add} className="flex gap-2">
          <input className="input" value={newUser} onChange={(e) => setNewUser(e.target.value)} placeholder={t('adm.accessAddPlaceholder')} />
          <Button type="submit" variant="soft" size="md" icon={<UserPlus className="h-4 w-4" />} disabled={!newUser.trim()}>
            {t('adm.accessAdd')}
          </Button>
        </form>

        <div className="overflow-x-auto rounded-xl border border-line">
          <table className="w-full text-sm">
            <thead className="bg-surface-muted text-left">
              <tr>
                <th className="label px-3 py-2">{t('adm.accessUser')}</th>
                {profiles.map((p) => <th key={p.id} className="label px-3 py-2 text-center">{p.displayName}</th>)}
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {loading && (
                <tr><td colSpan={profiles.length + 1} className="px-3 py-6 text-center"><Spinner className="mx-auto" /></td></tr>
              )}
              {data?.users.map((u) => (
                <tr key={u.username} className="hover:bg-surface-muted/50">
                  <td className="px-3 py-2">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-ink">{u.username}</span>
                      {u.username === me.username && <Badge tone="brand">{t('adm.accessYou')}</Badge>}
                      {u.profiles.length === 0 && <Badge>{t('auth.noProfile')}</Badge>}
                      {saving === u.username && <Spinner className="h-3.5 w-3.5" />}
                    </div>
                    {u.fullName && <p className="text-xs text-ink-subtle">{u.fullName}</p>}
                  </td>
                  {profiles.map((p) => (
                    <td key={p.id} className="px-3 py-2 text-center">
                      <input
                        type="checkbox"
                        aria-label={`${u.username} — ${p.displayName}`}
                        title={locked(u, p.id) ? t('adm.accessOwnAdmin') : undefined}
                        className="h-4 w-4 cursor-pointer accent-brand-600 disabled:cursor-not-allowed"
                        checked={u.profiles.includes(p.id)}
                        disabled={saving !== null || !p.exists || locked(u, p.id)}
                        onChange={() => toggle(u, p.id)}
                      />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-ink-subtle">{t('adm.accessNote')}</p>
      </div>
    </Card>
  )
}
