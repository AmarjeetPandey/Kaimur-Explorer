import { createContext, useContext, useEffect, useState } from 'react'
import api from '../utils/api'

const AuthContext = createContext({})

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const savedToken = localStorage.getItem('kaimur_token')
    const savedUser = localStorage.getItem('kaimur_user')
    if (savedToken && savedUser) {
      setUser(JSON.parse(savedUser))
    }
    setIsLoading(false)
  }, [])

  const login = async (email, otp) => {
    const response = await api.post('/api/auth/verify-otp', { email, otp })
    localStorage.setItem('kaimur_token', response.data.access_token)
    localStorage.setItem('kaimur_user', JSON.stringify(response.data.user))
    setUser(response.data.user)
    return response.data.user
  }

  const requestOtp = async (email) => {
    await api.post('/api/auth/send-otp', { email })
  }

  const logout = () => {
    localStorage.removeItem('kaimur_token')
    localStorage.removeItem('kaimur_user')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout, requestOtp }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
