import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { LanguageProvider } from './i18n/LanguageContext'
import Layout from './components/Layout'
import ClaimsListPage from './pages/ClaimsListPage'
import ClaimDetailPage from './pages/ClaimDetailPage'
import TendersListPage from './pages/TendersListPage'
import TenderDetailPage from './pages/TenderDetailPage'
import HomePage from './pages/HomePage'
import ChatPage from './pages/ChatPage'
import AdminPage from './pages/AdminPage'

function App() {
  return (
    <LanguageProvider>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/chat/:sessionId" element={<ChatPage />} />
            <Route path="/claims" element={<ClaimsListPage />} />
            <Route path="/claims/:claimId" element={<ClaimDetailPage />} />
            <Route path="/tenders" element={<TendersListPage />} />
            <Route path="/tenders/:tenderId" element={<TenderDetailPage />} />
            <Route path="/admin" element={<AdminPage />} />
          </Routes>
        </Layout>
      </Router>
    </LanguageProvider>
  )
}

export default App
