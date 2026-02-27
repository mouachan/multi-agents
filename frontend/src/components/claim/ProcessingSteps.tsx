/**
 * ProcessingSteps Component - Displays claim/tender processing steps and agent conversation
 */

import type { Claim, ClaimStatusResponse, ProcessingStepLog } from '../../types'
import StepOutputDisplay, { STEP_LABELS } from './StepOutputDisplay'
import { useTranslation } from '../../i18n/LanguageContext'

interface ProcessingStepsProps {
  claim: Claim
  status: ClaimStatusResponse | null
  logs: ProcessingStepLog[]
}

/** Step number badge */
function StepBadge({ index, status }: { index: number; status: string }) {
  const isCompleted = status === 'completed'
  const isFailed = status === 'failed'

  return (
    <div
      className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
        isCompleted
          ? 'bg-green-100 text-green-700 ring-2 ring-green-500'
          : isFailed
          ? 'bg-red-100 text-red-700 ring-2 ring-red-500'
          : 'bg-gray-100 text-gray-500 ring-2 ring-gray-300'
      }`}
    >
      {isCompleted ? (
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      ) : isFailed ? (
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      ) : (
        index + 1
      )}
    </div>
  )
}

/** Get human-readable step label */
function getStepLabel(stepName: string): string {
  return STEP_LABELS[stepName]?.label || stepName.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

export default function ProcessingSteps({ claim, status, logs }: ProcessingStepsProps) {
  const { t } = useTranslation()

  if (!['processing', 'completed', 'manual_review', 'failed'].includes(claim.status) && logs.length === 0) {
    return null
  }

  const steps = status?.processing_steps && status.processing_steps.length > 0
    ? status.processing_steps
    : logs

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-xl font-bold text-gray-900 mb-4">{t('processingSteps.title')}</h3>

      {/* Progress Bar */}
      {status && claim.status === 'processing' && (
        <div className="mb-4 p-4 bg-blue-50 rounded-lg">
          <p className="text-sm text-gray-600">{t('processingSteps.overallProgress')}</p>
          <div className="mt-2">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${status.progress_percentage || 0}%` }}
              ></div>
            </div>
            <p className="text-sm text-gray-600 mt-1">{status.progress_percentage || 0}% {t('processingSteps.complete')}</p>
          </div>
        </div>
      )}

      {/* Processing Steps Timeline */}
      <div className="space-y-0">
        {steps.map((step: ProcessingStepLog, index: number) => (
          <div key={index} className="relative">
            {/* Connector line */}
            {index < steps.length - 1 && (
              <div className="absolute left-4 top-12 bottom-0 w-px bg-gray-200" />
            )}

            <div className="flex gap-4 pb-6">
              <StepBadge index={index} status={step.status} />

              <div className="flex-1 min-w-0">
                {/* Step header */}
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-gray-900">
                      {getStepLabel(step.step_name)}
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {t('processingSteps.agent')}: {step.agent_name}
                      {step.duration_ms !== null && step.duration_ms !== undefined && (
                        <span className="ml-2 text-blue-600 font-medium">
                          {step.duration_ms < 1000
                            ? `${step.duration_ms}ms`
                            : `${(step.duration_ms / 1000).toFixed(2)}s`}
                        </span>
                      )}
                    </p>
                  </div>
                  <span
                    className={`text-xs px-2 py-1 rounded-full font-medium ${
                      step.status === 'completed'
                        ? 'bg-green-100 text-green-700'
                        : step.status === 'failed'
                        ? 'bg-red-100 text-red-700'
                        : step.status === 'in_progress'
                        ? 'bg-blue-100 text-blue-700'
                        : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    {step.status === 'completed' ? t('common.completed') :
                     step.status === 'failed' ? t('common.failed') :
                     step.status === 'in_progress' ? t('common.processing') :
                     step.status}
                  </span>
                </div>

                {/* Step output */}
                {step.output_data && (
                  <StepOutputDisplay stepName={step.step_name} outputData={step.output_data} />
                )}

                {/* Error message */}
                {step.error_message && (
                  <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                    {step.error_message}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}

        {steps.length === 0 && (
          <div className="p-4 bg-gray-50 rounded-lg text-center">
            <p className="text-gray-600">{t('processingSteps.waitingForProcessing')}</p>
          </div>
        )}
      </div>

      {/* Q&A Conversation */}
      {claim.agent_logs && claim.agent_logs.length > 0 && (
        <div className="mt-6 border-t pt-6">
          <h4 className="text-lg font-bold text-gray-900 mb-4">{t('processingSteps.reviewerConversation')}</h4>
          <div className="space-y-3">
            {claim.agent_logs.map((log, index) => {
              if (log.type === 'reviewer_question') {
                const answerLog = claim.agent_logs?.[index + 1]
                const hasAnswer = answerLog && answerLog.type === 'agent_answer'

                return (
                  <div key={index} className="ml-4">
                    {/* Question */}
                    <div className="p-3 bg-blue-50 rounded-lg border-l-4 border-blue-500">
                      <div className="text-xs text-gray-500">
                        <strong>{log.reviewer_name || t('processingSteps.reviewer')}</strong> · {new Date(log.timestamp).toLocaleString()}
                      </div>
                      <div className="mt-1 font-semibold text-blue-900">{log.message}</div>
                    </div>
                    {/* Answer */}
                    {hasAnswer && (
                      <div className="p-3 bg-purple-50 rounded-lg border-l-4 border-purple-500 mt-2 ml-4">
                        <div className="text-xs text-purple-700 font-semibold mb-1">{t('processingSteps.agentResponse')}</div>
                        {answerLog.message.length > 300 ? (
                          <details>
                            <summary className="text-xs text-purple-600 cursor-pointer hover:text-purple-800 font-medium mb-1">
                              {t('processingSteps.viewResponse')} ({answerLog.message.length} {t('processingSteps.characters')})
                            </summary>
                            <div className="text-sm text-gray-800 whitespace-pre-wrap mt-2">{answerLog.message}</div>
                          </details>
                        ) : (
                          <div className="text-sm text-gray-800 whitespace-pre-wrap">{answerLog.message}</div>
                        )}
                      </div>
                    )}
                  </div>
                )
              }
              return null
            })}
          </div>
        </div>
      )}
    </div>
  )
}
