import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const loginSchema = z.object({ email: z.string().email(), password: z.string().min(6) })

function Login() {
  const [serverMessage, setServerMessage] = useState('')
  const [error, setError] = useState('')
  const { login } = useAuth()
  const navigate = useNavigate()

  const { register, handleSubmit, formState: { errors } } = useForm({ resolver: zodResolver(loginSchema) })

  const onSubmit = async (data) => {
    setError('')
    setServerMessage('')
    try {
      await login(data.email, data.password)
      setServerMessage('Login successful. Redirecting to your dashboard...')
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to log in. Please try again.')
    }
  }

  return (
    <section className="mx-auto max-w-3xl px-4 py-20 sm:px-6">
      <div className="rounded-[2rem] border border-slate-200 bg-white p-8 shadow-card">
        <div className="mb-8">
          <p className="text-sm uppercase tracking-[0.35em] text-slate-400">Secure Login</p>
          <h1 className="mt-3 text-3xl font-semibold text-slate-900">Login with Email and Password</h1>
          <p className="mt-3 text-slate-600">Use your email and password to access your account. Super admin can sign in with the fixed admin account.</p>
        </div>
        {serverMessage && <div className="mb-4 rounded-3xl border border-forest/20 bg-forest/10 px-4 py-3 text-sm text-forest">{serverMessage}</div>}
        {error && <div className="mb-4 rounded-3xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
        <form onSubmit={handleSubmit(onSubmit)} className="grid gap-5">
          <label className="grid gap-2 text-sm font-medium text-slate-700">
            Email address
            <input type="email" {...register('email')} className="rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900" placeholder="you@example.com" />
            {errors.email && <span className="text-sm text-red-600">{errors.email.message}</span>}
          </label>
          <label className="grid gap-2 text-sm font-medium text-slate-700">
            Password
            <input type="password" {...register('password')} className="rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900" placeholder="Enter your password" />
            {errors.password && <span className="text-sm text-red-600">{errors.password.message}</span>}
          </label>
          <button type="submit" className="rounded-full bg-river px-6 py-3 text-sm font-semibold text-white transition hover:bg-blue-600">
            Log in
          </button>
        </form>
      </div>
    </section>
  )
}

export default Login
