/**
 * ClaimActions Component - Process claim button
 */

import { useState } from 'react'
import type { Claim } from '../../types'
import { claimService } from '../../services/claimService'

interface ClaimActionsProps {
  claim: Claim
  onProcessStart?: () => void
}

export default function ClaimActions({ claim, onProcessStart }: ClaimActionsProps) {
  const [processing, setProcessing] = useState(false)

  const handleProcessClaim = async () => {
    try {
      setProcessing(true)
      await claimService.processClaim(claim.id, 'standard')
      onProcessStart?.()
    } catch (error) {
      console.error('Error processing claim:', error)
      alert('Failed to process claim')
    } finally {
      setProcessing(false)
    }
  }

  if (!claimService.canProcess(claim)) {
    return null
  }

  return (
    <div className="mt-6">
      <button
        onClick={handleProcessClaim}
        disabled={processing}
        className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-8 rounded-lg transition-colors disabled:opacity-50"
      >
        {processing ? 'Processing...' : 'Process Claim'}
      </button>
    </div>
  )
}
