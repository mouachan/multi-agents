import { useCallback, useEffect, useState } from 'react'
import { chatApi } from '../services/api'
import type { AgentInfo } from '../types/chat'

/** The agent profiles the signed-in user may talk to (the backend keeps those of the user's domains). */
export function useAgents() {
  const [agents, setAgents] = useState<AgentInfo[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadAgents = useCallback(async () => {
    setIsLoading(true)
    try {
      setAgents(await chatApi.agents())
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
