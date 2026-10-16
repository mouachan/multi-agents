import { casesApi } from '../services/api'
import type { Case, Decision, Domain } from '../types/case'
import { usePolling, useResource } from './useResource'

/** A case and its current decision; reloaded every few seconds while the agent processes it. */
export function useCase(domain: Domain, id?: string) {
  const res = useResource<{ case: Case; decision: Decision | null }>(async () => {
    const api = casesApi(domain)
    const [found, decision] = await Promise.all([api.get(id!), api.decision(id!)])
    return { case: found, decision }
  }, [domain, id])
  usePolling(res.data?.case.status === 'processing', res.reload)
  return res
}
