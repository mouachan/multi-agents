import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { tendersApi } from '../services/tenderApi'
import type { Tender, TenderStatus } from '../types/tender'
import { useTranslation } from '../i18n/LanguageContext'

export default function TendersListPage() {
  const { t } = useTranslation()
  const [tenders, setTenders] = useState<Tender[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<TenderStatus | ''>('')
  const [searchQuery, setSearchQuery] = useState('')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [totalPages, setTotalPages] = useState(1)

  useEffect(() => {
    loadTenders()
  }, [page, statusFilter])

  const loadTenders = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await tendersApi.listTenders(page, 20, statusFilter || undefined)

      let filteredTenders = response.tenders || []

      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase()
        filteredTenders = filteredTenders.filter((t: Tender) =>
          t.tender_number.toLowerCase().includes(query) ||
          t.entity_id.toLowerCase().includes(query) ||
          (t.metadata as any)?.titre?.toLowerCase().includes(query) ||
          (t.metadata as any)?.objet_marche?.toLowerCase().includes(query) ||
          (t.metadata as any)?.maitre_ouvrage?.toLowerCase().includes(query)
        )
      }

      filteredTenders.sort((a: Tender, b: Tender) => {
        const numA = parseInt(a.tender_number.replace(/\D/g, ''))
        const numB = parseInt(b.tender_number.replace(/\D/g, ''))
        return sortOrder === 'asc' ? numA - numB : numB - numA
      })

      setTenders(filteredTenders)
      setTotalPages(Math.ceil(response.total / 20))
    } catch (err) {
      console.error('Error loading tenders:', err)
      setError('Failed to load tenders')
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: TenderStatus) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800'
      case 'processing': return 'bg-amber-100 text-amber-800'
      case 'completed': return 'bg-green-100 text-green-800'
      case 'failed': return 'bg-red-100 text-red-800'
      case 'manual_review': return 'bg-orange-100 text-orange-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusLabel = (status: TenderStatus) => {
    switch (status) {
      case 'pending': return t('tenders.statusPending')
      case 'processing': return t('tenders.statusProcessing')
      case 'completed': return t('tenders.statusCompleted')
      case 'failed': return t('tenders.statusFailed')
      case 'manual_review': return t('tenders.statusManualReview')
      default: return status
    }
  }

  const formatAmount = (amount: number | null | undefined) => {
    if (!amount) return '-'
    return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(amount)
  }

  return (
    <div className="space-y-6">
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-3xl font-bold text-gray-900">{t('tenders.title')}</h2>
            <p className="mt-2 text-gray-600">{t('tenders.subtitle')}</p>
          </div>
          <button
            onClick={loadTenders}
            className="bg-amber-600 hover:bg-amber-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
          >
            {t('tenders.refresh')}
          </button>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2">
            <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">{t('tenders.searchLabel')}</label>
            <input
              id="search"
              type="text"
              placeholder={t('tenders.searchPlaceholder')}
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setPage(1) }}
              className="block w-full pl-3 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-amber-500 focus:border-amber-500 sm:text-sm"
            />
          </div>
          <div>
            <label htmlFor="status-filter" className="block text-sm font-medium text-gray-700 mb-1">{t('tenders.filterByStatus')}</label>
            <select
              id="status-filter"
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value as TenderStatus | ''); setPage(1) }}
              className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-amber-500 focus:border-amber-500 rounded-md"
            >
              <option value="">{t('tenders.allStatus')}</option>
              <option value="pending">{t('tenders.statusPending')}</option>
              <option value="processing">{t('tenders.statusProcessing')}</option>
              <option value="completed">{t('tenders.statusCompleted')}</option>
              <option value="failed">{t('tenders.statusFailed')}</option>
              <option value="manual_review">{t('tenders.statusManualReview')}</option>
            </select>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-600"></div>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      ) : tenders.length === 0 ? (
        <div className="bg-white shadow rounded-lg p-12 text-center">
          <h3 className="mt-2 text-sm font-medium text-gray-900">{t('tenders.noTenders')}</h3>
          <p className="mt-1 text-sm text-gray-500">
            {statusFilter || searchQuery ? t('tenders.adjustFilters') : t('tenders.noTendersInSystem')}
          </p>
        </div>
      ) : (
        <div className="bg-white shadow rounded-lg overflow-x-auto">
          <table className="w-full divide-y divide-gray-200 table-fixed">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="w-32 px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" onClick={() => setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')}>{t('tenders.tenderNumber')}</th>
                <th scope="col" className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('tenders.object')}</th>
                <th scope="col" className="w-40 px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('tenders.client')}</th>
                <th scope="col" className="w-28 px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('tenders.amount')}</th>
                <th scope="col" className="w-28 px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('tenders.status')}</th>
                <th scope="col" className="w-24 px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('tenders.submitted')}</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {tenders.map((tender) => (
                <tr key={tender.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => window.location.href = `/tenders/${tender.id}`}>
                  <td className="px-3 py-3 whitespace-nowrap text-sm font-medium">
                    <Link to={`/tenders/${tender.id}`} className="text-amber-600 hover:text-amber-900" onClick={(e) => e.stopPropagation()}>{tender.tender_number}</Link>
                  </td>
                  <td className="px-3 py-3 text-sm text-gray-500 truncate">{(tender.metadata as any)?.titre || (tender.metadata as any)?.objet_marche || '-'}</td>
                  <td className="px-3 py-3 text-sm text-gray-500 truncate">{(tender.metadata as any)?.maitre_ouvrage || '-'}</td>
                  <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-500">{formatAmount((tender.metadata as any)?.montant_estime)}</td>
                  <td className="px-3 py-3 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(tender.status)}`}>{getStatusLabel(tender.status)}</span>
                  </td>
                  <td className="px-3 py-3 whitespace-nowrap text-xs text-gray-500">{new Date(tender.submitted_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!loading && tenders.length > 0 && (
        <div className="bg-white shadow rounded-lg p-4">
          <div className="flex items-center justify-between">
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">{t('tenders.previous')}</button>
            <span className="text-sm text-gray-700">{t('tenders.page')} {page} {totalPages > 1 && `${t('tenders.of')} ${totalPages}`}</span>
            <button onClick={() => setPage(p => p + 1)} disabled={page >= totalPages} className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">{t('tenders.next')}</button>
          </div>
        </div>
      )}
    </div>
  )
}
