import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { postalApi } from '../services/postalApi'
import type { Reclamation, ReclamationStatus } from '../types/reclamation'
import { useTranslation } from '../i18n/LanguageContext'

export default function PostalListPage() {
  const { t } = useTranslation()
  const [reclamations, setReclamations] = useState<Reclamation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<ReclamationStatus | ''>('')
  const [searchQuery, setSearchQuery] = useState('')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [totalPages, setTotalPages] = useState(1)

  useEffect(() => {
    loadReclamations()
  }, [page, statusFilter])

  const loadReclamations = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await postalApi.listReclamations(page, 20, statusFilter || undefined)

      let filteredReclamations = response.items || []

      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase()
        filteredReclamations = filteredReclamations.filter((r: Reclamation) =>
          r.reclamation_number.toLowerCase().includes(query) ||
          r.client_nom.toLowerCase().includes(query) ||
          r.numero_suivi.toLowerCase().includes(query) ||
          r.reclamation_type.toLowerCase().includes(query)
        )
      }

      filteredReclamations.sort((a: Reclamation, b: Reclamation) => {
        const numA = parseInt(a.reclamation_number.replace(/\D/g, ''))
        const numB = parseInt(b.reclamation_number.replace(/\D/g, ''))
        return sortOrder === 'asc' ? numA - numB : numB - numA
      })

      setReclamations(filteredReclamations)
      setTotalPages(Math.ceil(response.total / 20))
    } catch (err) {
      console.error('Error loading reclamations:', err)
      setError('Failed to load reclamations')
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: ReclamationStatus) => {
    switch (status) {
      case 'pending': return 'bg-gray-100 text-gray-800'
      case 'processing': return 'bg-blue-100 text-blue-800'
      case 'completed': return 'bg-green-100 text-green-800'
      case 'rejected': return 'bg-red-100 text-red-800'
      case 'escalated': return 'bg-orange-100 text-orange-800'
      case 'manual_review': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusLabel = (status: ReclamationStatus) => {
    switch (status) {
      case 'pending': return t('postal.statusPending')
      case 'processing': return t('postal.statusProcessing')
      case 'completed': return t('postal.statusCompleted')
      case 'rejected': return t('postal.statusRejected')
      case 'escalated': return t('postal.statusEscalated')
      case 'manual_review': return t('postal.statusManualReview')
      default: return status
    }
  }

  const getTypeLabel = (type: string) => {
    return t(`postal.type_${type}`) || type
  }

  return (
    <div className="space-y-6">
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-3xl font-bold text-gray-900">{t('postal.title')}</h2>
            <p className="mt-2 text-gray-600">{t('postal.subtitle')}</p>
          </div>
          <button
            onClick={loadReclamations}
            className="bg-yellow-600 hover:bg-yellow-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
          >
            {t('postal.refresh')}
          </button>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2">
            <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">{t('postal.searchLabel')}</label>
            <input
              id="search"
              type="text"
              placeholder={t('postal.searchPlaceholder')}
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setPage(1) }}
              className="block w-full pl-3 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-yellow-500 focus:border-yellow-500 sm:text-sm"
            />
          </div>
          <div>
            <label htmlFor="status-filter" className="block text-sm font-medium text-gray-700 mb-1">{t('postal.filterByStatus')}</label>
            <select
              id="status-filter"
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value as ReclamationStatus | ''); setPage(1) }}
              className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-yellow-500 focus:border-yellow-500 rounded-md"
            >
              <option value="">{t('postal.allStatus')}</option>
              <option value="pending">{t('postal.statusPending')}</option>
              <option value="processing">{t('postal.statusProcessing')}</option>
              <option value="completed">{t('postal.statusCompleted')}</option>
              <option value="rejected">{t('postal.statusRejected')}</option>
              <option value="escalated">{t('postal.statusEscalated')}</option>
              <option value="manual_review">{t('postal.statusManualReview')}</option>
            </select>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-600"></div>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      ) : reclamations.length === 0 ? (
        <div className="bg-white shadow rounded-lg p-12 text-center">
          <h3 className="mt-2 text-sm font-medium text-gray-900">{t('postal.noReclamations')}</h3>
          <p className="mt-1 text-sm text-gray-500">
            {statusFilter || searchQuery ? t('postal.adjustFilters') : t('postal.noReclamationsInSystem')}
          </p>
        </div>
      ) : (
        <div className="bg-white shadow rounded-lg overflow-x-auto">
          <table className="w-full divide-y divide-gray-200 table-fixed">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="w-36 px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" onClick={() => setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')}>{t('postal.reclamationNumber')}</th>
                <th scope="col" className="w-40 px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('postal.clientName')}</th>
                <th scope="col" className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('postal.reclamationType')}</th>
                <th scope="col" className="w-32 px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('postal.status')}</th>
                <th scope="col" className="w-24 px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('postal.submitted')}</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {reclamations.map((reclamation) => (
                <tr key={reclamation.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => window.location.href = `/postal/${reclamation.id}`}>
                  <td className="px-3 py-3 whitespace-nowrap text-sm font-medium">
                    <Link to={`/postal/${reclamation.id}`} className="text-yellow-700 hover:text-yellow-900" onClick={(e) => e.stopPropagation()}>{reclamation.reclamation_number}</Link>
                  </td>
                  <td className="px-3 py-3 text-sm text-gray-500 truncate">{reclamation.client_nom}</td>
                  <td className="px-3 py-3 text-sm text-gray-500 truncate">{getTypeLabel(reclamation.reclamation_type)}</td>
                  <td className="px-3 py-3 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(reclamation.status)}`}>{getStatusLabel(reclamation.status)}</span>
                  </td>
                  <td className="px-3 py-3 whitespace-nowrap text-xs text-gray-500">{new Date(reclamation.submitted_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!loading && reclamations.length > 0 && (
        <div className="bg-white shadow rounded-lg p-4">
          <div className="flex items-center justify-between">
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">{t('postal.previous')}</button>
            <span className="text-sm text-gray-700">{t('postal.page')} {page} {totalPages > 1 && `${t('postal.of')} ${totalPages}`}</span>
            <button onClick={() => setPage(p => p + 1)} disabled={page >= totalPages} className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">{t('postal.next')}</button>
          </div>
        </div>
      )}
    </div>
  )
}
