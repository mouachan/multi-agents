interface PIIBadgeProps {
  isRedacted?: boolean
  fieldName?: string
}

export default function PIIBadge({ isRedacted = true, fieldName }: PIIBadgeProps) {
  if (!isRedacted) return null

  return (
    <span
      className="inline-flex items-center gap-1 text-xs bg-yellow-100 text-yellow-800 border border-yellow-200 rounded px-2 py-0.5 ml-2"
      title={`Donnee masquee${fieldName ? ` (${fieldName})` : ''}`}
    >
      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
      </svg>
      PII
    </span>
  )
}
