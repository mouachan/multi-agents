import { useEffect, useRef, useState } from 'react'
import { ArrowUp, Square } from 'lucide-react'
import { useTranslation } from '../../i18n/LanguageContext'
import { cn } from '../../lib/cn'

interface ComposerProps {
  onSend: (text: string) => void
  onStop: () => void
  sending: boolean
  disabled?: boolean
  placeholder: string
}

export function Composer({ onSend, onStop, sending, disabled, placeholder }: ComposerProps) {
  const { t } = useTranslation()
  const [value, setValue] = useState('')
  const ref = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 180)}px`
  }, [value])

  useEffect(() => {
    if (!sending) ref.current?.focus()
  }, [sending])

  const submit = () => {
    const text = value.trim()
    if (!text || sending || disabled) return
    onSend(text)
    setValue('')
  }

  return (
    <div className="border-t border-line bg-surface/80 px-4 py-3 backdrop-blur">
      <div
        className={cn(
          'mx-auto flex max-w-3xl items-end gap-2 rounded-2xl border border-line bg-surface p-2 shadow-card transition-shadow',
          'focus-within:border-brand-400 focus-within:ring-4 focus-within:ring-brand-500/10',
        )}
      >
        <textarea
          ref={ref}
          rows={1}
          value={value}
          disabled={disabled}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
              e.preventDefault()
              submit()
            }
          }}
          placeholder={placeholder}
          className="max-h-[180px] min-h-[36px] flex-1 resize-none bg-transparent px-2 py-1.5 text-sm text-ink placeholder:text-ink-subtle focus:outline-none"
        />
        {sending ? (
          <button
            onClick={onStop}
            title={t('conv.stop')}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-ink text-surface transition-opacity hover:opacity-80"
          >
            <Square className="h-3.5 w-3.5 fill-current" />
          </button>
        ) : (
          <button
            onClick={submit}
            disabled={!value.trim() || disabled}
            title={t('conv.send')}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-600 text-white shadow-sm transition-colors hover:bg-brand-700 disabled:opacity-40"
          >
            <ArrowUp className="h-4 w-4" />
          </button>
        )}
      </div>
      <p className="mx-auto mt-1.5 max-w-3xl px-1 text-[10px] text-ink-subtle">{t('conv.hint')}</p>
    </div>
  )
}
