import { lazy, Suspense } from 'react'
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom'
import { AuthProvider, Guard } from './auth/AuthContext'
import { AppShell } from './components/layout/AppShell'
import { PageLoader } from './components/ui/Feedback'
import { LanguageProvider } from './i18n/LanguageContext'
import { PlatformProvider } from './theme/PlatformContext'
import { ThemeProvider } from './theme/ThemeContext'

const HomePage = lazy(() => import('./pages/HomePage'))
const ChatPage = lazy(() => import('./pages/ChatPage'))
const ClaimsListPage = lazy(() => import('./pages/ClaimsListPage'))
const ClaimDetailPage = lazy(() => import('./pages/ClaimDetailPage'))
const TendersListPage = lazy(() => import('./pages/TendersListPage'))
const TenderDetailPage = lazy(() => import('./pages/TenderDetailPage'))
const PostalListPage = lazy(() => import('./pages/PostalListPage'))
const PostalDetailPage = lazy(() => import('./pages/PostalDetailPage'))
const AdminPage = lazy(() => import('./pages/AdminPage'))
const SandboxPage = lazy(() => import('./pages/SandboxPage'))

export default function App() {
  return (
    <ThemeProvider>
      <LanguageProvider>
        <PlatformProvider>
          <AuthProvider>
          <Router>
            <AppShell>
              <Suspense fallback={<PageLoader />}>
                <Routes>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/chat" element={<ChatPage />} />
                  <Route path="/chat/:sessionId" element={<ChatPage />} />
                  <Route path="/claims" element={<Guard domain="claims"><ClaimsListPage /></Guard>} />
                  <Route path="/claims/:claimId" element={<Guard domain="claims"><ClaimDetailPage /></Guard>} />
                  <Route path="/tenders" element={<Guard domain="tenders"><TendersListPage /></Guard>} />
                  <Route path="/tenders/:tenderId" element={<Guard domain="tenders"><TenderDetailPage /></Guard>} />
                  <Route path="/postal" element={<Guard domain="postal"><PostalListPage /></Guard>} />
                  <Route path="/postal/:reclamationId" element={<Guard domain="postal"><PostalDetailPage /></Guard>} />
                  <Route path="/sandbox" element={<SandboxPage />} />
                  <Route path="/admin" element={<Guard admin><AdminPage /></Guard>} />
                </Routes>
              </Suspense>
            </AppShell>
          </Router>
          </AuthProvider>
        </PlatformProvider>
      </LanguageProvider>
    </ThemeProvider>
  )
}
