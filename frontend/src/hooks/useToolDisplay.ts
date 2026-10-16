import { useEffect, useState } from 'react'
import { chatApi } from '../services/api'
import type { ToolDisplayConfig } from '../types/chat'

const EMPTY: ToolDisplayConfig = { tools: {}, servers: {}, categories: {} }
let cachedConfig: ToolDisplayConfig | null = null
let fetchPromise: Promise<ToolDisplayConfig> | null = null

/** Labels and colors of the MCP tools (files/prompts/backend/chat-config.yaml), loaded once. */
async function fetchToolDisplayConfig(): Promise<ToolDisplayConfig> {
  return chatApi.toolDisplay().catch(() => EMPTY)
}

export function useToolDisplay() {
  const [config, setConfig] = useState<ToolDisplayConfig>(
    cachedConfig || EMPTY
  )

  useEffect(() => {
    if (cachedConfig) return

    if (!fetchPromise) {
      fetchPromise = fetchToolDisplayConfig()
    }

    fetchPromise.then((data) => {
      cachedConfig = data
      setConfig(data)
    }).catch(() => {
      // Keep empty defaults on error
    })
  }, [])

  const getToolLabel = (name: string, lang: string): string => {
    const meta = config.tools[name]
    if (meta?.label) {
      return meta.label[lang] || meta.label['en'] || meta.label['fr'] || name.replace(/_/g, ' ')
    }
    return name.replace(/_/g, ' ')
  }

  const getToolShort = (name: string): string => {
    const meta = config.tools[name]
    if (meta?.short) return meta.short
    return name.substring(0, 3).toUpperCase()
  }

  const getServerInfo = (serverLabel?: string): { label: string; color: string } | null => {
    if (!serverLabel) return null
    return config.servers[serverLabel] || null
  }

  const getToolCategoryInfo = (toolName: string, lang: string): { label: string; color: string } | null => {
    const meta = config.tools[toolName]
    if (!meta?.category) return null
    const cat = config.categories[meta.category]
    if (!cat) return null
    const label = cat.label[lang] || cat.label['en'] || cat.label['fr'] || meta.category
    // Map category to color
    const colorMap: Record<string, string> = {
      extraction: 'blue',
      rag: 'purple',
      crud: 'emerald',
    }
    return { label, color: colorMap[meta.category] || 'gray' }
  }

  return { toolDisplay: config, getToolLabel, getToolShort, getServerInfo, getToolCategoryInfo }
}
