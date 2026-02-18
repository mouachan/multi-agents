import { useCallback, useEffect, useState } from 'react'
import { orchestratorApi } from '../services/orchestratorService'
import type { AgentInfo } from '../types/chat'

export function useAgents() {
  const [agents, setAgents] = useState<AgentInfo[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadAgents = useCallback(async () => {
    setIsLoading(true)
    try {
      const data = await orchestratorApi.getAgents()
      setAgents(data)
    } catch (err: any) {
      setError(err.message || 'Failed to load agents')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadAgents()
  }, [loadAgents])

  return { agents, isLoading, error, reload: loadAgents }
}
