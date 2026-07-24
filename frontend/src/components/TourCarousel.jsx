import { Swiper, SwiperSlide } from 'swiper/react'
import 'swiper/css'
import 'swiper/css/navigation'
import 'swiper/css/pagination'
import { Navigation, Pagination, Autoplay } from 'swiper/modules'

function TourCarousel({ images }) {
  return (
    <Swiper modules={[Navigation, Pagination, Autoplay]} navigation pagination={{ clickable: true }} autoplay={{ delay: 4000 }} loop className="h-[380px] rounded-[32px] bg-slate-200">
      {images.map((src, index) => (
        <SwiperSlide key={index}>
          <img src={src} alt={`Tour image ${index + 1}`} className="h-[380px] w-full object-cover" />
        </SwiperSlide>
      ))}
    </Swiper>
  )
}

export default TourCarousel
