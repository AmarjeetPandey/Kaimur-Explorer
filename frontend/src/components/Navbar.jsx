import { Link, NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const navItems = [
  { label: 'Home', path: '/' },
  { label: 'Tours', path: '/tours' },
]

function Navbar({ darkMode, onToggleDarkMode }) {
  const { user, logout } = useAuth()

  return (
    <header className="fixed inset-x-0 top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur-xl dark:border-slate-700 dark:bg-slate-950/95">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-6 px-4 py-4 sm:px-6">
        <Link to="/" className="flex items-center gap-3 font-semibold text-slate-900 dark:text-slate-100">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-forest text-white shadow-card">KE</div>
          <div>
            <p className="text-lg">Kaimur Explorer</p>
            <p className="text-sm text-slate-500 dark:text-slate-400">Nature, heritage & adventure</p>
          </div>
        </Link>
        <nav className="hidden items-center gap-5 md:flex">
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
        </nav>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onToggleDarkMode}
            className="rounded-full border border-slate-200 bg-slate-100 px-3 py-2 text-sm text-slate-700 transition hover:bg-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
          >
            {darkMode ? '🌙 Dark' : '☀️ Light'}
          </button>
          {user ? (
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium text-slate-600 dark:text-slate-300">Welcome, {user.name}</span>
              <button onClick={logout} className="text-sm font-medium text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white">Logout</button>
            </div>
          ) : (
            <Link to="/login" className="text-sm font-medium text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white">Login</Link>
          )}
        </div>
      </div>
    </header>
  )
}

export default Navbar
