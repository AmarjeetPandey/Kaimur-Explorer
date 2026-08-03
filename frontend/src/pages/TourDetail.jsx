import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '../utils/api'

function TourDetail() {
  const { id } = useParams()
  const [tour, setTour] = useState(null)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [currentMediaIndex, setCurrentMediaIndex] = useState(0)
  const [bookingConfirmed, setBookingConfirmed] = useState(false)
  const today = new Date().toISOString().slice(0, 10)

  const normalizeMediaUrl = (url) => {
    if (!url) return url
    return url.startsWith('http') ? url : `https://kaimur-explorer.onrender.com${url}`
  }

  const media = [
    ...(tour?.image_urls || []).map(url => ({ type: 'image', url: normalizeMediaUrl(url) })),
    ...(tour?.video_urls || []).map(url => ({ type: 'video', url: normalizeMediaUrl(url) }))
  ]

  useEffect(() => {
    setCurrentMediaIndex(0)
  }, [tour?.image_urls?.length, tour?.video_urls?.length])

  const nextMedia = () => {
    setCurrentMediaIndex((prev) => (prev + 1) % media.length)
  }

  const prevMedia = () => {
    setCurrentMediaIndex((prev) => (prev - 1 + media.length) % media.length)
  }
  const [formData, setFormData] = useState({
    name: '',
    location: '',
    age: '',
    email: '',
    phone: '',
    date_of_booking: ''
  })
  const [password, setPassword] = useState('')
  const [passwordVerified, setPasswordVerified] = useState(false)
  const [passwordMessage, setPasswordMessage] = useState('')
  const [passwordError, setPasswordError] = useState('')

  // const { register, handleSubmit } = useForm()

  useEffect(() => {
    api.get(`/api/tours/${id}`).then((res) => setTour(res.data)).catch(() => {})
  }, [id])

  const onSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setMessage('')

    if (!passwordVerified) {
      setError('Please verify your email and password before confirming the booking.')
      return
    }

    const phone = formData.phone.trim().replace(/[^+0-9]/g, '')
    const phoneRegex = /^\+\d{1,3}\d{10}$/
    if (!phoneRegex.test(phone)) {
      setError('Enter a valid phone number with country code and 10 digits, e.g. +919876543210.')
      return
    }

    if (!formData.date_of_booking) {
      setError('Please select your booking date.')
      return
    }

    if (formData.date_of_booking < today) {
      setError('Booking date cannot be in the past.')
      return
    }

    try {
      await api.post('/api/bookings', { tour_id: tour.id, ...formData, phone })
      setMessage('Booking confirmed successfully! You will receive a confirmation email shortly.')
      setBookingConfirmed(true)
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to submit booking. Try again later.')
    }
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    if (name === 'email') {
      setPassword('')
      setPasswordVerified(false)
      setPasswordMessage('')
      setPasswordError('')
    }
    setFormData({ ...formData, [name]: value })
  }

  const verifyPassword = async () => {
    setError('')
    setPasswordError('')
    setPasswordMessage('')
    setPasswordVerified(false)

    if (!formData.email || !password) {
      setPasswordError('Enter your email and password to continue.')
      return
    }

    try {
      const response = await api.post('/api/auth/login', { email: formData.email, password })
      if (response.data?.access_token) {
        setPasswordVerified(true)
        setPasswordMessage('Credentials accepted. You can now confirm the booking.')
      }
    } catch (err) {
      setPasswordError(err.response?.data?.detail || 'Authentication failed. Please try again.')
    }
  }

  // Scroll to booking form if URL hash is #booking
  useEffect(() => {
    if (window.location.hash === '#booking') {
      const bookingEl = document.getElementById('booking')
      if (bookingEl) {
        setTimeout(() => bookingEl.scrollIntoView({ behavior: 'smooth' }), 100)
      }
    }
  }, [tour])

  if (!tour) return <div className="py-28 text-center text-slate-500">Loading tour details…</div>

  return (
    <section className="mx-auto max-w-7xl px-4 pb-20 pt-10 sm:px-6">
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between rounded-[2rem] bg-sun/10 p-6">
        <div>
          <h1 className="text-3xl font-semibold text-slate-900">{tour.name}</h1>
          <p className="mt-2 text-slate-600">{tour.short_description}</p>
          <div className="mt-3 inline-flex items-center rounded-full bg-sun px-5 py-2 text-lg font-semibold text-white">₹{tour.price} / person</div>
        </div>
        <a href="#booking" className="rounded-full bg-sun px-8 py-3 text-center text-sm font-semibold text-white transition hover:bg-orange-500">
          Book Now →
        </a>
      </div>
      <div className="grid gap-10 lg:grid-cols-[0.65fr_0.35fr]">
        <div className="space-y-8">
          {/* Media Carousel */}
          <div className="rounded-[2rem] overflow-hidden bg-white shadow-card relative">
            {media.length > 0 ? (
              media[currentMediaIndex].type === 'image' ? (
                <img 
                  src={media[currentMediaIndex].url} 
                  alt={tour.name}
                  className="w-full h-96 object-cover"
                />
              ) : (
                <video 
                  src={media[currentMediaIndex].url} 
                  controls
                  autoPlay
                  muted
                  loop
                  playsInline
                  className="w-full h-96 object-cover"
                />
              )
            ) : (
              <img 
                src="https://via.placeholder.com/800x400" 
                alt={tour.name}
                className="w-full h-96 object-cover"
              />
            )}
            {media.length > 1 && (
              <>
                <button onClick={prevMedia} className="absolute left-4 top-1/2 transform -translate-y-1/2 bg-black bg-opacity-50 text-white p-2 rounded-full">
                  ‹
                </button>
                <button onClick={nextMedia} className="absolute right-4 top-1/2 transform -translate-y-1/2 bg-black bg-opacity-50 text-white p-2 rounded-full">
                  ›
                </button>
              </>
            )}
          </div>
          {media.length > 1 && (
            <div className="grid gap-2 sm:grid-cols-4">
              {media.map((item, index) => (
                <button
                  key={`${item.type}-${index}`}
                  type="button"
                  onClick={() => setCurrentMediaIndex(index)}
                  className={`overflow-hidden rounded-3xl border transition duration-200 ${currentMediaIndex === index ? 'border-sun ring-2 ring-sun/50' : 'border-slate-200 hover:border-slate-400'}`}
                >
                  {item.type === 'image' ? (
                    <img src={item.url} alt={`Media ${index + 1}`} className="h-24 w-full object-cover" />
                  ) : (
                    <video src={item.url} className="h-24 w-full object-cover" />
                  )}
                </button>
              ))}
            </div>
          )}
          <div className="grid gap-6 sm:grid-cols-2">
            <div className="rounded-[2rem] bg-white p-6 shadow-card">
              <h2 className="text-xl font-semibold text-slate-900">Full Description</h2>
              <p className="mt-3 text-slate-600">{tour.full_description}</p>
            </div>
            <div className="rounded-[2rem] bg-white p-6 shadow-card">
              <h2 className="text-xl font-semibold text-slate-900">Itinerary</h2>
              <p className="mt-3 text-slate-600">{tour.itinerary}</p>
            </div>
          </div>
          <div className="rounded-[2rem] bg-white p-6 shadow-card">
            <h2 className="text-xl font-semibold text-slate-900">What's Included</h2>
            <p className="mt-3 text-slate-600">{tour.included}</p>
          </div>
        </div>
        <aside className="space-y-6">
          <div id="booking" className="rounded-[2rem] bg-white p-6 shadow-card">
            <h2 className="text-2xl font-semibold text-slate-900">Book This Tour</h2>
            <p className="mt-2 text-sm text-slate-600">Fill in your details below and your booking will be saved directly for the super admin to view and manage from the dashboard.</p>
            {error && <div className="mt-4 rounded-3xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
            {message && <div className="mt-4 rounded-3xl bg-forest/10 px-4 py-3 text-sm text-forest">{message}</div>}
            <form onSubmit={onSubmit} className="mt-6 space-y-4">
              <div className="grid gap-4">
                <label className="grid gap-2 text-sm font-medium text-slate-700">
                  Name
                  <input type="text" name="name" value={formData.name} onChange={handleChange} className="rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3" />
                </label>
                <label className="grid gap-2 text-sm font-medium text-slate-700">
                  Location
                  <input type="text" name="location" value={formData.location} onChange={handleChange} className="rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3" />
                </label>
                <label className="grid gap-2 text-sm font-medium text-slate-700">
                  Age
                  <input type="number" name="age" value={formData.age} onChange={handleChange} className="rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3" />
                </label>
                <label className="grid gap-2 text-sm font-medium text-slate-700">
                  Email
                  <div className="flex gap-3">
                    <input type="email" name="email" value={formData.email} onChange={handleChange} className="flex-1 rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3" />
                    <button type="button" onClick={verifyPassword} className="rounded-3xl bg-sun px-4 py-3 text-sm font-semibold text-white hover:bg-orange-500">
                      Verify
                    </button>
                  </div>
                </label>
                <label className="grid gap-2 text-sm font-medium text-slate-700">
                  Password
                  <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3" placeholder="Your account password" />
                  {passwordError && <span className="text-sm text-red-600">{passwordError}</span>}
                  {passwordMessage && <span className="text-sm text-forest">{passwordMessage}</span>}
                </label>
                <label className="grid gap-2 text-sm font-medium text-slate-700">
                  Mobile Number
                  <input type="tel" name="phone" value={formData.phone} onChange={handleChange} className="rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3" />
                </label>
                <label className="grid gap-2 text-sm font-medium text-slate-700">
                  Date of Booking
                  <input type="date" name="date_of_booking" value={formData.date_of_booking} min={today} onChange={handleChange} className="rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3" />
                </label>
              </div>
              <button 
                type="submit" 
                disabled={bookingConfirmed}
                className={`w-full rounded-full px-5 py-3 text-sm font-semibold text-white transition cursor-pointer ${
                  bookingConfirmed 
                    ? 'bg-green-500 hover:bg-green-600' 
                    : 'bg-sun hover:bg-orange-500'
                }`}
              >
                {bookingConfirmed ? 'Tour Booked ✓' : 'Confirm Booking'}
              </button>
            </form>
          </div>
        </aside>
      </div>
      <Link to="/tours" className="mt-10 inline-flex text-sm font-semibold text-forest hover:text-green-700">← Back to tours</Link>
    </section>
  )
}

export default TourDetail
