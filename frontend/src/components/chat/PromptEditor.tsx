import { useEffect, useState } from 'react'
import { RotateCcw, Save } from 'lucide-react'
import { useTranslation } from '../../i18n/LanguageContext'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { Spinner } from '../ui/Feedback'
import { Modal } from '../ui/Modal'

interface PromptEditorProps {
  open: boolean
  onClose: () => void
  prompt: string | null
  isCustom: boolean
  loading: boolean
  onSave: (text: string) => Promise<boolean>
  onReset: () => Promise<boolean>
}

/** Session system prompt (overrides the MLflow Prompt Registry version for this session). */
export function PromptEditor({ open, onClose, prompt, isCustom, loading, onSave, onReset }: PromptEditorProps) {
  const { t } = useTranslation()
  const [draft, setDraft] = useState('')
  const [status, setStatus] = useState<string | null>(null)

  useEffect(() => {
    if (prompt !== null) setDraft(prompt)
  }, [prompt])

  const flash = (msg: string) => {
    setStatus(msg)
    window.setTimeout(() => setStatus(null), 2000)
  }

  return (
    <Modal
      open={open}
      wide
      onClose={onClose}
      title={(
        <span className="flex items-center gap-2">
          {t('prompt.systemPrompt')}
          <Badge tone={isCustom ? 'violet' : 'neutral'}>{isCustom ? t('prompt.customBadge') : t('prompt.defaultBadge')}</Badge>
          {status && <span className="text-xs font-normal text-emerald-600">{status}</span>}
        </span>
      )}
      footer={(
        <>
          {isCustom && (
            <Button icon={<RotateCcw className="h-4 w-4" />} onClick={async () => (await onReset()) && flash(t('prompt.resetDone'))}>
              {t('prompt.reset')}
            </Button>
          )}
          <Button
            variant="primary"
            icon={<Save className="h-4 w-4" />}
            disabled={prompt === null || draft === prompt}
            onClick={async () => (await onSave(draft)) && flash(t('prompt.saved'))}
          >
            {t('prompt.save')}
          </Button>
        </>
      )}
    >
      <p className="mb-3 text-xs text-ink-muted">{t('conv.promptHelp')}</p>
      {loading ? (
        <div className="flex h-40 items-center justify-center"><Spinner /></div>
      ) : (
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          spellCheck={false}
          className="input h-80 resize-y font-mono text-xs leading-relaxed"
        />
      )}
    </Modal>
  )
}
