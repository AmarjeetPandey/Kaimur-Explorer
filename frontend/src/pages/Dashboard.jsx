import { useEffect, useState } from 'react'
import api from '../utils/api'
import { useAuth } from '../context/AuthContext'

function Dashboard() {
  const { user } = useAuth()
  const [bookings, setBookings] = useState([])

  useEffect(() => {
    api.get('/api/bookings').then((res) => setBookings(res.data)).catch(() => {})
  }, [])

  return (
    <section className="mx-auto max-w-6xl px-4 pb-20 pt-10 sm:px-6">
      <div className="mb-10 rounded-[2rem] bg-white p-8 shadow-card">
        <p className="text-sm uppercase tracking-[0.35em] text-slate-400">Traveler Dashboard</p>
        <h1 className="mt-2 text-3xl font-semibold text-slate-900">Welcome back, {user?.name}</h1>
        <p className="mt-4 max-w-2xl text-slate-600">Track your booking requests, view tour status, and manage your Kaimur experiences from one place.</p>
      </div>
      <div className="grid gap-6">
        <div className="rounded-[2rem] bg-white p-8 shadow-card">
          <h2 className="text-2xl font-semibold text-slate-900">Recent bookings</h2>
          {bookings.length === 0 ? (
            <p className="mt-5 text-slate-600">You have not booked any tours yet. Browse our packages and plan your next trip.</p>
          ) : (
            <div className="mt-6 grid gap-5">
              {bookings.map((booking) => (
                <div key={booking.id} className="rounded-3xl border border-slate-200 p-5">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p className="text-sm uppercase tracking-[0.3em] text-slate-400">{booking.tour.name}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-900">{booking.start_date} → {booking.end_date}</p>
                    </div>
                    <span className={`rounded-full px-4 py-2 text-sm font-semibold ${booking.status === 'Pending' ? 'bg-slate-100 text-slate-700' : 'bg-forest/10 text-forest'}`}>{booking.status}</span>
                  </div>
                  <p className="mt-4 text-slate-600">Guests: {booking.adults} adults, {booking.kids} kids</p>
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="rounded-[2rem] bg-white p-6 shadow-card">
            <p className="text-sm uppercase tracking-[0.35em] text-slate-400">Your profile</p>
            <p className="mt-4 text-slate-700">Email</p>
            <p className="text-lg font-semibold text-slate-900">{user?.email}</p>
          </div>
          <div className="rounded-[2rem] bg-white p-6 shadow-card">
            <p className="text-sm uppercase tracking-[0.35em] text-slate-400">User type</p>
            <p className="mt-4 text-lg font-semibold text-slate-900">{user?.is_admin ? 'Administrator' : 'Traveler'}</p>
          </div>
        </div>
      </div>
    </section>
  )
}

export default Dashboard
