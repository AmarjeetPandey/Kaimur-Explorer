import { Route, Routes } from 'react-router-dom'
import { useEffect, useState } from 'react'
import Home from './pages/Home'
import Tours from './pages/Tours'
import TourDetail from './pages/TourDetail'
import Login from './pages/Login'
import AdminPanel from './pages/AdminPanel'
import AdminRoute from './components/AdminRoute'
import Navbar from './components/Navbar'
import Footer from './components/Footer'

function App() {
  const [darkMode, setDarkMode] = useState(false)

  useEffect(() => {
    // Clear authentication token and refresh only on first visit
    const hasVisited = sessionStorage.getItem('kaimur_visited')
    if (!hasVisited) {
      localStorage.removeItem('kaimur_token')
      sessionStorage.setItem('kaimur_visited', 'true')
      window.location.reload()
    }
  }, [])

  useEffect(() => {
    const storedMode = localStorage.getItem('kaimur_dark_mode')
    const initialMode = storedMode !== null ? storedMode === 'true' : false
    setDarkMode(initialMode)
  }, [])

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark')
      localStorage.setItem('kaimur_dark_mode', 'true')
    } else {
      document.documentElement.classList.remove('dark')
      localStorage.setItem('kaimur_dark_mode', 'false')
    }
  }, [darkMode])

  return (
    <div className={`min-h-screen overflow-x-hidden bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100`}>
      <Navbar darkMode={darkMode} onToggleDarkMode={() => setDarkMode((prev) => !prev)} />
      <main className="pt-24 px-2 sm:px-4 lg:px-6">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/tours" element={<Tours />} />
          <Route path="/tours/:id" element={<TourDetail />} />
          <Route path="/login" element={<Login />} />
          <Route path="/admin" element={<AdminRoute><AdminPanel /></AdminRoute>} />
        </Routes>
      </main>
      <Footer />
    </div>
  )
}

export default App
