import { useState } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const navItems = [
  { label: 'Home', path: '/' },
  { label: 'Tours', path: '/tours' },
]

function Navbar({ darkMode, onToggleDarkMode }) {
  const { user, logout } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <header className="fixed inset-x-0 top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur-xl dark:border-slate-700 dark:bg-slate-950/95">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-3 py-3 sm:px-6">
        <Link to="/" className="flex min-w-0 items-center gap-3 font-semibold text-slate-900 dark:text-slate-100">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-forest text-white shadow-card sm:h-11 sm:w-11">KE</div>
          <div className="min-w-0">
            <p className="truncate text-base sm:text-lg">Kaimur Explorer</p>
            <p className="truncate text-xs text-slate-500 dark:text-slate-400 sm:text-sm">Nature, heritage & adventure</p>
          </div>
        </Link>

        <div className="flex items-center gap-2 sm:gap-3">
          <button
            type="button"
            onClick={onToggleDarkMode}
            className="rounded-full border border-slate-200 bg-slate-100 px-3 py-2 text-sm text-slate-700 transition hover:bg-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
          >
            {darkMode ? '🌙' : '☀️'}
          </button>
          <button
            type="button"
            onClick={() => setMenuOpen((prev) => !prev)}
            className="rounded-full border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 md:hidden"
          >
            Menu
          </button>
        </div>

        <nav className="hidden w-full items-center justify-end gap-5 md:flex md:w-auto">
          {navItems.map((item) => (
            <NavLink key={item.path} to={item.path} className={({ isActive }) => isActive ? 'text-forest font-semibold' : 'text-slate-600 hover:text-slate-900'}>
              {item.label}
            </NavLink>
          ))}
          {user?.is_admin && (
            <NavLink to="/admin" className={({ isActive }) => isActive ? 'text-forest font-semibold' : 'text-slate-600 hover:text-slate-900'}>
              Admin
            </NavLink>
          )}
          {user ? (
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium text-slate-600 dark:text-slate-300">Welcome, {user.name}</span>
              <button onClick={logout} className="text-sm font-medium text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white">Logout</button>
            </div>
          ) : (
            <Link to="/login" className="text-sm font-medium text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white">Login</Link>
          )}
        </nav>

        {menuOpen && (
          <nav className="flex w-full flex-col gap-3 border-t border-slate-200 pt-3 text-sm dark:border-slate-700 md:hidden">
            {navItems.map((item) => (
              <NavLink key={item.path} to={item.path} onClick={() => setMenuOpen(false)} className={({ isActive }) => isActive ? 'font-semibold text-forest' : 'text-slate-600 hover:text-slate-900 dark:text-slate-300'}>
                {item.label}
              </NavLink>
            ))}
            {user?.is_admin && (
              <NavLink to="/admin" onClick={() => setMenuOpen(false)} className={({ isActive }) => isActive ? 'font-semibold text-forest' : 'text-slate-600 hover:text-slate-900 dark:text-slate-300'}>
                Admin
              </NavLink>
            )}
            {user ? (
              <>
                <span className="text-slate-600 dark:text-slate-300">Welcome, {user.name}</span>
                <button onClick={() => { logout(); setMenuOpen(false) }} className="text-left font-medium text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white">Logout</button>
              </>
            ) : (
              <Link to="/login" onClick={() => setMenuOpen(false)} className="font-medium text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white">Login</Link>
            )}
          </nav>
        )}
      </div>
    </header>
  )
}

export default Navbar
