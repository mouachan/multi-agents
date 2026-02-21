import { useState } from 'react'
import type { ToolCallInfo } from '../../types/chat'
import { useToolDisplay } from '../../hooks/useToolDisplay'
import { useTranslation } from '../../i18n/LanguageContext'

interface ToolCallStepsProps {
  toolCalls: ToolCallInfo[]
}

const SERVER_COLORS: Record<string, string> = {
  blue: 'text-blue-600 bg-blue-50',
  purple: 'text-purple-600 bg-purple-50',
  emerald: 'text-emerald-600 bg-emerald-50',
  amber: 'text-amber-600 bg-amber-50',
}

export default function ToolCallSteps({ toolCalls }: ToolCallStepsProps) {
  const [expanded, setExpanded] = useState(false)
  const [expandedOutputs, setExpandedOutputs] = useState<Set<number>>(new Set())
  const { getToolLabel, getToolCategoryInfo } = useToolDisplay()
  const { locale, t } = useTranslation()

  if (toolCalls.length === 0) return null

  const toggleOutput = (idx: number) => {
    setExpandedOutputs((prev) => {
      const next = new Set(prev)
      if (next.has(idx)) next.delete(idx)
      else next.add(idx)
      return next
    })
  }

  const count = toolCalls.length
  const summary = `${count} ${count > 1 ? t('toolCalls.toolsCalled') : t('toolCalls.toolCalled')}`

  return (
    <div className="mb-1.5 ml-1">
      {/* Collapsed / Expanded toggle */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-700 transition-colors"
      >
        <span className="text-[10px]">{expanded ? '\u25BC' : '\u25B6'}</span>
        <span className="font-medium">{summary}</span>
      </button>

      {expanded && (
        <div className="mt-1.5 space-y-1.5 border-l-2 border-gray-200 pl-3">
          {toolCalls.map((tc, idx) => {
            const isError = tc.status === 'error'
            const categoryInfo = getToolCategoryInfo(tc.name, locale)
            const categoryColorClass = categoryInfo
              ? SERVER_COLORS[categoryInfo.color] || 'text-gray-600 bg-gray-50'
              : null
            const hasOutput = tc.output || tc.error
            const isOutputExpanded = expandedOutputs.has(idx)

            return (
              <div key={idx} className="text-xs">
                {/* Tool line */}
                <div className="flex items-center gap-2">
                  {/* Status icon */}
                  <span className={isError ? 'text-red-500' : 'text-green-500'}>
                    {isError ? '\u2717' : '\u2713'}
                  </span>

                  {/* Tool name */}
                  <span className={`font-medium ${isError ? 'text-red-700' : 'text-gray-700'}`}>
                    {getToolLabel(tc.name, locale)}
                  </span>

                  {/* Category badge (OCR / RAG / Database) */}
                  {categoryInfo && categoryColorClass && (
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${categoryColorClass}`}>
                      {categoryInfo.label}
                    </span>
                  )}
                </div>

                {/* Expandable output */}
                {hasOutput && (
                  <div className="ml-5 mt-0.5">
                    <button
                      onClick={() => toggleOutput(idx)}
                      className={`text-[10px] font-medium ${
                        isError ? 'text-red-500 hover:text-red-700' : 'text-gray-400 hover:text-gray-600'
                      } transition-colors`}
                    >
                      {isOutputExpanded
                        ? (isError ? t('toolCalls.hideError') : t('toolCalls.hideResult'))
                        : (isError ? t('toolCalls.viewError') : t('toolCalls.viewResult'))
                      }
                    </button>

                    {isOutputExpanded && (
                      <pre
                        className={`mt-1 p-2 rounded text-[10px] leading-relaxed max-h-40 overflow-auto whitespace-pre-wrap break-all ${
                          isError
                            ? 'bg-red-50 text-red-800 border border-red-200'
                            : 'bg-gray-50 text-gray-700 border border-gray-200'
                        }`}
                      >
                        {isError ? tc.error : tc.output}
                      </pre>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
