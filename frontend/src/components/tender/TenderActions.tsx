/**
 * TenderActions Component - Process tender button
 * Process button hidden — processing is triggered automatically
 */

import type { Tender } from '../../types/tender'

interface TenderActionsProps {
  tender?: Tender
  onProcessStart?: () => void
}

export default function TenderActions(_props: TenderActionsProps) {
  return null
}
