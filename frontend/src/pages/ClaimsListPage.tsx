import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { claimsApi } from '../services/api'
import type { Claim, ClaimStatus } from '../types'
import { useTranslation } from '../i18n/LanguageContext'

export default function ClaimsListPage() {
  const { t } = useTranslation()
  const [claims, setClaims] = useState<Claim[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<ClaimStatus | ''>('')
  const [claimTypeFilter, setClaimTypeFilter] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState('')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [totalPages, setTotalPages] = useState(1)

  useEffect(() => {
    loadClaims()
  }, [page, statusFilter, claimTypeFilter, searchQuery, sortOrder])

  const loadClaims = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await claimsApi.listClaims(page, 20, statusFilter || undefined)

      // Client-side filtering and sorting
      let filteredClaims = response.claims || []

      // Filter by claim type
      if (claimTypeFilter) {
        filteredClaims = filteredClaims.filter((c: Claim) =>
          c.claim_type?.toLowerCase() === claimTypeFilter.toLowerCase()
        )
      }

      // Search filter
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase()
        filteredClaims = filteredClaims.filter((c: Claim) =>
          c.claim_number.toLowerCase().includes(query) ||
          c.user_id.toLowerCase().includes(query) ||
          (c.user_name && c.user_name.toLowerCase().includes(query)) ||
          c.claim_type?.toLowerCase().includes(query)
        )
      }

      // Sort by claim_number
      filteredClaims.sort((a: Claim, b: Claim) => {
        const numA = parseInt(a.claim_number.replace(/\D/g, ''))
        const numB = parseInt(b.claim_number.replace(/\D/g, ''))
        return sortOrder === 'asc' ? numA - numB : numB - numA
      })

      setClaims(filteredClaims)
      const totalPagesCalc = Math.ceil(response.total / 20)
      setTotalPages(totalPagesCalc)
    } catch (err) {
      console.error('Error loading claims:', err)
      setError(t('claims.failedToProcess'))
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: ClaimStatus) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800'
      case 'processing':
        return 'bg-purple-100 text-purple-800'
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'denied':
        return 'bg-red-100 text-red-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      case 'manual_review':
        return 'bg-orange-100 text-orange-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusLabel = (status: ClaimStatus) => {
    switch (status) {
      case 'pending': return t('common.pending')
      case 'processing': return t('common.processing')
      case 'completed': return t('common.completed')
      case 'denied': return t('common.denied')
      case 'failed': return t('common.failed')
      case 'manual_review': return t('common.manualReview')
      default: return status
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  const formatProcessingTime = (claim: Claim) => {
    if (claim.total_processing_time_ms) {
      const secs = claim.total_processing_time_ms / 1000
      if (secs < 60) return `${secs.toFixed(1)}s`
      return `${Math.floor(secs / 60)}m ${Math.round(secs % 60)}s`
    }
    return '-'
  }

  const toggleSortOrder = () => {
    setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-3xl font-bold text-gray-900">{t('claims.title')}</h2>
            <p className="mt-2 text-gray-600">{t('claims.subtitle')}</p>
          </div>
          <button
            onClick={loadClaims}
            className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
          >
            {t('common.refresh')}
          </button>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search Bar */}
          <div className="md:col-span-2">
            <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">
              {t('claims.searchLabel')}
            </label>
            <div className="relative">
              <input
                id="search"
                type="text"
                placeholder={t('claims.searchPlaceholder')}
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value)
                  setPage(1)
                }}
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </div>
          </div>

          {/* Status Filter */}
          <div>
            <label htmlFor="status-filter" className="block text-sm font-medium text-gray-700 mb-1">
              {t('claims.filterByStatus')}
            </label>
            <select
              id="status-filter"
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value as ClaimStatus | '')
                setPage(1)
              }}
              className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 rounded-md"
            >
              <option value="">{t('claims.allStatus')}</option>
              <option value="pending">{t('common.pending')}</option>
              <option value="processing">{t('common.processing')}</option>
              <option value="completed">{t('common.completed')}</option>
              <option value="denied">{t('common.denied')}</option>
              <option value="failed">{t('common.failed')}</option>
              <option value="manual_review">{t('common.manualReview')}</option>
            </select>
          </div>

          {/* Claim Type Filter */}
          <div>
            <label htmlFor="type-filter" className="block text-sm font-medium text-gray-700 mb-1">
              {t('claims.filterByType')}
            </label>
            <select
              id="type-filter"
              value={claimTypeFilter}
              onChange={(e) => {
                setClaimTypeFilter(e.target.value)
                setPage(1)
              }}
              className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 rounded-md"
            >
              <option value="">{t('claims.allTypes')}</option>
              <option value="Auto">Auto</option>
              <option value="Home">Home</option>
              <option value="Medical">Medical</option>
              <option value="Life">Life</option>
            </select>
          </div>
        </div>
      </div>

      {/* Claims List */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      ) : claims.length === 0 ? (
        <div className="bg-white shadow rounded-lg p-12 text-center">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">{t('claims.noClaims')}</h3>
          <p className="mt-1 text-sm text-gray-500">
            {statusFilter || claimTypeFilter || searchQuery
              ? t('claims.adjustFilters')
              : t('claims.noClaimsInSystem')}
          </p>
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden rounded-lg">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={toggleSortOrder}
                >
                  <div className="flex items-center gap-1">
                    {t('claims.claimNumber')}
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      {sortOrder === 'asc' ? (
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                      ) : (
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      )}
                    </svg>
                  </div>
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('claims.claimant')}
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('claims.type')}
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('claims.status')}
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('claims.submitted')}
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('claims.duration')}
                </th>
                <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('claims.actions')}
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {claims.map((claim) => (
                <tr key={claim.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {claim.claim_number}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {claim.user_name || claim.user_id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {claim.claim_type || 'N/A'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(claim.status)}`}>
                      {getStatusLabel(claim.status)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(claim.submitted_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatProcessingTime(claim)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <Link
                      to={`/claims/${claim.id}`}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      {t('claims.viewDetails')}
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {!loading && claims.length > 0 && (
        <div className="bg-white shadow rounded-lg p-4">
          <div className="flex items-center justify-between">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {t('common.previous')}
            </button>
            <span className="text-sm text-gray-700">
              {t('common.page')} {page} {totalPages > 1 && `/ ${totalPages}`}
            </span>
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={page >= totalPages}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {t('common.next')}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
