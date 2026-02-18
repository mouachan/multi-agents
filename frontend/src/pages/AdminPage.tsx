import { useState, useEffect } from 'react'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

interface DatabaseStats {
  users: number
  contracts: number
  claims_total: number
  claims_by_status: Record<string, number>
  knowledge_base: number
  knowledge_base_embeddings: string
  claim_documents_embeddings: string
}

export default function AdminPage() {
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState<DatabaseStats | null>(null)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/database-stats`)
      if (response.ok) {
        const data = await response.json()
        setStats(data.data)
      }
    } catch (error) {
      console.error('Error fetching stats:', error)
    }
  }

  const handleResetDatabase = async () => {
    if (!confirm('⚠️ WARNING: This will DELETE ALL DATA and reload seed data.\n\nAre you sure you want to reset the database?')) {
      return
    }

    setLoading(true)
    setMessage(null)

    try {
      const response = await fetch(`${API_BASE_URL}/admin/reset-database`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      const data = await response.json()

      if (response.ok) {
        setMessage({
          type: 'success',
          text: `✅ Database reset successfully!\n\nUsers: ${data.data.users}\nContracts: ${data.data.contracts}\nClaims: ${data.data.claims}\nKnowledge Base: ${data.data.knowledge_base}`
        })
        // Refresh stats
        await fetchStats()
      } else {
        setMessage({
          type: 'error',
          text: `❌ Reset failed: ${data.detail || 'Unknown error'}`
        })
      }
    } catch (error) {
      setMessage({
        type: 'error',
        text: `❌ Reset failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-3xl font-bold text-gray-900">Admin Panel</h2>
        <p className="mt-2 text-gray-600">Database management and demo utilities</p>
      </div>

      {/* Statistics Cards */}
      {stats && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Users */}
            <div className="bg-white shadow rounded-lg p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0 bg-blue-500 rounded-md p-3">
                  <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Users</dt>
                    <dd className="text-3xl font-semibold text-gray-900">{stats.users}</dd>
                  </dl>
                </div>
              </div>
            </div>

            {/* Contracts */}
            <div className="bg-white shadow rounded-lg p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0 bg-green-500 rounded-md p-3">
                  <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Contracts</dt>
                    <dd className="text-3xl font-semibold text-gray-900">{stats.contracts}</dd>
                  </dl>
                </div>
              </div>
            </div>

            {/* Total Claims */}
            <div className="bg-white shadow rounded-lg p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0 bg-purple-500 rounded-md p-3">
                  <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Total Claims</dt>
                    <dd className="text-3xl font-semibold text-gray-900">{stats.claims_total}</dd>
                  </dl>
                </div>
              </div>
            </div>

            {/* Knowledge Base */}
            <div className="bg-white shadow rounded-lg p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0 bg-indigo-500 rounded-md p-3">
                  <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Knowledge Base</dt>
                    <dd className="text-3xl font-semibold text-gray-900">{stats.knowledge_base}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          {/* Claims by Status */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Claims by Status</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center justify-between p-4 bg-red-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Failed</span>
                <span className="text-2xl font-bold text-red-600">{stats.claims_by_status.failed || 0}</span>
              </div>
              <div className="flex items-center justify-between p-4 bg-yellow-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Pending</span>
                <span className="text-2xl font-bold text-yellow-600">{stats.claims_by_status.pending || 0}</span>
              </div>
              <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Completed</span>
                <span className="text-2xl font-bold text-green-600">{stats.claims_by_status.completed || 0}</span>
              </div>
            </div>
          </div>

          {/* Embeddings Status */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Embeddings Status</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">KB Embeddings</span>
                <span className="text-2xl font-bold text-blue-600">{stats.knowledge_base_embeddings}</span>
              </div>
              <div className="flex items-center justify-between p-4 bg-indigo-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Claim Embeddings</span>
                <span className="text-2xl font-bold text-indigo-600">{stats.claim_documents_embeddings}</span>
              </div>
            </div>
            <button
              onClick={fetchStats}
              className="mt-4 text-sm text-blue-600 hover:text-blue-800 font-medium flex items-center"
            >
              <svg className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh Stats
            </button>
          </div>
        </>
      )}

      {/* Reset Database Section */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center mb-4">
          <div className="flex-shrink-0 bg-orange-500 rounded-md p-2">
            <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
            </svg>
          </div>
          <h3 className="ml-3 text-lg font-medium text-gray-900">Database Management</h3>
        </div>

        <div className="bg-orange-50 border-l-4 border-orange-400 p-4 mb-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-orange-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-orange-800">Reset Database</h3>
              <div className="mt-2 text-sm text-orange-700">
                <p className="font-medium">This action will:</p>
                <ul className="list-disc list-inside mt-2 space-y-1">
                  <li>Delete ALL existing data (claims, users, contracts, etc.)</li>
                  <li>Reload seed data from 001_sample_data.sql</li>
                  <li>Reset to initial demo state</li>
                  <li className="font-semibold">Embeddings will need to be regenerated via KFP pipeline</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <button
          onClick={handleResetDatabase}
          disabled={loading}
          className={`w-full px-6 py-3 rounded-lg font-semibold text-white transition-colors flex items-center justify-center ${
            loading
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-red-600 hover:bg-red-700'
          }`}
        >
          {loading ? (
            <>
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Resetting Database...
            </>
          ) : (
            <>
              <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Reset Database to Demo State
            </>
          )}
        </button>
      </div>

      {/* Message Display */}
      {message && (
        <div className={`p-4 rounded-lg shadow ${
          message.type === 'success'
            ? 'bg-green-50 border-l-4 border-green-400'
            : 'bg-red-50 border-l-4 border-red-400'
        }`}>
          <div className="flex">
            <div className="flex-shrink-0">
              {message.type === 'success' ? (
                <svg className="h-5 w-5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                <svg className="h-5 w-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              )}
            </div>
            <div className="ml-3">
              <pre className={`text-sm whitespace-pre-wrap font-sans ${
                message.type === 'success' ? 'text-green-800' : 'text-red-800'
              }`}>
                {message.text}
              </pre>
            </div>
          </div>
        </div>
      )}

      {/* Next Steps */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center mb-4">
          <div className="flex-shrink-0 bg-blue-500 rounded-md p-2">
            <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
          </div>
          <h3 className="ml-3 text-lg font-medium text-gray-900">Next Steps After Reset</h3>
        </div>
        <ol className="space-y-3">
          <li className="flex">
            <span className="flex-shrink-0 w-6 h-6 flex items-center justify-center bg-blue-100 text-blue-800 rounded-full text-sm font-semibold mr-3">1</span>
            <span className="text-gray-700">Verify database stats show correct counts (116 contracts, 100 claims, etc.)</span>
          </li>
          <li className="flex">
            <span className="flex-shrink-0 w-6 h-6 flex items-center justify-center bg-blue-100 text-blue-800 rounded-full text-sm font-semibold mr-3">2</span>
            <span className="text-gray-700">Access Data Science Pipelines UI in OpenShift</span>
          </li>
          <li className="flex">
            <span className="flex-shrink-0 w-6 h-6 flex items-center justify-center bg-blue-100 text-blue-800 rounded-full text-sm font-semibold mr-3">3</span>
            <span className="text-gray-700">Upload and run <code className="bg-gray-100 px-2 py-1 rounded text-sm">data_initialization_pipeline.yaml</code></span>
          </li>
          <li className="flex">
            <span className="flex-shrink-0 w-6 h-6 flex items-center justify-center bg-blue-100 text-blue-800 rounded-full text-sm font-semibold mr-3">4</span>
            <span className="text-gray-700">Wait ~10-15 minutes for embeddings generation</span>
          </li>
          <li className="flex">
            <span className="flex-shrink-0 w-6 h-6 flex items-center justify-center bg-blue-100 text-blue-800 rounded-full text-sm font-semibold mr-3">5</span>
            <span className="text-gray-700">Verify embeddings: KB 15/15, Claims 90/90</span>
          </li>
          <li className="flex">
            <span className="flex-shrink-0 w-6 h-6 flex items-center justify-center bg-blue-100 text-blue-800 rounded-full text-sm font-semibold mr-3">6</span>
            <span className="text-gray-700">Start testing claim processing with APPROVE/DENY/MANUAL_REVIEW scenarios</span>
          </li>
        </ol>
      </div>
    </div>
  )
}
