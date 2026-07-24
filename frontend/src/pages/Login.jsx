import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const emailSchema = z.object({ email: z.string().email() })
const otpSchema = z.object({ email: z.string().email(), otp: z.string().length(6) })

function Login() {
  const [otpSent, setOtpSent] = useState(false)
  const [serverMessage, setServerMessage] = useState('')
  const [error, setError] = useState('')
  const { requestOtp, login } = useAuth()
  const navigate = useNavigate()

  const { register, handleSubmit, formState: { errors }, watch } = useForm({ resolver: zodResolver(otpSent ? otpSchema : emailSchema) })

  const onSubmit = async (data) => {
    setError('')
    setServerMessage('')
    try {
      if (!otpSent) {
        await requestOtp(data.email)
        setOtpSent(true)
        setServerMessage('OTP request sent. Check your email and enter the code below.')
      } else {
        await login(data.email, data.otp)
        navigate('/dashboard')
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to proceed. Please try again.')
    }
  }

  return (
    <section className="mx-auto max-w-3xl px-4 py-20 sm:px-6">
      <div className="rounded-[2rem] border border-slate-200 bg-white p-8 shadow-card">
        <div className="mb-8">
          <p className="text-sm uppercase tracking-[0.35em] text-slate-400">Secure Login</p>
          <h1 className="mt-3 text-3xl font-semibold text-slate-900">Login with Email OTP</h1>
          <p className="mt-3 text-slate-600">Enter your email to receive a one-time password. Admin login is available with admin@kaimurexplorer.com.</p>
        </div>
        {serverMessage && <div className="mb-4 rounded-3xl border border-forest/20 bg-forest/10 px-4 py-3 text-sm text-forest">{serverMessage}</div>}
        {error && <div className="mb-4 rounded-3xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
        <form onSubmit={handleSubmit(onSubmit)} className="grid gap-5">
          <label className="grid gap-2 text-sm font-medium text-slate-700">
            Email address
            <input type="email" {...register('email')} className="rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900" placeholder="you@example.com" />
            {errors.email && <span className="text-sm text-red-600">{errors.email.message}</span>}
          </label>
          {otpSent && (
            <label className="grid gap-2 text-sm font-medium text-slate-700">
              OTP code
              <input type="text" maxLength="6" {...register('otp')} className="rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900" placeholder="123456" />
              {errors.otp && <span className="text-sm text-red-600">{errors.otp.message}</span>}
            </label>
          )}
          <button type="submit" className="rounded-full bg-river px-6 py-3 text-sm font-semibold text-white transition hover:bg-blue-600">
            {otpSent ? 'Verify OTP' : 'Send OTP'}
          </button>
        </form>
      </div>
    </section>
  )
}

export default Login
