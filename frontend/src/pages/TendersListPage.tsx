import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { tendersApi } from '../services/tenderApi'
import type { Tender, TenderStatus } from '../types/tender'

export default function TendersListPage() {
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
          t.objet_marche?.toLowerCase().includes(query) ||
          t.maitre_ouvrage?.toLowerCase().includes(query)
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

  const formatDate = (dateString: string) => new Date(dateString).toLocaleString()

  const formatAmount = (amount: number | null | undefined) => {
    if (!amount) return '-'
    return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(amount)
  }

  return (
    <div className="space-y-6">
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-3xl font-bold text-gray-900">Appels d'Offres</h2>
            <p className="mt-2 text-gray-600">Analyse et suivi des appels d'offres BTP</p>
          </div>
          <button
            onClick={loadTenders}
            className="bg-amber-600 hover:bg-amber-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
          >
            Rafraichir
          </button>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2">
            <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">Rechercher</label>
            <input
              id="search"
              type="text"
              placeholder="N AO, maitre d'ouvrage, objet..."
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setPage(1) }}
              className="block w-full pl-3 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-amber-500 focus:border-amber-500 sm:text-sm"
            />
          </div>
          <div>
            <label htmlFor="status-filter" className="block text-sm font-medium text-gray-700 mb-1">Statut</label>
            <select
              id="status-filter"
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value as TenderStatus | ''); setPage(1) }}
              className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-amber-500 focus:border-amber-500 rounded-md"
            >
              <option value="">Tous</option>
              <option value="pending">En attente</option>
              <option value="processing">En cours</option>
              <option value="completed">Termine</option>
              <option value="failed">Echoue</option>
              <option value="manual_review">A approfondir</option>
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
          <h3 className="mt-2 text-sm font-medium text-gray-900">Aucun appel d'offres</h3>
          <p className="mt-1 text-sm text-gray-500">
            {statusFilter || searchQuery ? "Essayez d'ajuster vos filtres" : 'Aucun AO dans le systeme'}
          </p>
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden rounded-lg">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" onClick={() => setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')}>N AO</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Objet</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Maitre d'Ouvrage</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Montant</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Statut</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Soumis</th>
                <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {tenders.map((tender) => (
                <tr key={tender.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{tender.tender_number}</td>
                  <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">{tender.objet_marche || 'N/A'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{tender.maitre_ouvrage || 'N/A'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatAmount(tender.montant_estime)}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(tender.status)}`}>{tender.status}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatDate(tender.submitted_at)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <Link to={`/tenders/${tender.id}`} className="text-amber-600 hover:text-amber-900">Voir</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!loading && tenders.length > 0 && (
        <div className="bg-white shadow rounded-lg p-4">
          <div className="flex items-center justify-between">
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">Precedent</button>
            <span className="text-sm text-gray-700">Page {page} {totalPages > 1 && `sur ${totalPages}`}</span>
            <button onClick={() => setPage(p => p + 1)} disabled={page >= totalPages} className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">Suivant</button>
          </div>
        </div>
      )}
    </div>
  )
}
