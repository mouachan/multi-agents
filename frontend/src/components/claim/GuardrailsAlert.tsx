import { useEffect, useState } from 'react'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

interface GuardrailsDetection {
  id: string
  detection_type: string
  severity: string
  action_taken: string
  detected_at: string
  record_metadata: Record<string, any>
}

interface GuardrailsAlertProps {
  claimId: string
}

export default function GuardrailsAlert({ claimId }: GuardrailsAlertProps) {
  const [detections, setDetections] = useState<GuardrailsDetection[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchDetections = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/claims/${claimId}/guardrails`)
        if (response.ok) {
          const data = await response.json()
          if (data.total > 0) {
            setDetections(data.detections)
          }
        }
      } catch (error) {
        console.error('Error fetching guardrails detections:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchDetections()
  }, [claimId])

  if (loading || detections.length === 0) {
    return null
  }

  return (
    <div className="bg-orange-50 border-l-4 border-orange-400 p-4 rounded-lg">
      <div className="flex">
        <div className="flex-shrink-0">
          <svg className="h-5 w-5 text-orange-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <div className="ml-3">
          <h3 className="text-sm font-medium text-orange-800">
            PII Detected
          </h3>
          <div className="mt-2 text-sm text-orange-700">
            <p>
              {detections.length} sensitive data pattern(s) detected and flagged for review.
            </p>
            <details className="mt-2">
              <summary className="cursor-pointer font-medium hover:text-orange-900">
                View details
              </summary>
              <ul className="mt-2 space-y-3">
                {detections.map((detection) => (
                  <li key={detection.id} className="border-l-2 border-orange-300 pl-3">
                    <div className="font-medium capitalize text-orange-900">{detection.detection_type}</div>
                    <div className="text-xs mt-1 space-y-1">
                      <div>
                        <span className="font-semibold">Severity:</span> {detection.severity} |
                        <span className="font-semibold ml-2">Action:</span> {detection.action_taken}
                      </div>
                      {detection.record_metadata?.source_step && (
                        <div>
                          <span className="font-semibold">Source:</span> {detection.record_metadata.source_step}
                        </div>
                      )}
                      {detection.record_metadata?.detected_fields && detection.record_metadata.detected_fields.length > 0 && (
                        <div>
                          <span className="font-semibold">Detected:</span> {detection.record_metadata.detected_fields.join(', ')}
                        </div>
                      )}
                      {detection.record_metadata?.score && (
                        <div>
                          <span className="font-semibold">Confidence:</span> {(detection.record_metadata.score * 100).toFixed(0)}%
                        </div>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </details>
          </div>
        </div>
      </div>
    </div>
  )
}
