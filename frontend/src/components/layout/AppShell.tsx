import { useState, type ReactNode } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import {
  Box, Building2, ChevronsLeft, ChevronsRight, Cpu, LayoutDashboard, MessagesSquare, Moon, Package, Settings, ShieldCheck, Sun,
} from 'lucide-react'
import { useTranslation } from '../../i18n/LanguageContext'
import { cn } from '../../lib/cn'
import { usePlatform } from '../../theme/PlatformContext'
import { useTheme } from '../../theme/ThemeContext'

const NAV = [
  { to: '/', key: 'nav.dashboard', icon: LayoutDashboard, end: true },
  { to: '/chat', key: 'nav.chat', icon: MessagesSquare },
  { to: '/claims', key: 'nav.claims', icon: ShieldCheck },
  { to: '/tenders', key: 'nav.tenders', icon: Building2 },
  { to: '/postal', key: 'nav.postal', icon: Package },
  { to: '/sandbox', key: 'nav.sandbox', icon: Box },
  { to: '/admin', key: 'nav.admin', icon: Settings },
]

function Logo({ collapsed }: { collapsed: boolean }) {
  const { t } = useTranslation()
  return (
    <div className="flex items-center gap-2.5 px-1">
      <img src="/logo.svg" alt="" className="h-8 w-8 shrink-0 rounded-xl shadow-sm" />
      {!collapsed && (
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold tracking-tight text-ink">{t('nav.title')}</p>
          <p className="truncate text-[10px] text-ink-subtle">Red Hat OpenShift AI 3.5</p>
        </div>
      )}
    </div>
  )
}

export function AppShell({ children }: { children: ReactNode }) {
  const { t, locale, setLocale } = useTranslation()
  const { theme, toggleTheme } = useTheme()
  const { modelId } = usePlatform()
  const location = useLocation()
  const isChat = location.pathname.startsWith('/chat')
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem('nav-collapsed') === 'true')

  const toggleCollapsed = () => {
    setCollapsed((c) => {
      localStorage.setItem('nav-collapsed', String(!c))
      return !c
    })
  }

  return (
    <div className="flex h-full">
      {/* Sidebar */}
      <aside
        className={cn(
          'flex shrink-0 flex-col border-r border-line bg-surface transition-[width] duration-200',
          collapsed ? 'w-[60px]' : 'w-56',
        )}
      >
        <div className="flex h-14 items-center border-b border-line px-3">
          <Logo collapsed={collapsed} />
        </div>
        <nav className="flex-1 space-y-0.5 p-2">
          {NAV.map(({ to, key, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              title={collapsed ? t(key) : undefined}
              className={({ isActive }) => cn(
                'group flex items-center gap-3 rounded-xl px-2.5 py-2 text-sm font-medium transition-colors',
                isActive ? 'bg-brand-500/10 text-brand-700 dark:text-brand-300' : 'text-ink-muted hover:bg-surface-muted hover:text-ink',
              )}
            >
              <Icon className="h-[18px] w-[18px] shrink-0" />
              {!collapsed && <span className="truncate">{t(key)}</span>}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-line p-2">
          <button
            onClick={toggleCollapsed}
            className="flex w-full items-center gap-3 rounded-xl px-2.5 py-2 text-xs font-medium text-ink-subtle transition-colors hover:bg-surface-muted hover:text-ink"
            title={collapsed ? t('shell.expand') : t('shell.collapse')}
          >
            {collapsed ? <ChevronsRight className="h-4 w-4" /> : <ChevronsLeft className="h-4 w-4" />}
            {!collapsed && t('shell.collapse')}
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 shrink-0 items-center justify-between gap-3 border-b border-line bg-surface/80 px-4 backdrop-blur">
          <div className="flex min-w-0 items-center gap-2">
            <span className="hidden items-center gap-1.5 rounded-full border border-line bg-surface-muted px-2.5 py-1 text-[11px] font-medium text-ink-muted md:inline-flex">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              OGX · A2A · MCP · NeMo Guardrails · MLflow
            </span>
            {modelId && (
              <span
                className="inline-flex items-center gap-1.5 rounded-full bg-brand-500/10 px-2.5 py-1 text-[11px] font-semibold text-brand-700 dark:text-brand-300"
                title={t('shell.model')}
              >
                <Cpu className="h-3 w-3" /> {modelId}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <div className="flex rounded-lg border border-line bg-surface-muted p-0.5">
              {(['fr', 'en'] as const).map((l) => (
                <button
                  key={l}
                  onClick={() => setLocale(l)}
                  className={cn(
                    'rounded-md px-2 py-0.5 text-[11px] font-semibold uppercase transition-colors',
                    locale === l ? 'bg-surface text-ink shadow-sm' : 'text-ink-subtle hover:text-ink',
                  )}
                >
                  {l}
                </button>
              ))}
            </div>
            <button
              onClick={toggleTheme}
              title={theme === 'dark' ? t('shell.light') : t('shell.dark')}
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-line bg-surface text-ink-muted transition-colors hover:text-ink"
            >
              {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>
          </div>
        </header>

        {isChat ? (
          <main className="min-h-0 flex-1 overflow-hidden">{children}</main>
        ) : (
          <main className="min-h-0 flex-1 overflow-y-auto">
            <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">{children}</div>
          </main>
        )}
      </div>
    </div>
  )
}
