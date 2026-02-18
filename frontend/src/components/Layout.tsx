import { Link, useLocation } from 'react-router-dom'
import { ReactNode } from 'react'
import { useTranslation } from '../i18n/LanguageContext'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const isChatPage = location.pathname.startsWith('/chat')
  const { locale, setLocale, t } = useTranslation()

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/' ? 'bg-blue-700' : ''
    return location.pathname.startsWith(path) ? 'bg-blue-700' : ''
  }

  return (
    <div className={`bg-gray-50 ${isChatPage ? 'h-screen flex flex-col' : 'min-h-screen'}`}>
      {/* Navigation */}
      <nav className="bg-blue-600 text-white shadow-lg flex-shrink-0">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-14">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <h1 className="text-xl font-bold">{t('nav.title')}</h1>
              </div>
              <div className="hidden sm:ml-6 sm:flex sm:space-x-4 items-center">
                <Link
                  to="/"
                  className={`${isActive('/')} inline-flex items-center px-3 py-1.5 text-sm font-medium rounded-md hover:bg-blue-700 transition-colors`}
                >
                  {t('nav.dashboard')}
                </Link>
                <Link
                  to="/chat"
                  className={`${isActive('/chat')} inline-flex items-center px-3 py-1.5 text-sm font-medium rounded-md hover:bg-blue-700 transition-colors`}
                >
                  {t('nav.chat')}
                </Link>
                <Link
                  to="/claims"
                  className={`${isActive('/claims')} inline-flex items-center px-3 py-1.5 text-sm font-medium rounded-md hover:bg-blue-700 transition-colors`}
                >
                  {t('nav.claims')}
                </Link>
                <Link
                  to="/tenders"
                  className={`${isActive('/tenders')} inline-flex items-center px-3 py-1.5 text-sm font-medium rounded-md hover:bg-blue-700 transition-colors`}
                >
                  {t('nav.tenders')}
                </Link>
                <Link
                  to="/admin"
                  className={`${isActive('/admin')} inline-flex items-center px-3 py-1.5 text-sm font-medium rounded-md hover:bg-blue-700 transition-colors`}
                >
                  {t('nav.admin')}
                </Link>
              </div>
            </div>
            {/* Language Toggle */}
            <div className="flex items-center">
              <div className="flex bg-blue-700 rounded-md overflow-hidden">
                <button
                  onClick={() => setLocale('fr')}
                  className={`px-2.5 py-1 text-xs font-semibold transition-colors ${
                    locale === 'fr'
                      ? 'bg-white text-blue-700'
                      : 'text-blue-200 hover:text-white'
                  }`}
                >
                  FR
                </button>
                <button
                  onClick={() => setLocale('en')}
                  className={`px-2.5 py-1 text-xs font-semibold transition-colors ${
                    locale === 'en'
                      ? 'bg-white text-blue-700'
                      : 'text-blue-200 hover:text-white'
                  }`}
                >
                  EN
                </button>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      {isChatPage ? (
        <main className="flex-1 overflow-hidden px-4 py-3">
          {children}
        </main>
      ) : (
        <>
          <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
            {children}
          </main>
          <footer className="bg-white border-t border-gray-200 mt-12">
            <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
              <p className="text-center text-sm text-gray-500">
                {t('footer.text')}
              </p>
            </div>
          </footer>
        </>
      )}
    </div>
  )
}
