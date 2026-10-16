import { lazy, Suspense } from 'react'
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom'
import { AuthProvider, Guard } from './auth/AuthContext'
import { AppShell } from './components/layout/AppShell'
import { PageLoader } from './components/ui/Feedback'
import { DOMAINS } from './domains'
import { LanguageProvider } from './i18n/LanguageContext'
import { PlatformProvider } from './theme/PlatformContext'
import { ThemeProvider } from './theme/ThemeContext'

const HomePage = lazy(() => import('./pages/HomePage'))
const ChatPage = lazy(() => import('./pages/ChatPage'))
const CaseListPage = lazy(() => import('./pages/CaseListPage'))
const CaseDetailPage = lazy(() => import('./pages/CaseDetailPage'))
const ReviewInboxPage = lazy(() => import('./pages/ReviewInboxPage'))
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
                    {/* the pages of each business domain (src/domains) */}
                    {Object.values(DOMAINS).flatMap((ui) => [
                      <Route key={ui.name} path={ui.path} element={<Guard domain={ui.name}><CaseListPage domain={ui.name} /></Guard>} />,
                      <Route key={`${ui.name}-case`} path={`${ui.path}/:id`} element={<Guard domain={ui.name}><CaseDetailPage domain={ui.name} /></Guard>} />,
                    ])}
                    <Route path="/review" element={<ReviewInboxPage />} />
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
