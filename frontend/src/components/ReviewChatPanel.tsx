/**
 * ReviewChatPanel - Human-in-the-Loop review interface
 *
 * Features:
 * - Real-time WebSocket connection for collaborative review
 * - Chat with other reviewers
 * - Submit review actions (approve/reject/comment)
 * - See presence of other active reviewers
 */

import { useEffect, useState, useRef } from 'react'

interface Message {
  type: string
  reviewer_id?: string
  reviewer_name?: string
  message?: string
  answer?: string
  action?: string
  comment?: string
  timestamp?: string
  reason?: string
  new_status?: string
}

interface Reviewer {
  reviewer_id: string
  reviewer_name: string
  joined_at: string
}

interface ReviewChatPanelProps {
  claimId: string
  entityType?: 'claim' | 'tender'
  reviewerId?: string
  reviewerName?: string
  onActionSubmitted?: (action: string) => void
}

export default function ReviewChatPanel({
  claimId,
  entityType: _entityType = 'claim',
  reviewerId = 'reviewer_' + Math.random().toString(36).substr(2, 9),
  reviewerName = 'Anonymous Reviewer',
  onActionSubmitted
}: ReviewChatPanelProps) {
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [connected, setConnected] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [activeReviewers, setActiveReviewers] = useState<Reviewer[]>([])
  const [chatInput, setChatInput] = useState('')
  const [commentInput, setCommentInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Get WebSocket URL from browser location
  const getWsUrl = () => {
    // Use window.location to construct WebSocket URL
    const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const wsHost = window.location.host
    return `${wsProtocol}://${wsHost}/api/v1/review/ws/review/${claimId}?reviewer_id=${reviewerId}&reviewer_name=${encodeURIComponent(reviewerName)}`
  }

  useEffect(() => {
    // Connect to WebSocket
    const wsUrl = getWsUrl()
    console.log('Connecting to WebSocket:', wsUrl)

    const websocket = new WebSocket(wsUrl)

    websocket.onopen = () => {
      console.log('WebSocket connected')
      setConnected(true)
    }

    websocket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        console.log('Received message:', message)

        // Handle different message types
        if (message.type === 'connected') {
          setActiveReviewers(message.active_reviewers || [])
        } else if (message.type === 'reviewer_joined') {
          setActiveReviewers(prev => [...prev, {
            reviewer_id: message.reviewer_id,
            reviewer_name: message.reviewer_name,
            joined_at: message.timestamp
          }])
          setMessages(prev => [...prev, message])
        } else if (message.type === 'reviewer_left') {
          setActiveReviewers(prev => prev.filter(r => r.reviewer_id !== message.reviewer_id))
          setMessages(prev => [...prev, message])
        } else if (message.type === 'manual_review_required') {
          setMessages(prev => [...prev, {
            type: 'system',
            message: `Manual review required: ${message.reason}`,
            timestamp: message.timestamp
          }])
        } else if (message.type === 'qa_exchange') {
          // Remove "Asking agent..." loading message if exists
          setMessages(prev => [
            ...prev.filter(m => m.message !== 'Asking agent...'),
            message
          ])
        } else {
          setMessages(prev => [...prev, message])
        }
      } catch (err) {
        console.error('Error parsing WebSocket message:', err)
      }
    }

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error)
      setConnected(false)
    }

    websocket.onclose = () => {
      console.log('WebSocket disconnected')
      setConnected(false)
    }

    setWs(websocket)

    // Ping every 30 seconds to keep connection alive
    const pingInterval = setInterval(() => {
      if (websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30000)

    return () => {
      clearInterval(pingInterval)
      websocket.close()
    }
  }, [claimId, reviewerId, reviewerName])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendChatMessage = () => {
    if (!ws || !chatInput.trim()) return

    ws.send(JSON.stringify({
      type: 'chat',
      message: chatInput.trim()
    }))

    setChatInput('')
  }

  const askAgent = async () => {
    if (!claimId || !commentInput.trim()) {
      alert('Please enter a question for the agent')
      return
    }

    const question = commentInput.trim()

    try {
      // Show loading message
      setMessages(prev => [...prev, {
        type: 'system',
        message: 'Asking agent...',
        timestamp: new Date().toISOString()
      }])

      const response = await fetch(`/api/v1/review/${claimId}/ask-agent`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          question,
          reviewer_id: reviewerId,
          reviewer_name: reviewerName
        })
      })

      if (!response.ok) {
        throw new Error('Failed to ask agent')
      }

      await response.json()

      // Don't add locally - will come via WebSocket broadcast to avoid duplication
      setMessages(prev => prev.filter(m => m.message !== 'Asking agent...')) // Just remove loading message

      setCommentInput('')
    } catch (err) {
      console.error('Error asking agent:', err)
      setMessages(prev => [
        ...prev.filter(m => m.message !== 'Asking agent...'),
        {
          type: 'system',
          message: 'Failed to get answer from agent. Please try again.',
          timestamp: new Date().toISOString()
        }
      ])
    }
  }

  const submitAction = async (action: string) => {
    if (!claimId) return

    const comment = commentInput.trim()

    // Send via WebSocket
    if (ws) {
      ws.send(JSON.stringify({
        type: 'action',
        action,
        comment
      }))
    }

    // Also send via REST API to update database
    try {
      await fetch(`/api/v1/review/${claimId}/action`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          action,
          comment,
          reviewer_id: reviewerId,
          reviewer_name: reviewerName
        })
      })

      setCommentInput('')
      onActionSubmitted?.(action)
    } catch (err) {
      console.error('Error submitting action:', err)
    }
  }

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return ''
    const date = new Date(timestamp)
    return date.toLocaleTimeString()
  }

  const renderMessage = (msg: Message, index: number) => {
    if (msg.type === 'chat_message') {
      return (
        <div key={index} className="mb-3 p-2 bg-gray-50 rounded">
          <div className="text-xs text-gray-500">
            <strong>{msg.reviewer_name}</strong> · {formatTimestamp(msg.timestamp)}
          </div>
          <div className="mt-1">{msg.message}</div>
        </div>
      )
    }

    if (msg.type === 'action_taken') {
      return (
        <div key={index} className="mb-3 p-2 bg-blue-50 rounded border-l-4 border-blue-500">
          <div className="text-xs text-gray-500">
            <strong>{msg.reviewer_name}</strong> · {formatTimestamp(msg.timestamp)}
          </div>
          <div className="mt-1 font-semibold text-blue-700">
            {msg.action?.toUpperCase()}
          </div>
          {msg.comment && <div className="mt-1 text-sm">{msg.comment}</div>}
        </div>
      )
    }

    if (msg.type === 'claim_updated') {
      return (
        <div key={index} className="mb-3 p-2 bg-green-50 rounded border-l-4 border-green-500">
          <div className="text-xs text-gray-500">{formatTimestamp(msg.timestamp)}</div>
          <div className="mt-1 font-semibold text-green-700">
            Claim updated: {msg.new_status}
          </div>
          <div className="text-sm text-gray-600">
            {msg.reviewer_name} performed action: {msg.action}
          </div>
        </div>
      )
    }

    if (msg.type === 'reviewer_joined') {
      return (
        <div key={index} className="mb-2 text-xs text-gray-500 text-center italic">
          {msg.reviewer_name} joined the review
        </div>
      )
    }

    if (msg.type === 'reviewer_left') {
      return (
        <div key={index} className="mb-2 text-xs text-gray-500 text-center italic">
          {msg.reviewer_name} left the review
        </div>
      )
    }

    if (msg.type === 'qa_exchange') {
      return (
        <div key={index} className="mb-3">
          {/* Question */}
          <div className="p-3 bg-blue-50 rounded-lg border-l-4 border-blue-500 mb-2">
            <div className="text-xs text-gray-500">
              <strong>{msg.reviewer_name}</strong> asked · {formatTimestamp(msg.timestamp)}
            </div>
            <div className="mt-1 font-semibold text-blue-900">
              💬 {msg.message}
            </div>
          </div>
          {/* Answer */}
          <div className="p-3 bg-purple-50 rounded-lg border-l-4 border-purple-500 ml-4">
            <div className="text-xs text-purple-700 font-semibold mb-1">
              🤖 Agent Response
            </div>
            <div className="text-sm text-gray-800 whitespace-pre-wrap">
              {msg.answer}
            </div>
          </div>
        </div>
      )
    }

    if (msg.type === 'system' || msg.type === 'manual_review_required') {
      return (
        <div key={index} className="mb-3 p-2 bg-yellow-50 rounded border-l-4 border-yellow-500">
          <div className="text-sm font-semibold text-yellow-800">System</div>
          <div className="mt-1 text-sm">{msg.message || msg.reason}</div>
        </div>
      )
    }

    return null
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-4 h-full flex flex-col">
      {/* Header */}
      <div className="border-b pb-3 mb-3">
        <h2 className="text-xl font-bold mb-2">Manual Review Required</h2>
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm text-gray-600">
            {connected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Active Reviewers */}
      {activeReviewers.length > 0 && (
        <div className="mb-3 p-2 bg-gray-50 rounded">
          <div className="text-xs text-gray-500 mb-1">Active Reviewers ({activeReviewers.length})</div>
          <div className="flex flex-wrap gap-2">
            {activeReviewers.map(reviewer => (
              <div key={reviewer.reviewer_id} className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded">
                {reviewer.reviewer_name}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto mb-3 max-h-96">
        {messages.map((msg, index) => renderMessage(msg, index))}
        <div ref={messagesEndRef} />
      </div>

      {/* Review Actions */}
      <div className="border-t pt-3 mb-3">
        <h3 className="text-sm font-semibold mb-2">Review Decision</h3>
        <textarea
          className="w-full p-2 border rounded mb-2 text-sm"
          placeholder="Add comments (optional)..."
          value={commentInput}
          onChange={(e) => setCommentInput(e.target.value)}
          rows={2}
        />
        <div className="flex gap-2">
          <button
            onClick={() => submitAction('approve')}
            className="flex-1 bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 text-sm font-semibold"
          >
            ✓ Approve
          </button>
          <button
            onClick={() => submitAction('reject')}
            className="flex-1 bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 text-sm font-semibold"
          >
            ✗ Reject
          </button>
          <button
            onClick={askAgent}
            className="flex-1 bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 text-sm font-semibold"
          >
            🤖 Ask Agent
          </button>
        </div>
      </div>

      {/* Chat Input */}
      <div className="border-t pt-3">
        <h3 className="text-sm font-semibold mb-2">Chat with Reviewers</h3>
        <div className="flex gap-2">
          <input
            type="text"
            className="flex-1 p-2 border rounded text-sm"
            placeholder="Type a message..."
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendChatMessage()}
          />
          <button
            onClick={sendChatMessage}
            disabled={!chatInput.trim()}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:bg-gray-400 text-sm font-semibold"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}
