import { agentVisual } from '../../lib/agents'
import { cn } from '../../lib/cn'

export function AgentAvatar({ agentId, size = 'md', className }: { agentId?: string | null; size?: 'sm' | 'md' | 'lg'; className?: string }) {
  const v = agentVisual(agentId)
  const Icon = v.icon
  const dims = size === 'sm' ? 'h-6 w-6 rounded-lg' : size === 'lg' ? 'h-10 w-10 rounded-xl' : 'h-8 w-8 rounded-xl'
  const icon = size === 'sm' ? 'h-3.5 w-3.5' : size === 'lg' ? 'h-5 w-5' : 'h-4 w-4'
  return (
    <div className={cn('flex shrink-0 items-center justify-center shadow-sm', dims, v.accent.solid, className)}>
      <Icon className={icon} />
    </div>
  )
}
