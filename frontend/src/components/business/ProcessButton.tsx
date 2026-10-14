import { useState } from 'react'
import { Play } from 'lucide-react'
import { useTranslation } from '../../i18n/LanguageContext'
import { Button } from '../ui/Button'

/** Starts the agent processing of a pending (or failed) item; the page then polls its status. */
export function ProcessButton({ onProcess, onStarted, disabled }: {
  onProcess: () => Promise<unknown>
  onStarted: () => void
  disabled?: boolean
}) {
  const { t } = useTranslation()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const run = async () => {
    setBusy(true)
    setError(null)
    try {
      await onProcess()
      onStarted()
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || t('ui.processFailed'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <Button variant="primary" icon={<Play className="h-4 w-4" />} loading={busy} disabled={disabled} onClick={run}>
        {busy ? t('ui.processing') : t('ui.process')}
      </Button>
      {error && <span className="max-w-xs text-right text-[11px] text-red-600">{error}</span>}
    </div>
  )
}
