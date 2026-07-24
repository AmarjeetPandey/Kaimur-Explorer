import os
import json
import random
import re
from datetime import datetime, timedelta
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Body, Path, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field, validator
from sqlalchemy import text
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import shutil
import os

from .database import Base, engine, SessionLocal, get_db
from .models import User, Tour, Booking, OTPToken
from .email_utils import send_booking_notification, send_status_email, send_otp_email

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@kaimurexplorer.com")
SITE_URL = os.getenv("SITE_URL", "http://localhost:5175")
API_URL = os.getenv("API_URL", "http://localhost:8000")
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretjwtkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7
security = HTTPBearer()

app = FastAPI(title="Kaimur Explorer API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if os.getenv("ALLOW_ORIGINS") is None else os.getenv("ALLOW_ORIGINS").split(","),
    allow_credentials=True,
    allow_methods=["*"]
    ,
    allow_headers=["*"]
)

# Create upload directories
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
IMAGES_DIR = os.path.join(UPLOAD_DIR, "images")
VIDEOS_DIR = os.path.join(UPLOAD_DIR, "videos")
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(VIDEOS_DIR, exist_ok=True)

# Mount static files
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

class SendOTPRequest(BaseModel):
    email: EmailStr

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)

class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: Optional[str]
    is_admin: bool
    is_active: bool

    class Config:
        from_attributes = True


def create_access_token(subject: str, is_admin: bool = False):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "is_admin": is_admin, "exp": expire}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

class TourBase(BaseModel):
    name: str
    short_description: str
    full_description: str
    itinerary: str
    included: str
    price: float
    duration: str
    image_urls: List[str] = []
    video_urls: Optional[List[str]] = []
    front_media_url: Optional[str] = None

class TourOut(TourBase):
    id: int
    class Config:
        from_attributes = True

class BookingCreate(BaseModel):
    tour_id: int
    name: str
    location: str
    age: int = Field(..., gt=0)
    email: EmailStr
    phone: str
    date_of_booking: str

    @validator('phone')
    def phone_must_include_country_code(cls, value):
        cleaned = re.sub(r'[^+0-9]', '', value or '')
        if not re.match(r'^\+\d{1,3}\d{10}$', cleaned):
            raise ValueError('Phone must include country code and 10 digit number, e.g. +919876543210')
        return cleaned

    @validator('date_of_booking')
    def date_cannot_be_in_past(cls, value):
        try:
            booking_date = datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')
        if booking_date < datetime.utcnow().date():
            raise ValueError('Booking date cannot be in the past')
        return value

class BookingOut(BaseModel):
    id: int
    tour_id: int
    user_id: int
    name: str
    location: str
    age: int
    email: EmailStr
    phone: str
    date_of_booking: str
    status: str
    tour: TourOut

    class Config:
        from_attributes = True

def ensure_front_media_column():
    if engine.dialect.name == 'sqlite':
        with engine.connect() as connection:
            result = connection.execute(text("PRAGMA table_info('tours')"))
            columns = [row[1] for row in result]
            if 'front_media_url' not in columns:
                connection.execute(text('ALTER TABLE tours ADD COLUMN front_media_url TEXT'))

@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    ensure_front_media_column()
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if not admin:
            admin = User(
                email=ADMIN_EMAIL,
                name="Kaimur Admin",
                password_hash=generate_password_hash("Admin@123"),
                is_admin=True,
                is_active=True,
            )
            db.add(admin)
            db.commit()
        if db.query(Tour).count() == 0:
            tours = []
            tours_data = [
                {
                    "name": "Maa Mundeshwari Temple",
                    "short_description": "World's oldest functional Hindu temple, dedicated to Shiva and Shakti.",
                    "full_description": "Maa Mundeshwari Temple is one of the oldest surviving temples in India, perched on Mundeshwari hill with panoramic views and spiritual ambiance.",
                    "itinerary": "Visit the temple, receive blessings, enjoy the hilltop sunrise, and explore nearby tribal markets.",
                    "included": "Transport, local guide, temple darshan assistance, entry fee.",
                    "price": 500,
                    "duration": "1 day",
                    "image_urls": [
                        "https://example.com/mundeshwari1.jpg",
                        "https://example.com/mundeshwari2.jpg",
                    ],
                },
                {
                    "name": "Kaimur Wildlife Sanctuary",
                    "short_description": "Lush sanctuary home to tigers, deer, and migratory birds.",
                    "full_description": "Kaimur Wildlife Sanctuary is a biodiversity hotspot featuring dense forests, wildlife safaris and scenic viewpoints in the Kaimur hills.",
                    "itinerary": "Morning safari, birdwatching, nature trail and picnic in the sanctuary zone.",
                    "included": "Transport, safari permit, ranger guide, refreshments.",
                    "price": 800,
                    "duration": "1 day",
                    "image_urls": [
                        "https://example.com/kaimur-wildlife1.jpg",
                        "https://example.com/kaimur-wildlife2.jpg",
                        "https://example.com/kaimur-wildlife3.jpg",
                    ],
                },
                {
                    "name": "Karkat Waterfall",
                    "short_description": "Stunning cascade in the Kaimur hills, perfect for trekking and photos.",
                    "full_description": "Karkat Waterfall offers a dramatic drop, clear pools and scenic trekking paths through green forests.",
                    "itinerary": "Trek to the waterfall, swim in the natural pool, meal by the falls and return in the evening.",
                    "included": "Transport, trekking guide, lunch, entry permit.",
                    "price": 1200,
                    "duration": "1 day",
                    "image_urls": [
                        "https://example.com/karkat1.jpg",
                        "https://example.com/karkat2.jpg",
                        "https://example.com/karkat3.jpg",
                    ],
                },
                {
                    "name": "Telhar Kund Waterfall",
                    "short_description": "Natural pool under a waterfall, a serene and photogenic location.",
                    "full_description": "Telhar Kund captivates visitors with its tranquil pool, cascading water and quiet surrounding forest.",
                    "itinerary": "Visit the waterfall, relax by the pool, take photos and enjoy a packed picnic.",
                    "included": "Transport, local guide, snacks, entry fee.",
                    "price": 700,
                    "duration": "1 day",
                    "image_urls": [
                        "https://example.com/telhar1.jpg",
                        "https://example.com/telhar2.jpg",
                        "https://example.com/telhar3.jpg",
                    ],
                },
                {
                    "name": "Rohtasgarh Fort",
                    "short_description": "Historic fort built by Sher Shah Suri, offering panoramic hill views.",
                    "full_description": "Rohtasgarh Fort stands atop a ridge with ancient architecture, bastions and sweeping valley views.",
                    "itinerary": "Guided fort tour, photography stops, history session and sunset viewpoint.",
                    "included": "Transport, heritage guide, entry fee.",
                    "price": 600,
                    "duration": "1 day",
                    "image_urls": [
                        "https://example.com/rohtas1.jpg",
                        "https://example.com/rohtas2.jpg",
                        "https://example.com/rohtas3.jpg",
                    ],
                },
                {
                    "name": "Durgawati Fort",
                    "short_description": "Ancient hill fort with wide valley views and historic ruins.",
                    "full_description": "Durgawati Fort is a hilltop fortress known for its rugged beauty, ancient structures and peaceful setting.",
                    "itinerary": "Visit fort ruins, discover scenic overlooks, and walk the heritage trail.",
                    "included": "Transport, guide, entry fees.",
                    "price": 550,
                    "duration": "1 day",
                    "image_urls": [
                        "https://example.com/durgawati1.jpg",
                        "https://example.com/durgawati2.jpg",
                        "https://example.com/durgawati3.jpg",
                    ],
                },
                {
                    "name": "Sanjay Jalprapat",
                    "short_description": "Peaceful waterfall set in dense greenery, ideal for relaxation.",
                    "full_description": "Sanjay Jalprapat is a charming waterfall surrounded by forest, offering calm picnic spots and gentle trails.",
                    "itinerary": "Reach the waterfall, enjoy the ambient waters, walk forest trails and return refreshed.",
                    "included": "Transport, guide, snacks.",
                    "price": 650,
                    "duration": "1 day",
                    "image_urls": [
                        "https://example.com/sanjay1.jpg",
                        "https://example.com/sanjay2.jpg",
                        "https://example.com/sanjay3.jpg",
                    ],
                },
                {
                    "name": "Ramgarh Vishdhari Sanctuary",
                    "short_description": "Dense jungle sanctuary favored by wildlife lovers and nature explorers.",
                    "full_description": "Ramgarh Vishdhari Sanctuary offers pristine forest, wildlife sightings and nature walks in the Kaimur region.",
                    "itinerary": "Safari-style walk, wildlife spotting, photography, and forest picnic.",
                    "included": "Transport, wildlife guide, entry permit.",
                    "price": 900,
                    "duration": "1 day",
                    "image_urls": [
                        "https://example.com/ramgarh1.jpg",
                        "https://example.com/ramgarh2.jpg",
                        "https://example.com/ramgarh3.jpg",
                    ],
                },
                {
                    "name": "Sidhanath Temple",
                    "short_description": "Historic Shiva temple located in the village of Bararura.",
                    "full_description": "Sidhanath Temple is a sacred shrine in the heart of Bararura village, attracting pilgrims with its spiritual atmosphere.",
                    "itinerary": "Temple visit, local market walk, vegetarian prasad and cultural exploration.",
                    "included": "Transport, guide, temple donation management.",
                    "price": 400,
                    "duration": "1 day",
                    "image_urls": [
                        "https://example.com/sidhanath1.jpg",
                        "https://example.com/sidhanath2.jpg",
                        "https://example.com/sidhanath3.jpg",
                    ],
                },
                {
                    "name": "Baidyanath Temple",
                    "short_description": "Sacred Shiva temple popular with pilgrims across Bihar.",
                    "full_description": "Baidyanath Temple is one of the most revered Shiva temples in the region, offering a tranquil pilgrimage experience.",
                    "itinerary": "Visit the temple, explore surrounding ghats, and learn about local traditions.",
                    "included": "Transport, darshan assistance, guide.",
                    "price": 450,
                    "duration": "1 day",
                    "image_urls": [
                        "https://example.com/baidyanath1.jpg",
                        "https://example.com/baidyanath2.jpg",
                        "https://example.com/baidyanath3.jpg",
                    ],
                },
                {
                    "name": "Karmanasa River",
                    "short_description": "Serene river landscape for boating, picnics and sunsets.",
                    "full_description": "The Karmanasa River is famous for scenic banks, boating, and quiet picnic spots surrounded by riverine beauty.",
                    "itinerary": "Boat ride, riverside picnic, and sunset viewing by the water.",
                    "included": "Transport, boat ride, picnic setup, guide.",
                    "price": 300,
                    "duration": "1 day",
                    "image_urls": [
                        "https://example.com/karmanasa1.jpg",
                        "https://example.com/karmanasa2.jpg",
                        "https://example.com/karmanasa3.jpg",
                    ],
                },
                {
                    "name": "Chorghatia",
                    "short_description": "Natural rock formations and sweeping views in the hills.",
                    "full_description": "Chorghatia is known for its dramatic rock formations, scenic overlooks and quiet trails in the Kaimur hills.",
                    "itinerary": "Hike to the rock site, photograph panoramic views, and enjoy a nature walk.",
                    "included": "Transport, trekking guide, snacks.",
                    "price": 350,
                    "duration": "1 day",
                    "image_urls": [
                        "https://example.com/chorghatia1.jpg",
                        "https://example.com/chorghatia2.jpg",
                        "https://example.com/chorghatia3.jpg",
                    ],
                },
            ]
            for tour in tours_data:
                db.add(
                    Tour(
                        name=tour["name"],
                        short_description=tour["short_description"],
                        full_description=tour["full_description"],
                        itinerary=tour["itinerary"],
                        included=tour["included"],
                        price=tour["price"],
                        duration=tour["duration"],
                        image_urls=json.dumps(tour["image_urls"]),
                        media_items=json.dumps([{"type": "image", "url": url} for url in tour["image_urls"]]),
                    )
                )
            db.commit()
    finally:
        db.close()


@app.post("/api/auth/send-otp")
def send_otp(payload: SendOTPRequest, db: Session = Depends(get_db)):
    otp_code = f"{random.randint(100000, 999999)}"
    expiry = datetime.utcnow() + timedelta(minutes=5)
    otp_hash = generate_password_hash(otp_code)
    token = OTPToken(email=payload.email, otp_hash=otp_hash, expires_at=expiry)
    db.add(token)
    db.commit()
    try:
        send_otp_email(payload.email, otp_code)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to send OTP email")
    return {"message": "OTP sent to your email address. Please check your inbox."}


@app.post("/api/auth/verify-otp")
def verify_otp(payload: VerifyOTPRequest, db: Session = Depends(get_db)):
    token = (
        db.query(OTPToken)
        .filter(OTPToken.email == payload.email, OTPToken.used == False)
        .order_by(OTPToken.created_at.desc())
        .first()
    )
    if not token or token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP expired or invalid")
    if not check_password_hash(token.otp_hash, payload.otp):
        raise HTTPException(status_code=400, detail="OTP invalid")
    token.used = True
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        user = User(email=payload.email, name=payload.email.split("@")[0].title(), is_active=True, is_admin=(payload.email.lower() == ADMIN_EMAIL))
        db.add(user)
        db.commit()
        db.refresh(user)
    access_token = create_access_token(payload.email, user.is_admin)
    return {"access_token": access_token, "user": {"email": user.email, "name": user.name, "is_admin": user.is_admin}}


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    payload = decode_access_token(token)
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not active")
    return user


def get_admin_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@app.get("/api/auth/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user



@app.get("/api/tours", response_model=List[TourOut])
def get_tours(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    tours = db.query(Tour).offset(skip).limit(limit).all()
    for tour in tours:
        image_urls = [url for url in json.loads(tour.image_urls) if url]
        video_urls = [url for url in json.loads(tour.video_urls) if url] if tour.video_urls else []
        tour.image_urls = image_urls
        tour.video_urls = video_urls
    return tours


@app.get("/api/tours/{tour_id}", response_model=TourOut)
def get_tour(tour_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    tour = db.query(Tour).filter(Tour.id == tour_id).first()
    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found")
    image_urls = [url for url in json.loads(tour.image_urls) if url]
    video_urls = [url for url in json.loads(tour.video_urls) if url] if tour.video_urls else []
    tour.image_urls = image_urls
    tour.video_urls = video_urls
    return tour


@app.post("/api/bookings")
def create_booking(payload: BookingCreate, db: Session = Depends(get_db)):
    try:
        tour = db.query(Tour).filter(Tour.id == payload.tour_id).first()
        if not tour:
            raise HTTPException(status_code=404, detail="Tour not found")

        user = db.query(User).filter(User.email == payload.email).first()
        if not user:
            user = User(
                email=payload.email,
                name=payload.name,
                is_active=True,
                is_admin=(payload.email.lower() == ADMIN_EMAIL),
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        booking = Booking(
            user_id=user.id,
            tour_id=payload.tour_id,
            name=payload.name,
            location=payload.location,
            age=payload.age,
            email=payload.email,
            phone=payload.phone,
            date_of_booking=payload.date_of_booking,
            status="Approved",
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)
        
        booking_sent = send_booking_notification(
            ADMIN_EMAIL,
            {
                "booking_id": booking.id,
                "tour_name": tour.name,
                "name": booking.name,
                "location": booking.location,
                "age": booking.age,
                "email": booking.email,
                "phone": booking.phone,
                "date_of_booking": booking.date_of_booking,
                "status": booking.status,
            },
        )
        if not booking_sent:
            print("[Booking Notification] Email delivery failed. Booking was saved successfully.")

        try:
            sent = send_status_email(
                booking.email,
                {
                    "tour_name": tour.name,
                    "name": booking.name,
                    "status": "Confirmed",
                    "details": f"Booking date: {booking.date_of_booking}, tour: {tour.name}",
                },
            )
            if not sent:
                print(f"[Booking Confirmation] Failed to send confirmation email to {booking.email}")
        except Exception as exc:
            print(f"[Booking Confirmation] Error sending confirmation email: {exc}")

        # Return booking as dict with parsed tour data
        return {
            "id": booking.id,
            "tour_id": booking.tour_id,
            "user_id": booking.user_id,
            "name": booking.name,
            "location": booking.location,
            "age": booking.age,
            "email": booking.email,
            "phone": booking.phone,
            "date_of_booking": booking.date_of_booking,
            "status": booking.status,
            "tour": {
                "id": tour.id,
                "name": tour.name,
                "short_description": tour.short_description,
                "full_description": tour.full_description,
                "itinerary": tour.itinerary,
                "included": tour.included,
                "price": tour.price,
                "duration": tour.duration,
                "image_urls": [url for url in json.loads(tour.image_urls) if url],
                "video_urls": [url for url in json.loads(tour.video_urls) if url] if tour.video_urls else [],
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in create_booking: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/bookings", response_model=List[BookingOut])
def list_bookings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bookings = db.query(Booking).filter(Booking.user_id == current_user.id).all()
    for booking in bookings:
        image_urls = [url for url in json.loads(booking.tour.image_urls) if url]
        video_urls = [url for url in json.loads(booking.tour.video_urls) if url] if booking.tour.video_urls else []
        booking.tour.image_urls = image_urls
        booking.tour.video_urls = video_urls
    return bookings


@app.get("/api/admin/bookings", response_model=List[BookingOut])
def admin_list_bookings(admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    bookings = db.query(Booking).order_by(Booking.created_at.desc()).all()
    for booking in bookings:
        image_urls = [url for url in json.loads(booking.tour.image_urls) if url]
        video_urls = [url for url in json.loads(booking.tour.video_urls) if url] if booking.tour.video_urls else []
        booking.tour.image_urls = image_urls
        booking.tour.video_urls = video_urls
        booking.tour.media = build_media_list(image_urls, video_urls, json.loads(booking.tour.media_items) if booking.tour.media_items else None)
    return bookings


@app.put("/api/admin/bookings/{booking_id}")
def admin_update_booking(booking_id: int, status: str = Body(...), admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    booking.status = status
    db.commit()
    tour = db.query(Tour).filter(Tour.id == booking.tour_id).first()
    try:
        if status.lower() == "approved":
            sent = send_status_email(
                booking.email,
                {
                    "tour_name": tour.name,
                    "name": booking.name,
                    "status": "Confirmed",
                    "details": f"Booking date: {booking.date_of_booking}, tour: {tour.name}",
                },
            )
            if not sent:
                print(f"[Booking Status] Failed to send confirmation email to {booking.email}")
        elif status.lower() == "rejected" or status.lower() == "cancelled":
            sent = send_status_email(
                booking.email,
                {
                    "tour_name": tour.name,
                    "name": booking.name,
                    "status": "Rejected",
                    "details": f"Booking date: {booking.date_of_booking}, tour: {tour.name}",
                },
            )
            if not sent:
                print(f"[Booking Status] Failed to send rejection email to {booking.email}")
    except Exception as exc:
        print(f"[Booking Status] Error sending status email: {exc}")
    return {"message": "Booking status updated"}


@app.get("/api/admin/users", response_model=List[UserOut])
def admin_list_users(admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    users = db.query(User).filter(User.email != ADMIN_EMAIL).all()
    return users


@app.delete("/api/admin/users/{user_id}")
def admin_delete_user(user_id: int, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Delete all bookings associated with this user first
    db.query(Booking).filter(Booking.user_id == user_id).delete()

    db.delete(user)
    db.commit()
    return {"message": "User deleted"}


@app.post("/api/admin/tours", response_model=TourOut)
def admin_create_tour(payload: TourBase, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    image_urls = [url for url in payload.image_urls if url]
    video_urls = [url for url in payload.video_urls if url] if payload.video_urls else []
    front_media_url = payload.front_media_url if payload.front_media_url in image_urls + video_urls else None
    if not front_media_url:
        front_media_url = image_urls[0] if image_urls else (video_urls[0] if video_urls else None)
    tour = Tour(
        name=payload.name,
        short_description=payload.short_description,
        full_description=payload.full_description,
        itinerary=payload.itinerary,
        included=payload.included,
        price=payload.price,
        duration=payload.duration,
        image_urls=json.dumps(image_urls),
        video_urls=json.dumps(video_urls) if video_urls else None,
        front_media_url=front_media_url,
    )
    db.add(tour)
    db.commit()
    db.refresh(tour)
    tour.image_urls = image_urls
    tour.video_urls = video_urls
    tour.front_media_url = front_media_url
    return tour


@app.put("/api/admin/tours/{tour_id}", response_model=TourOut)
def admin_update_tour(tour_id: int, payload: TourBase, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    tour = db.query(Tour).filter(Tour.id == tour_id).first()
    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found")
    image_urls = [url for url in payload.image_urls if url]
    video_urls = [url for url in payload.video_urls if url] if payload.video_urls else []
    front_media_url = payload.front_media_url if payload.front_media_url in image_urls + video_urls else None
    if not front_media_url:
        front_media_url = image_urls[0] if image_urls else (video_urls[0] if video_urls else None)
    tour.name = payload.name
    tour.short_description = payload.short_description
    tour.full_description = payload.full_description
    tour.itinerary = payload.itinerary
    tour.included = payload.included
    tour.price = payload.price
    tour.duration = payload.duration
    tour.image_urls = json.dumps(image_urls)
    tour.video_urls = json.dumps(video_urls) if video_urls else None
    tour.front_media_url = front_media_url
    db.commit()
    tour.image_urls = image_urls
    tour.video_urls = video_urls
    tour.front_media_url = front_media_url
    return tour


@app.delete("/api/admin/tours/{tour_id}")
def admin_delete_tour(tour_id: int, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    tour = db.query(Tour).filter(Tour.id == tour_id).first()
    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found")

    # Delete all bookings associated with this tour first
    db.query(Booking).filter(Booking.tour_id == tour_id).delete()

    db.delete(tour)
    db.commit()
    return {"message": "Tour deleted"}


@app.get("/api/admin/stats")
def admin_stats(admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    total_tours = db.query(Tour).count()
    total_bookings = db.query(Booking).count()
    pending_bookings = db.query(Booking).filter(Booking.status == "Pending").count()
    approved_bookings = db.query(Booking).filter(Booking.status == "Approved").count()
    return {
        "total_users": total_users,
        "total_tours": total_tours,
        "total_bookings": total_bookings,
        "pending_bookings": pending_bookings,
        "approved_bookings": approved_bookings,
    }


@app.post("/api/admin/upload-image")
def upload_image(file: UploadFile = File(...), admin_user: User = Depends(get_admin_user)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Generate unique filename
    import uuid
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(IMAGES_DIR, unique_filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Return URL
    return {"url": f"/uploads/images/{unique_filename}"}


@app.post("/api/admin/upload-video")
def upload_video(file: UploadFile = File(...), admin_user: User = Depends(get_admin_user)):
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    # Generate unique filename
    import uuid
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(VIDEOS_DIR, unique_filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Return URL
    return {"url": f"/uploads/videos/{unique_filename}"}
