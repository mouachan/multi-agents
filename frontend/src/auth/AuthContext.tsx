import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { ShieldOff } from 'lucide-react'
import { EmptyState, ErrorBanner, PageLoader } from '../components/ui/Feedback'
import { useTranslation } from '../i18n/LanguageContext'
import { http } from '../services/http'

/** Business domain = one A2A agent (claims-agent, tenders-agent, postal-agent). */
export type Domain = 'claims' | 'tenders' | 'postal'

/**
 * The signed-in user, from GET /auth/me. The backend validates the OpenShift token forwarded
 * by the OAuth proxy and derives the domains from OpenShift RBAC (backend/app/core/auth.py).
 */
export interface AuthUser {
  username: string
  groups: string[]
  profiles: string[]
  domains: Domain[]
  admin: boolean
  /** false on the local stack: no OpenShift login, every user is an administrator */
  authEnabled: boolean
}

interface AuthState {
  user: AuthUser
  can: (domain: Domain) => boolean
}

const AuthContext = createContext<AuthState | null>(null)

/** OAuth proxy sign-out: ends the session cookie, then OpenShift asks for a new login */
export const SIGN_OUT_URL = '/oauth/sign_out'

export function AuthProvider({ children }: { children: ReactNode }) {
  const { t } = useTranslation()
  const [user, setUser] = useState<AuthUser | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    http.get<AuthUser>('/auth/me')
      .then(({ data }) => setUser(data))
      .catch((err) => setError(err?.response?.data?.detail || err?.message || t('auth.error')))
  }, [t])

  if (error) return <div className="p-6"><ErrorBanner>{error}</ErrorBanner></div>
  if (!user) return <PageLoader />
  return <AuthContext.Provider value={{ user, can: (d) => user.domains.includes(d) }}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthState {
  const state = useContext(AuthContext)
  if (!state) throw new Error('useAuth outside AuthProvider')
  return state
}

function Forbidden() {
  const { t } = useTranslation()
  return <EmptyState icon={<ShieldOff className="h-5 w-5" />} title={t('auth.forbiddenTitle')} description={t('auth.forbiddenText')} className="py-24" />
}

/** Renders the page only for users who may use the domain's agent (or the admins). */
export function Guard({ domain, admin, children }: { domain?: Domain; admin?: boolean; children: ReactNode }) {
  const { user, can } = useAuth()
  const allowed = (domain ? can(domain) : true) && (admin ? user.admin : true)
  return allowed ? <>{children}</> : <Forbidden />
}
