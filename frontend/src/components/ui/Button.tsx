import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react'
import { Loader2 } from 'lucide-react'
import { cn } from '../../lib/cn'

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'soft'
type Size = 'xs' | 'sm' | 'md'

const VARIANTS: Record<Variant, string> = {
  primary: 'bg-brand-600 text-white shadow-sm hover:bg-brand-700 focus-visible:ring-brand-500/30',
  secondary: 'border border-line bg-surface text-ink hover:bg-surface-muted focus-visible:ring-brand-500/20',
  ghost: 'text-ink-muted hover:bg-surface-muted hover:text-ink focus-visible:ring-brand-500/20',
  danger: 'bg-red-600 text-white shadow-sm hover:bg-red-700 focus-visible:ring-red-500/30',
  soft: 'bg-brand-500/10 text-brand-700 hover:bg-brand-500/15 dark:text-brand-300 focus-visible:ring-brand-500/20',
}

const SIZES: Record<Size, string> = {
  xs: 'h-7 gap-1 rounded-lg px-2 text-xs',
  sm: 'h-8 gap-1.5 rounded-lg px-3 text-sm',
  md: 'h-10 gap-2 rounded-xl px-4 text-sm',
}

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  icon?: ReactNode
  loading?: boolean
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = 'secondary', size = 'sm', icon, loading, className, children, disabled, ...props },
  ref,
) {
  return (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={cn(
        'inline-flex shrink-0 items-center justify-center font-medium transition-colors focus-visible:outline-none focus-visible:ring-4 disabled:cursor-not-allowed disabled:opacity-50',
        VARIANTS[variant], SIZES[size], className,
      )}
      {...props}
    >
      {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : icon}
      {children}
    </button>
  )
})

export function IconButton({ className, label, ...props }: ButtonProps & { label: string }) {
  return (
    <Button
      variant="ghost"
      size="sm"
      aria-label={label}
      title={label}
      className={cn('w-8 px-0', className)}
      {...props}
    />
  )
}
