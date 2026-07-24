import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function AdminRoute({ children }) {
  const { user, isLoading } = useAuth()
  if (isLoading) return null
  return user?.is_admin ? children : <Navigate to="/login" replace />
}

export default AdminRoute
