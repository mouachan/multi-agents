import { useEffect, useState } from 'react'
import type { AgentInfo } from '../../types/chat'
import { useTranslation } from '../../i18n/LanguageContext'
import { useToolDisplay } from '../../hooks/useToolDisplay'

interface AgentGraphProps {
  agents: AgentInfo[]
  activeAgentId?: string | null
  activatedAgentIds?: Set<string>
  activeTools?: string[]
  onAgentClick?: (agent: AgentInfo) => void
}

const AGENT_COLORS: Record<string, string> = {
  blue: '#3B82F6',
  amber: '#F59E0B',
  green: '#10B981',
  emerald: '#10B981',
  red: '#EF4444',
  purple: '#8B5CF6',
  indigo: '#6366F1',
  teal: '#14B8A6',
  pink: '#EC4899',
}

const ORCH_COLOR = '#2563EB'

function getColor(c: string) {
  return AGENT_COLORS[c] || AGENT_COLORS.blue
}

function getShortLabel(agent: AgentInfo) {
  if (agent.id === 'claims') return 'SI'
  if (agent.id === 'tenders') return 'AO'
  return agent.name.substring(0, 2).toUpperCase()
}

export default function AgentGraph({
  agents,
  activeAgentId,
  activatedAgentIds,
  activeTools,
  onAgentClick,
}: AgentGraphProps) {
  const showAll = activatedAgentIds === undefined
  const [ready, setReady] = useState(false)
  const { t } = useTranslation()
  const { getToolShort } = useToolDisplay()

  useEffect(() => {
    const t = setTimeout(() => setReady(true), 150)
    return () => clearTimeout(t)
  }, [])

  // Layout
  const W = 400
  const H = 380
  const cx = W / 2
  const cy = 155
  const orbit = 100
  const orchR = 30
  const nodeR = 25
  const toolOrbit = 44
  const toolR = 8
  const maxTools = 7

  // Position agents in a circle around the hub
  const nodes = agents.map((agent, i) => {
    const a = ((2 * Math.PI) / agents.length) * i - Math.PI / 2
    return { agent, x: cx + orbit * Math.cos(a), y: cy + orbit * Math.sin(a), angle: a }
  })

  // Active tools set for quick lookup
  const activeToolSet = new Set(activeTools || [])

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden border border-gray-200">
      <div className="px-4 pt-3 pb-1 border-b border-gray-100">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          {t('chat.agentArchitecture')}
        </h3>
      </div>

      <div className="bg-gradient-to-b from-gray-50 to-white">
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full">
          <style>{`
            @keyframes dash-flow {
              to { stroke-dashoffset: -16; }
            }
            @keyframes particle-fade {
              0%, 100% { opacity: 0; }
              15%, 85% { opacity: 1; }
            }
            @keyframes tool-pulse {
              0%, 100% { r: ${toolR}; opacity: 0.9; }
              50% { r: ${toolR + 2}; opacity: 1; }
            }
            .flow-line {
              stroke-dasharray: 5 5;
              animation: dash-flow 1.2s linear infinite;
            }
            .particle {
              animation: particle-fade 2.5s ease-in-out infinite;
            }
            .tool-active {
              animation: tool-pulse 1.5s ease-in-out infinite;
            }
          `}</style>

          <defs>
            <filter id="node-shadow">
              <feDropShadow dx="0" dy="1" stdDeviation="2" floodOpacity="0.15" />
            </filter>
            <filter id="particle-glow">
              <feGaussianBlur stdDeviation="2" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <filter id="tool-glow">
              <feGaussianBlur stdDeviation="1.5" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <radialGradient id="ambient" cx="50%" cy="44%">
              <stop offset="0%" stopColor={ORCH_COLOR} stopOpacity="0.06" />
              <stop offset="100%" stopColor="transparent" />
            </radialGradient>
          </defs>

          {/* Ambient glow */}
          <circle cx={cx} cy={cy} r="150" fill="url(#ambient)" />

          {/* Connections: hub <-> agents */}
          {nodes.map((n, i) => {
            const c = getColor(n.agent.color)
            const isActivated = showAll || (activatedAgentIds?.has(n.agent.id) ?? false)
            return (
              <g
                key={`conn-${n.agent.id}`}
                opacity={ready && isActivated ? 1 : 0}
                style={{ transition: `opacity 0.6s ease ${0.4 + i * 0.15}s` }}
              >
                {/* Base line */}
                <line
                  x1={cx} y1={cy} x2={n.x} y2={n.y}
                  stroke={c} strokeWidth="1.5" strokeOpacity="0.12"
                />
                {/* Dashed animated overlay */}
                <line
                  x1={cx} y1={cy} x2={n.x} y2={n.y}
                  stroke={c} strokeWidth="1" strokeOpacity="0.35"
                  className="flow-line"
                />
                {/* Particle hub->agent */}
                <circle
                  r="3" fill={c} filter="url(#particle-glow)"
                  className="particle"
                  style={{ animationDelay: `${i * 0.7}s` }}
                >
                  <animateMotion
                    dur={`${2.2 + i * 0.3}s`}
                    repeatCount="indefinite"
                    path={`M${cx},${cy} L${n.x},${n.y}`}
                  />
                </circle>
                {/* Particle agent->hub */}
                <circle
                  r="2" fill={ORCH_COLOR} opacity="0.4"
                  className="particle"
                  style={{ animationDelay: `${0.6 + i * 0.5}s` }}
                >
                  <animateMotion
                    dur={`${2.8 + i * 0.4}s`}
                    repeatCount="indefinite"
                    path={`M${n.x},${n.y} L${cx},${cy}`}
                  />
                </circle>
              </g>
            )
          })}

          {/* Inter-agent connections (subtle, only when both activated) */}
          {nodes.map((a, i) =>
            nodes.slice(i + 1).map((b, j) => {
              const bothActive = (showAll || (activatedAgentIds?.has(a.agent.id) && activatedAgentIds?.has(b.agent.id)))
              return (
                <line
                  key={`ia-${i}-${j}`}
                  x1={a.x} y1={a.y} x2={b.x} y2={b.y}
                  stroke="#CBD5E1" strokeWidth="0.5" strokeDasharray="2 6"
                  opacity={ready && bothActive ? 0.3 : 0}
                  style={{ transition: `opacity 0.6s ease ${0.9 + (i + j) * 0.1}s` }}
                />
              )
            })
          )}

          {/* Orchestrator hub node */}
          <g transform={`translate(${cx}, ${cy})`}>
            <g
              style={{
                transform: ready ? 'scale(1)' : 'scale(0)',
                transition: 'transform 0.7s cubic-bezier(0.34, 1.56, 0.64, 1) 0.15s',
              }}
            >
              {/* Pulse ring */}
              <circle r={orchR + 6} fill="none" stroke={ORCH_COLOR} strokeWidth="1">
                <animate
                  attributeName="r"
                  values={`${orchR + 6};${orchR + 14};${orchR + 6}`}
                  dur="3s" repeatCount="indefinite"
                />
                <animate
                  attributeName="opacity"
                  values="0.2;0.04;0.2"
                  dur="3s" repeatCount="indefinite"
                />
              </circle>

              {/* Main circle */}
              <circle r={orchR} fill={ORCH_COLOR} filter="url(#node-shadow)" />
              <circle r={orchR - 1.5} fill="none" stroke="white" strokeWidth="0.5" opacity="0.3" />

              {/* Label inside */}
              <text
                y="1" textAnchor="middle" dominantBaseline="central"
                fontSize="9" fill="white" fontWeight="700"
                style={{ fontFamily: 'system-ui, sans-serif' }}
              >
                HUB
              </text>
            </g>

            {/* Label below */}
            <text
              y={orchR + 14} textAnchor="middle"
              fontSize="9" fill="#64748B" fontWeight="600"
              style={{
                fontFamily: 'system-ui, sans-serif',
                opacity: ready ? 1 : 0,
                transition: 'opacity 0.5s ease 0.5s',
              }}
            >
              {t('chat.orchestrator')}
            </text>
          </g>

          {/* Agent nodes */}
          {nodes.map((n, i) => {
            const c = getColor(n.agent.color)
            const active = n.agent.id === activeAgentId
            const isActivated = showAll || (activatedAgentIds?.has(n.agent.id) ?? false)
            const delay = 0.35 + i * 0.22

            // Tool positions: arc on the outward side of the agent
            const toolsToShow = (n.agent.tools || []).slice(0, maxTools)
            const spreadAngle = Math.PI * 0.7
            const startAngle = n.angle - spreadAngle / 2

            return (
              <g key={n.agent.id}>
                {/* Tool connector lines + nodes */}
                {toolsToShow.map((toolName, j) => {
                  const tAngle = toolsToShow.length > 1
                    ? startAngle + (spreadAngle / (toolsToShow.length - 1)) * j
                    : n.angle
                  const tx = n.x + toolOrbit * Math.cos(tAngle)
                  const ty = n.y + toolOrbit * Math.sin(tAngle)
                  const isActive = activeToolSet.has(toolName)
                  const toolDelay = delay + 0.3 + j * 0.08

                  return (
                    <g
                      key={`tool-${n.agent.id}-${toolName}`}
                      opacity={ready && isActivated ? 1 : 0}
                      style={{ transition: `opacity 0.5s ease ${toolDelay}s` }}
                    >
                      {/* Connector line */}
                      <line
                        x1={n.x} y1={n.y} x2={tx} y2={ty}
                        stroke={c} strokeWidth="0.7" strokeOpacity="0.2"
                        strokeDasharray="2 2"
                      />
                      {/* Tool node */}
                      <g style={{ cursor: 'default' }}>
                        <title>{toolName.replace(/_/g, ' ')}</title>
                        {isActive ? (
                          <>
                            {/* Glow ring for active tool */}
                            <circle cx={tx} cy={ty} r={toolR + 3} fill={c} opacity="0.15" />
                            <rect
                              x={tx - toolR} y={ty - toolR}
                              width={toolR * 2} height={toolR * 2}
                              rx="3" ry="3"
                              fill={c} filter="url(#tool-glow)"
                              className="tool-active"
                            />
                          </>
                        ) : (
                          <rect
                            x={tx - toolR + 1} y={ty - toolR + 1}
                            width={(toolR - 1) * 2} height={(toolR - 1) * 2}
                            rx="2.5" ry="2.5"
                            fill={c} opacity="0.25"
                            stroke={c} strokeWidth="0.5" strokeOpacity="0.3"
                          />
                        )}
                        {/* Tool abbreviation */}
                        <text
                          x={tx} y={ty + 0.5}
                          textAnchor="middle" dominantBaseline="central"
                          fontSize="6.5" fill={isActive ? 'white' : c}
                          fontWeight="700" opacity={isActive ? 1 : 0.7}
                          style={{ fontFamily: 'system-ui, sans-serif', pointerEvents: 'none' }}
                        >
                          {getToolShort(toolName)}
                        </text>
                      </g>
                    </g>
                  )
                })}

                {/* Agent node (on top of tool lines) */}
                <g
                  transform={`translate(${n.x}, ${n.y})`}
                  style={{ cursor: 'pointer' }}
                  onClick={() => onAgentClick?.(n.agent)}
                >
                  <g
                    style={{
                      transform: ready && isActivated ? 'scale(1)' : 'scale(0)',
                      transition: `transform 0.7s cubic-bezier(0.34, 1.56, 0.64, 1) ${delay}s`,
                    }}
                  >
                    {/* Active pulse ring */}
                    {active && (
                      <circle r={nodeR + 5} fill="none" stroke={c} strokeWidth="1.5">
                        <animate
                          attributeName="r"
                          values={`${nodeR + 5};${nodeR + 12};${nodeR + 5}`}
                          dur="2s" repeatCount="indefinite"
                        />
                        <animate
                          attributeName="opacity"
                          values="0.5;0.1;0.5"
                          dur="2s" repeatCount="indefinite"
                        />
                      </circle>
                    )}

                    {/* Main circle */}
                    <circle
                      r={nodeR} fill={c} filter="url(#node-shadow)"
                      stroke={active ? c : 'none'}
                      strokeWidth={active ? 2 : 0}
                      strokeOpacity={active ? 0.3 : 0}
                    />
                    <circle
                      r={nodeR - 1.5} fill="none" stroke="white"
                      strokeWidth="0.5" opacity="0.2"
                    />

                    {/* Abbreviation inside */}
                    <text
                      y="1" textAnchor="middle" dominantBaseline="central"
                      fontSize="10" fill="white" fontWeight="800"
                      style={{ fontFamily: 'system-ui, sans-serif' }}
                    >
                      {getShortLabel(n.agent)}
                    </text>
                  </g>

                  {/* Name label */}
                  <text
                    y={nodeR + 13} textAnchor="middle"
                    fontSize="9" fill={active ? '#1E40AF' : '#64748B'}
                    fontWeight={active ? '700' : '500'}
                    style={{
                      fontFamily: 'system-ui, sans-serif',
                      opacity: ready && isActivated ? 1 : 0,
                      transition: `opacity 0.5s ease ${delay + 0.2}s`,
                    }}
                  >
                    {n.agent.name}
                  </text>
                </g>
              </g>
            )
          })}
        </svg>
      </div>
    </div>
  )
}
