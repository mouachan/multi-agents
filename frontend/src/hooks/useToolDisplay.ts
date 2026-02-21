import { useEffect, useState } from 'react'
import type { ToolDisplayConfig } from '../types/chat'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

let cachedConfig: ToolDisplayConfig | null = null
let fetchPromise: Promise<ToolDisplayConfig> | null = null

async function fetchToolDisplayConfig(): Promise<ToolDisplayConfig> {
  const res = await fetch(`${API_BASE_URL}/config/tool-display`)
  if (!res.ok) {
    return { tools: {}, servers: {}, categories: {} }
  }
  return res.json()
}

export function useToolDisplay() {
  const [config, setConfig] = useState<ToolDisplayConfig>(
    cachedConfig || { tools: {}, servers: {}, categories: {} }
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
