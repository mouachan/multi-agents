import { CheckCircle2, Loader2, Wrench, XCircle } from 'lucide-react'
import { useToolDisplay } from '../../hooks/useToolDisplay'
import { useTranslation } from '../../i18n/LanguageContext'
import { cn } from '../../lib/cn'
import type { ToolCallInfo } from '../../types/chat'

/** Live MCP tool calls of one assistant turn. */
export function ToolChips({ toolCalls }: { toolCalls: ToolCallInfo[] }) {
  const { locale } = useTranslation()
  const { getToolLabel } = useToolDisplay()
  if (!toolCalls.length) return null
  return (
    <div className="mb-2 flex flex-wrap gap-1.5">
      {toolCalls.map((tc, i) => {
        const running = tc.status === 'running' || tc.status === 'in_progress'
        const failed = tc.status === 'error' || tc.status === 'failed'
        return (
          <span
            key={`${tc.name}-${i}`}
            title={tc.server_label ? `${tc.name} · ${tc.server_label}` : tc.name}
            className={cn(
              'chip animate-fade-in py-0.5 text-[11px]',
              running && 'border-sky-500/30 bg-sky-500/5 text-sky-700 dark:text-sky-300',
              failed && 'border-red-500/30 bg-red-500/5 text-red-700 dark:text-red-300',
            )}
          >
            {running ? <Loader2 className="h-3 w-3 animate-spin" />
              : failed ? <XCircle className="h-3 w-3" />
                : <CheckCircle2 className="h-3 w-3 text-emerald-500" />}
            <Wrench className="h-3 w-3 opacity-50" />
            {getToolLabel(tc.name, locale)}
          </span>
        )
      })}
    </div>
  )
}
