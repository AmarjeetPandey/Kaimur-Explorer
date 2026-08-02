import { useEffect, useState } from 'react'
import api from '../utils/api'

const sections = ['Stats', 'Bookings', 'Tours', 'Users']
const defaultTourForm = {
  name: '',
  short_description: '',
  full_description: '',
  itinerary: '',
  included: '',
  price: 0,
  duration: '1 day',
  image_urls: [],
  video_urls: [],
  front_media_url: null,
}

function AdminPanel() {
  const [activeTab, setActiveTab] = useState('Stats')
  const [stats, setStats] = useState(null)
  const [bookings, setBookings] = useState([])
  const [tours, setTours] = useState([])
  const [users, setUsers] = useState([])
  const [tourForm, setTourForm] = useState(defaultTourForm)
  const [editingTourId, setEditingTourId] = useState(null)
  const [message, setMessage] = useState('')

  const normalizeMediaUrl = (url) => {
    if (!url) return url
    return url.startsWith('http') ? url : `https://kaimur-explorer.onrender.com${url}`
  }

  const handleMediaUpload = async (e) => {
    const files = Array.from(e.target.files)
    if (!files.length) return

    const newImages = []
    const newVideos = []

    for (const file of files) {
      const formData = new FormData()
      formData.append('file', file)
      try {
        const endpoint = file.type.startsWith('video/') ? '/api/admin/upload-video' : '/api/admin/upload-image'
        const res = await api.post(endpoint, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        if (file.type.startsWith('video/')) {
          newVideos.push(res.data.url)
        } else {
          newImages.push(res.data.url)
        }
      } catch (err) {
        console.error('Upload failed', err)
      }
    }

    if (newImages.length > 0 || newVideos.length > 0) {
      setTourForm(prev => ({
        ...prev,
        image_urls: [...(prev.image_urls || []), ...newImages],
        video_urls: [...(prev.video_urls || []), ...newVideos],
      }))
      setMessage('Media uploaded successfully!')
    } else {
      setMessage('Failed to upload media')
    }
  }

  const handleEditTour = (tour) => {
    setEditingTourId(tour.id)
    setTourForm({
      name: tour.name || '',
      short_description: tour.short_description || '',
      full_description: tour.full_description || '',
      itinerary: tour.itinerary || '',
      included: tour.included || '',
      price: tour.price || 0,
      duration: tour.duration || '1 day',
      image_urls: tour.image_urls || [],
      video_urls: tour.video_urls || [],
      front_media_url: tour.front_media_url || null,
    })
    setMessage('Editing tour ID ' + tour.id)
  }

  const handleCancelEdit = () => {
    setEditingTourId(null)
    setTourForm(defaultTourForm)
    setMessage('')
  }

  const handleSaveTour = async (e) => {
    e.preventDefault()
    const payload = {
      ...tourForm,
      image_urls: tourForm.image_urls || [],
      video_urls: tourForm.video_urls || [],
      front_media_url: tourForm.front_media_url || null,
    }
    try {
      if (editingTourId) {
        await api.put(`/api/admin/tours/${editingTourId}`, payload)
        setMessage('Tour updated successfully.')
      } else {
        await api.post('/api/admin/tours', payload)
        setMessage('Tour created successfully.')
      }
      setEditingTourId(null)
      setTourForm(defaultTourForm)
      const res = await api.get('/api/tours')
      setTours(res.data)
    } catch (err) {
      setMessage('Failed to save tour. Please check all fields.')
    }
  }

  const handleSelectFrontMedia = (url) => {
    setTourForm((prev) => ({
      ...prev,
      front_media_url: url,
    }))
  }

  useEffect(() => {
    api.get('/api/admin/stats').then((res) => setStats(res.data)).catch(() => {})
    api.get('/api/admin/bookings').then((res) => setBookings(res.data)).catch(() => {})
    api.get('/api/tours').then((res) => setTours(res.data)).catch(() => {})
    api.get('/api/admin/users').then((res) => setUsers(res.data)).catch(() => {})
  }, [])


  const handleApprove = async (id) => {
    await api.put(`/api/admin/bookings/${id}`, { status: 'Approved' })
    setMessage('Booking approved successfully.')
    setBookings((prev) => prev.map((booking) => booking.id === id ? { ...booking, status: 'Approved' } : booking))
  }

  const handleReject = async (id) => {
    await api.put(`/api/admin/bookings/${id}`, { status: 'Rejected' })
    setMessage('Booking rejected successfully.')
    setBookings((prev) => prev.map((booking) => booking.id === id ? { ...booking, status: 'Rejected' } : booking))
  }

  const handleDeleteUser = async (id) => {
    try {
      await api.delete(`/api/admin/users/${id}`)
      setUsers((prev) => prev.filter((user) => user.id !== id))
      setMessage('User deleted successfully.')
    } catch (err) {
      setMessage('Failed to delete user. Please try again.')
      console.error('Delete user error:', err)
    }
  }

  const handleDeleteTour = async (id) => {
    try {
      await api.delete(`/api/admin/tours/${id}`)
      setTours((prev) => prev.filter((tour) => tour.id !== id))
      setMessage('Tour deleted successfully.')
    } catch (err) {
      setMessage('Failed to delete tour. Please try again.')
      console.error('Delete tour error:', err)
    }
  }

  const handleCreateTour = async (e) => {
    await handleSaveTour(e)
  }

  return (
    <section className="mx-auto max-w-7xl px-4 pb-20 pt-10 sm:px-6">
      <div className="mb-8 rounded-[2rem] bg-white p-8 shadow-card">
        <p className="text-sm uppercase tracking-[0.35em] text-slate-400">Admin Dashboard</p>
        <h1 className="mt-2 text-3xl font-semibold text-slate-900">Manage Kaimur Explorer</h1>
        <p className="mt-4 max-w-2xl text-slate-600">Full control over tours, bookings, users and platform analytics.</p>
      </div>
      <div className="mb-8 flex flex-wrap items-center gap-3">
        {sections.map((section) => (
          <button key={section} onClick={() => setActiveTab(section)} className={`rounded-full px-5 py-3 text-sm font-semibold transition ${activeTab === section ? 'bg-forest text-white' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'}`}>
            {section}
          </button>
        ))}
      </div>
      {message && <div className="mb-6 rounded-3xl bg-forest/10 px-5 py-4 text-sm text-forest">{message}</div>}
      {activeTab === 'Stats' && stats && (
        <div className="grid gap-6 lg:grid-cols-3">
          {['total_users','total_tours','total_bookings','pending_bookings','approved_bookings'].map((key) => (
            <div key={key} className="rounded-[2rem] bg-white p-6 shadow-card">
              <p className="text-sm uppercase tracking-[0.3em] text-slate-400">{key.replace(/_/g, ' ')}</p>
              <p className="mt-4 text-4xl font-semibold text-slate-900">{stats[key]}</p>
            </div>
          ))}
        </div>
      )}
      {activeTab === 'Bookings' && (
        <div className="overflow-hidden rounded-[2rem] bg-white shadow-card">
          <table className="min-w-full divide-y divide-slate-200 text-left text-sm text-slate-700">
            <thead className="bg-slate-50 text-slate-500">
              <tr>
                <th className="px-6 py-4">ID</th>
                <th className="px-6 py-4">Tour</th>
                <th className="px-6 py-4">Guest</th>
                <th className="px-6 py-4">Dates</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 bg-white">
              {bookings.map((booking) => (
                <tr key={booking.id}>
                  <td className="px-6 py-4">{booking.id}</td>
                  <td className="px-6 py-4">{booking.tour.name}</td>
                  <td className="px-6 py-4">{booking.name}</td>
                  <td className="px-6 py-4">{booking.start_date} → {booking.end_date}</td>
                  <td className="px-6 py-4">{booking.status}</td>
                  <td className="px-6 py-4 space-x-2">
                    <button onClick={() => handleApprove(booking.id)} className="rounded-full bg-forest px-4 py-2 text-xs font-semibold text-white">Approve</button>
                    <button onClick={() => handleReject(booking.id)} className="rounded-full bg-red-500 px-4 py-2 text-xs font-semibold text-white">Reject</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {activeTab === 'Tours' && (
        <div className="space-y-8">
          <form onSubmit={handleCreateTour} className="grid gap-4 rounded-[2rem] bg-white p-6 shadow-card">
            <h2 className="text-xl font-semibold text-slate-900">Add new tour</h2>
            {['name','short_description','full_description','itinerary','included','duration'].map((key) => (
              <label key={key} className="grid gap-2 text-sm font-medium text-slate-700">
                {key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                <input type="text" value={tourForm[key]} onChange={(e) => setTourForm((prev) => ({ ...prev, [key]: e.target.value }))} className="rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3" />
              </label>
            ))}
            <label className="grid gap-2 text-sm font-medium text-slate-700">
              Price
              <input type="number" value={tourForm.price} onChange={(e) => setTourForm((prev) => ({ ...prev, price: Number(e.target.value) }))} className="rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3" />
            </label>
            <label className="grid gap-2 text-sm font-medium text-slate-700">
              Upload Photos & Videos
              <input type="file" accept="image/*,video/*" multiple onChange={handleMediaUpload} className="rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3" />
            </label>
            <div className="text-sm text-slate-600">
              <p>Uploaded images: {(tourForm.image_urls || []).length}</p>
              <p>Uploaded videos: {(tourForm.video_urls || []).length}</p>
              {((tourForm.image_urls || []).length > 0 || (tourForm.video_urls || []).length > 0) && (
                <div className="mt-2">
                  <p className="font-medium">Media Previews:</p>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {(tourForm.image_urls || []).map((url, index) => (
                      <div key={`image-${index}`} className="relative">
                        <button
                          type="button"
                          onClick={() => handleSelectFrontMedia(url)}
                          className={`absolute right-1 top-1 rounded-full px-2 py-1 text-[10px] font-semibold text-white ${tourForm.front_media_url === url ? 'bg-forest' : 'bg-slate-700/90 hover:bg-slate-700'}`}
                        >
                          {tourForm.front_media_url === url ? 'Selected' : 'Set Front'}
                        </button>
                        <img src={normalizeMediaUrl(url)} alt={`Image ${index}`} className="w-20 h-20 object-cover rounded" />
                      </div>
                    ))}
                    {(tourForm.video_urls || []).map((url, index) => (
                      <div key={`video-${index}`} className="relative">
                        <button
                          type="button"
                          onClick={() => handleSelectFrontMedia(url)}
                          className={`absolute right-1 top-1 rounded-full px-2 py-1 text-[10px] font-semibold text-white ${tourForm.front_media_url === url ? 'bg-forest' : 'bg-slate-700/90 hover:bg-slate-700'}`}
                        >
                          {tourForm.front_media_url === url ? 'Selected' : 'Set Front'}
                        </button>
                        <video src={normalizeMediaUrl(url)} className="w-20 h-20 object-cover rounded" />
                      </div>
                    ))}
                  </div>
                  {tourForm.front_media_url && (
                    <p className="mt-2 text-xs text-slate-500">Selected front media is highlighted and will be shown on the tour card.</p>
                  )}
                </div>
              )}
            </div>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <button type="submit" className="w-full rounded-full bg-river px-6 py-3 text-sm font-semibold text-white hover:bg-blue-600 sm:w-auto">
                {editingTourId ? 'Update Tour' : 'Create Tour'}
              </button>
              {editingTourId && (
                <button type="button" onClick={handleCancelEdit} className="w-full rounded-full border border-slate-200 bg-white px-6 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-100 sm:w-auto">
                  Cancel Edit
                </button>
              )}
            </div>
          </form>
          <div className="overflow-hidden rounded-[2rem] bg-white shadow-card">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm text-slate-700">
              <thead className="bg-slate-50 text-slate-500">
                <tr>
                  <th className="px-6 py-4">ID</th>
                  <th className="px-6 py-4">Name</th>
                  <th className="px-6 py-4">Price</th>
                  <th className="px-6 py-4">Duration</th>
                  <th className="px-6 py-4">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white">
                {tours.map((tour) => (
                  <tr key={tour.id}>
                    <td className="px-6 py-4">{tour.id}</td>
                    <td className="px-6 py-4">{tour.name}</td>
                    <td className="px-6 py-4">₹{tour.price}</td>
                    <td className="px-6 py-4">{tour.duration}</td>
                    <td className="px-6 py-4 space-x-2">
                      <button onClick={() => handleEditTour(tour)} className="rounded-full bg-forest px-4 py-2 text-xs font-semibold text-white">Edit</button>
                      <button onClick={() => handleDeleteTour(tour.id)} className="rounded-full bg-red-500 px-4 py-2 text-xs font-semibold text-white">Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      {activeTab === 'Users' && (
        <div className="overflow-hidden rounded-[2rem] bg-white shadow-card">
          <table className="min-w-full divide-y divide-slate-200 text-left text-sm text-slate-700">
            <thead className="bg-slate-50 text-slate-500">
              <tr>
                <th className="px-6 py-4">ID</th>
                <th className="px-6 py-4">Email</th>
                <th className="px-6 py-4">Active</th>
                <th className="px-6 py-4">Admin</th>
                <th className="px-6 py-4">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 bg-white">
              {users.map((user) => (
                <tr key={user.id}>
                  <td className="px-6 py-4">{user.id}</td>
                  <td className="px-6 py-4">{user.email}</td>
                  <td className="px-6 py-4">{String(user.is_active)}</td>
                  <td className="px-6 py-4">{String(user.is_admin)}</td>
                  <td className="px-6 py-4">
                    <button onClick={() => handleDeleteUser(user.id)} className="rounded-full bg-red-500 px-4 py-2 text-xs font-semibold text-white">Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

export default AdminPanel
