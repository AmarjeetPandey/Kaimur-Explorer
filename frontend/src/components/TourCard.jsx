import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'

function TourCard({ tour }) {
  const normalizeMediaUrl = (url) => {
    if (!url) return url
    return url.startsWith('http') ? url : `http://localhost:8000${url}`
  }

  const primaryMedia = tour.front_media_url || tour.image_urls?.[0] || tour.video_urls?.[0] || null
  const isPrimaryVideo = primaryMedia ? /\.(mp4|webm|ogg|mov|avi)$/i.test(primaryMedia) || primaryMedia.includes('/videos/') : false

  return (
    <motion.div whileHover={{ y: -6 }} className="group rounded-3xl bg-white p-5 shadow-card transition duration-300 hover:border-river hover:border-2">
      <div className="relative overflow-hidden rounded-3xl">
        {primaryMedia ? (
          isPrimaryVideo ? (
            <video src={normalizeMediaUrl(primaryMedia)} muted autoPlay loop playsInline className="h-56 w-full object-cover" />
          ) : (
            <img src={normalizeMediaUrl(primaryMedia)} alt={tour.name} className="h-56 w-full object-cover transition duration-500 group-hover:scale-105" />
          )
        ) : (
          <img src="https://via.placeholder.com/600x350" alt={tour.name} className="h-56 w-full object-cover transition duration-500 group-hover:scale-105" />
        )}
      </div>
      <div className="mt-5">
        <p className="text-xs uppercase tracking-[0.3em] text-slate-400">{tour.duration}</p>
        <h3 className="mt-3 text-xl font-semibold text-slate-900">{tour.name}</h3>
        <p className="mt-3 text-slate-600">{tour.short_description}</p>
        <div className="mt-5 flex flex-col gap-3">
          <span className="text-lg font-semibold text-forest">₹{tour.price} / person</span>
          <div className="flex gap-2">
            <Link to={`/tours/${tour.id}`} className="flex-1 rounded-full border-2 border-river px-4 py-2 text-center text-sm font-semibold text-river transition hover:bg-river hover:text-white">
              View Details
            </Link>
            <Link to={`/tours/${tour.id}#booking`} className="flex-1 rounded-full bg-sun px-4 py-2 text-center text-sm font-semibold text-white transition hover:bg-orange-500">
              Book Now
            </Link>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

export default TourCard
