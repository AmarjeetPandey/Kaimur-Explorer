import { useEffect, useState } from 'react'
import api from '../utils/api'
import { useAuth } from '../context/AuthContext'

function Profile() {
  const { user } = useAuth()
  const [bookings, setBookings] = useState([])

  useEffect(() => {
    if (!user) return
    api.get('/api/bookings').then((res) => setBookings(res.data)).catch(() => {})
  }, [user])

  return (
    <section className="mx-auto max-w-6xl px-4 pb-20 pt-10 sm:px-6">
      <div className="mb-10 rounded-[2rem] bg-white p-8 shadow-card">
        <h1 className="text-3xl font-semibold text-slate-900">Hi, {user?.name}</h1>
        <p className="mt-3 text-slate-600">Your upcoming bookings and trip planning dashboard.</p>
      </div>
      <div className="grid gap-6">
        {bookings.length === 0 ? (
          <div className="rounded-[2rem] bg-white p-8 text-slate-600 shadow-card">You have no bookings yet. Explore tours and reserve your next Kaimur adventure.</div>
        ) : (
          bookings.map((booking) => (
            <div key={booking.id} className="rounded-[2rem] bg-white p-6 shadow-card">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm uppercase tracking-[0.3em] text-slate-400">Booking #{booking.id}</p>
                  <h2 className="mt-2 text-2xl font-semibold text-slate-900">{booking.tour.name}</h2>
                </div>
                <span className={`rounded-full px-4 py-2 text-sm font-semibold ${booking.status === 'Pending' ? 'bg-slate-100 text-slate-700' : 'bg-forest/10 text-forest'}`}>{booking.status}</span>
              </div>
              <div className="mt-5 grid gap-4 sm:grid-cols-2">
                <p><strong>Travel dates:</strong> {booking.start_date} - {booking.end_date}</p>
                <p><strong>Guests:</strong> {booking.adults} adults, {booking.kids} kids</p>
              </div>
              <p className="mt-4 text-slate-600"><strong>Special requests:</strong> {booking.special_requests || 'None'}</p>
            </div>
          ))
        )}
      </div>
    </section>
  )
}

export default Profile
