import { useCallback, useEffect, useState } from 'react'
import { useAuth, type Domain } from '../auth/AuthContext'
import { agentVisual } from '../lib/agents'
import { orchestratorApi } from '../services/orchestratorService'
import type { AgentInfo } from '../types/chat'

/** Agents the signed-in user may use (their domain's agent is granted by OpenShift RBAC). */
export function useAgents() {
  const { can } = useAuth()
  const [agents, setAgents] = useState<AgentInfo[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadAgents = useCallback(async () => {
    setIsLoading(true)
    try {
      const data = await orchestratorApi.getAgents()
      setAgents(data.filter((a) => {
        const domain = agentVisual(a.id).domain
        return domain === 'orchestrator' || can(domain as Domain)
      }))
    } catch (err: any) {
      setError(err.message || 'Failed to load agents')
    } finally {
      setIsLoading(false)
    }
  }, [can])

  useEffect(() => {
    loadAgents()
  }, [loadAgents])

  return { agents, isLoading, error, reload: loadAgents }
}
