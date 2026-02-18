/**
 * ProcessingSteps Component - Displays claim processing steps and agent conversation
 */

import type { Claim, ClaimStatusResponse, ProcessingStepLog } from '../../types'
import StepOutputDisplay from './StepOutputDisplay'

interface ProcessingStepsProps {
  claim: Claim
  status: ClaimStatusResponse | null
  logs: ProcessingStepLog[]
}

export default function ProcessingSteps({ claim, status, logs }: ProcessingStepsProps) {
  const getStepStatusIcon = (stepStatus: string) => {
    if (stepStatus === 'completed') {
      return (
        <svg className="h-6 w-6 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      )
    }
    return (
      <svg className="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    )
  }

  if (!['processing', 'completed', 'manual_review', 'failed'].includes(claim.status) && logs.length === 0) {
    return null
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-xl font-bold text-gray-900 mb-4">Processing Steps</h3>

      {/* Progress Bar */}
      {status && claim.status === 'processing' && (
        <div className="mb-4 p-4 bg-blue-50 rounded-lg">
          <p className="text-sm text-gray-600">Overall Progress</p>
          <div className="mt-2">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${status.progress_percentage || 0}%` }}
              ></div>
            </div>
            <p className="text-sm text-gray-600 mt-1">{status.progress_percentage || 0}% complete</p>
          </div>
        </div>
      )}

      {/* Processing Steps */}
      <div className="space-y-4">
        {(status?.processing_steps && status.processing_steps.length > 0
          ? status.processing_steps
          : logs
        ).map((step: ProcessingStepLog, index: number) => (
          <div key={index} className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-start">
              <div className="flex-shrink-0 mt-1">{getStepStatusIcon(step.status)}</div>
              <div className="ml-3 flex-1">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold text-gray-900">{step.step_name}</p>
                  <span
                    className={`text-xs px-2 py-1 rounded ${
                      step.status === 'completed'
                        ? 'bg-green-100 text-green-800'
                        : step.status === 'failed'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {step.status}
                  </span>
                </div>
                <div className="flex items-center gap-3 mt-1">
                  <p className="text-xs text-gray-500">Agent: {step.agent_name}</p>
                  {step.duration_ms !== null && step.duration_ms !== undefined && (
                    <p className="text-xs text-blue-600 font-medium">
                      ⏱️ {step.duration_ms < 1000
                        ? `${step.duration_ms}ms`
                        : `${(step.duration_ms / 1000).toFixed(2)}s`}
                    </p>
                  )}
                </div>

                {/* Pretty output display */}
                {step.output_data && (
                  <StepOutputDisplay stepName={step.step_name} outputData={step.output_data} />
                )}
              </div>
            </div>
          </div>
        ))}

        {logs.length === 0 && (!status?.processing_steps || status.processing_steps.length === 0) && (
          <div className="p-4 bg-gray-50 rounded-lg text-center">
            <p className="text-gray-600">Waiting for processing to start...</p>
          </div>
        )}
      </div>

      {/* Q&A Conversation */}
      {claim.agent_logs && claim.agent_logs.length > 0 && (
        <div className="mt-6 border-t pt-6">
          <h4 className="text-lg font-bold text-gray-900 mb-4">💬 Reviewer-Agent Conversation</h4>
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
                        <strong>{log.reviewer_name || 'Reviewer'}</strong> · {new Date(log.timestamp).toLocaleString()}
                      </div>
                      <div className="mt-1 font-semibold text-blue-900">💬 {log.message}</div>
                    </div>
                    {/* Answer */}
                    {hasAnswer && (
                      <div className="p-3 bg-purple-50 rounded-lg border-l-4 border-purple-500 mt-2 ml-4">
                        <div className="text-xs text-purple-700 font-semibold mb-1">🤖 Agent Response</div>
                        {answerLog.message.length > 300 ? (
                          <details>
                            <summary className="text-xs text-purple-600 cursor-pointer hover:text-purple-800 font-medium mb-1">
                              View response ({answerLog.message.length} characters)
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
