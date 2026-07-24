import { useEffect, useState } from 'react'
import TourCard from '../components/TourCard'
import api from '../utils/api'

function Tours() {
  const [tours, setTours] = useState([])

  useEffect(() => {
    api.get('/api/tours').then((res) => setTours(res.data)).catch(() => {})
  }, [])

  return (
    <section className="mx-auto max-w-7xl px-4 pb-20 pt-10 sm:px-6">
      <div className="mb-10 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm uppercase tracking-[0.35em] text-slate-400">Tour Packages</p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-900">All Kaimur tour experiences</h1>
        </div>
        <p className="max-w-2xl text-sm text-slate-600">Choose from heritage temples, waterfalls, wildlife, river tours and curated day trips with transparent pricing.</p>
      </div>
      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
        {tours.map((tour) => (
          <TourCard key={tour.id} tour={tour} />
        ))}
      </div>
    </section>
  )
}

export default Tours
