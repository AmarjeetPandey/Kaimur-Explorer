import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import api from '../utils/api'
import TourCard from '../components/TourCard'

function Home() {
  const [tours, setTours] = useState([])

  useEffect(() => {
    api.get('/api/tours').then((res) => setTours(res.data.slice(0, 6))).catch(() => {})
  }, [])

  return (
    <section className="mx-auto max-w-7xl px-2 pb-20 pt-4 sm:px-6 sm:pt-8">
      <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
        <motion.div initial={{ opacity: 0, x: -40 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.8 }} className="rounded-[2rem] bg-hero-gradient p-6 text-white shadow-card sm:rounded-[2.5rem] sm:p-10">
          <p className="mb-4 text-sm uppercase tracking-[0.4em] text-white/80">Discover Kaimur</p>
          <h1 className="text-3xl font-semibold sm:text-4xl lg:text-5xl">Explore hidden hills, waterfalls, temples, and rivers.</h1>
          <p className="mt-5 max-w-xl text-base leading-7 text-white/90 sm:mt-6 sm:text-lg sm:leading-8">Kaimur Explorer helps you plan immersive tours across Bihar's nature sanctuary, heritage forts, pilgrimage sites, and riverfront landscapes.</p>
          <div className="mt-8 flex flex-col gap-3 sm:mt-10 sm:flex-row">
            <Link to="/tours" className="rounded-full bg-white px-6 py-3 text-center text-sm font-semibold text-slate-900 transition hover:bg-slate-100 sm:px-8">
              Browse Tours
            </Link>
            <Link to="/tours" className="rounded-full border border-white/40 px-6 py-3 text-center text-sm text-white transition hover:bg-white/10 sm:px-8">
              Book a Tour
            </Link>
          </div>
        </motion.div>
        <motion.div initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.8 }} className="grid gap-5 sm:grid-cols-2">
          <div className="overflow-hidden rounded-[2rem] bg-white shadow-card">
            <img src="https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1000&q=80" alt="Kaimur hills" className="h-72 w-full object-cover" />
          </div>
          <div className="grid gap-5">
            <div className="overflow-hidden rounded-[2rem] bg-white shadow-card">
              <img src="https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=1000&q=80" alt="Waterfall" className="h-36 w-full object-cover sm:h-40" />
            </div>
            <div className="overflow-hidden rounded-[2rem] bg-white shadow-card">
              <img src="https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=1000&q=80" alt="Temple" className="h-36 w-full object-cover sm:h-40" />
            </div>
          </div>
        </motion.div>
      </div>

      <div className="mt-20">
        <div className="mb-10 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.35em] text-slate-400">Featured Tours</p>
            <h2 className="mt-2 text-3xl font-semibold text-slate-900">Popular Kaimur experiences</h2>
          </div>
          <Link to="/tours" className="text-sm font-semibold text-forest hover:text-green-700">View all tours →</Link>
        </div>
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {tours.map((tour) => (
            <TourCard key={tour.id} tour={tour} />
          ))}
        </div>
      </div>
    </section>
  )
}

export default Home
