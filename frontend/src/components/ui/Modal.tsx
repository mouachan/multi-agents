import { useEffect, useRef, useState, type ReactNode } from 'react'
import { X } from 'lucide-react'
import { Button, IconButton } from './Button'

interface ModalProps {
  open: boolean
  title: ReactNode
  onClose: () => void
  children: ReactNode
  footer?: ReactNode
  wide?: boolean
}

export function Modal({ open, title, onClose, children, footer, wide }: ModalProps) {
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-slate-950/50 backdrop-blur-sm" onClick={onClose} />
      <div className={`card relative w-full animate-fade-in shadow-elevated ${wide ? 'max-w-3xl' : 'max-w-md'}`}>
        <div className="card-header">
          <h3 className="card-title">{title}</h3>
          <IconButton label="Close" icon={<X className="h-4 w-4" />} onClick={onClose} />
        </div>
        <div className="p-5">{children}</div>
        {footer && <div className="flex justify-end gap-2 border-t border-line px-5 py-3">{footer}</div>}
      </div>
    </div>
  )
}

export function ConfirmDialog({ open, title, message, confirmLabel, cancelLabel, danger, onConfirm, onCancel }: {
  open: boolean; title: ReactNode; message: ReactNode; confirmLabel: string; cancelLabel: string
  danger?: boolean; onConfirm: () => void; onCancel: () => void
}) {
  return (
    <Modal
      open={open}
      title={title}
      onClose={onCancel}
      footer={(
        <>
          <Button onClick={onCancel}>{cancelLabel}</Button>
          <Button variant={danger ? 'danger' : 'primary'} onClick={onConfirm}>{confirmLabel}</Button>
        </>
      )}
    >
      <p className="text-sm text-ink-muted">{message}</p>
    </Modal>
  )
}

export function PromptDialog({ open, title, label, initialValue, confirmLabel, cancelLabel, onSubmit, onCancel }: {
  open: boolean; title: ReactNode; label: string; initialValue: string; confirmLabel: string; cancelLabel: string
  onSubmit: (value: string) => void; onCancel: () => void
}) {
  const [value, setValue] = useState(initialValue)
  const inputRef = useRef<HTMLInputElement>(null)
  useEffect(() => {
    if (open) {
      setValue(initialValue)
      setTimeout(() => inputRef.current?.select(), 0)
    }
  }, [open, initialValue])

  return (
    <Modal
      open={open}
      title={title}
      onClose={onCancel}
      footer={(
        <>
          <Button onClick={onCancel}>{cancelLabel}</Button>
          <Button variant="primary" onClick={() => onSubmit(value.trim())} disabled={!value.trim()}>{confirmLabel}</Button>
        </>
      )}
    >
      <label className="label mb-1.5 block">{label}</label>
      <input
        ref={inputRef}
        className="input"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && value.trim() && onSubmit(value.trim())}
      />
    </Modal>
  )
}
