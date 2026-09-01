import os
import json
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

from database import Base, engine, SessionLocal, get_db
from models import User, Tour, Booking

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@kaimurexplorer.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
if not ADMIN_PASSWORD:
    raise RuntimeError("ADMIN_PASSWORD must be set in backend/.env")
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

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)

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
    tour: Optional[TourOut] = None
    tour_name: Optional[str] = None
    tour_duration: Optional[str] = None
    tour_price: Optional[float] = None
    tour_short_description: Optional[str] = None

    class Config:
        from_attributes = True

def ensure_front_media_column():
    if engine.dialect.name == 'sqlite':
        with engine.connect() as connection:
            result = connection.execute(text("PRAGMA table_info('tours')"))
            columns = [row[1] for row in result]
            if 'front_media_url' not in columns:
                connection.execute(text('ALTER TABLE tours ADD COLUMN front_media_url TEXT'))


def parse_media_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(url).strip() for url in value if str(url).strip()]
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return []
        try:
            parsed = json.loads(cleaned)
        except (TypeError, ValueError):
            return [cleaned] if cleaned else []
        if isinstance(parsed, list):
            return [str(url).strip() for url in parsed if str(url).strip()]
        if isinstance(parsed, str):
            return [parsed.strip()] if parsed.strip() else []
    return []


def reset_tour_sequence(db: Session):
    try:
        if engine.dialect.name == 'postgresql':
            max_id = db.execute(text("SELECT COALESCE(MAX(id), 0) FROM tours")).scalar() or 0
            db.execute(text(f"ALTER SEQUENCE tours_id_seq RESTART WITH {max_id + 1}"))
        elif engine.dialect.name == 'sqlite':
            db.execute(text("DELETE FROM sqlite_sequence WHERE name = 'tours'"))
    except Exception:
        pass


def cleanup_demo_tours(db: Session):
    legacy_demo_names = {
        "Maa Mundeshwari Temple",
        "Kaimur Wildlife Sanctuary",
        "Karkat Waterfall",
        "Telhar Kund Waterfall",
        "Rohtasgarh Fort",
        "Durgawati Fort",
        "Sanjay Jalprapat",
        "Ramgarh Vishdhari Sanctuary",
        "Sidhanath Temple",
        "Baidyanath Temple",
        "Karmanasa River",
        "Chorghatia",
    }
    demo_tours = db.query(Tour).filter(Tour.name.in_(sorted(legacy_demo_names))).all()
    if demo_tours:
        for tour in demo_tours:
            db.delete(tour)
        db.commit()
        reset_tour_sequence(db)


def drop_otp_tokens_table(db: Session):
    try:
        db.execute(text("DROP TABLE IF EXISTS otp_tokens"))
        db.commit()
    except Exception:
        pass


@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    ensure_front_media_column()
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == ADMIN_EMAIL.lower()).first()
        if not admin:
            admin = User(
                email=ADMIN_EMAIL.lower(),
                name="Kaimur Admin",
                password_hash=generate_password_hash(ADMIN_PASSWORD),
                is_admin=True,
                is_active=True,
            )
            db.add(admin)
            db.commit()
        else:
            admin.email = ADMIN_EMAIL.lower()
            admin.password_hash = generate_password_hash(ADMIN_PASSWORD)
            admin.is_admin = True
            admin.is_active = True
            db.commit()

        cleanup_demo_tours(db)
        drop_otp_tokens_table(db)
    finally:
        db.close()


@app.post("/api/auth/signup")
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    normalized_email = payload.email.lower()
    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists. Please log in instead.")

    user = User(
        email=normalized_email,
        name=payload.name or normalized_email.split("@")[0].title(),
        password_hash=generate_password_hash(payload.password),
        is_active=True,
        is_admin=(normalized_email == ADMIN_EMAIL.lower()),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(normalized_email, user.is_admin)
    return {"access_token": access_token, "user": {"email": user.email, "name": user.name, "is_admin": user.is_admin}}


@app.post("/api/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    normalized_email = payload.email.lower()
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user or not user.password_hash or not check_password_hash(user.password_hash, payload.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(normalized_email, user.is_admin)
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


def build_media_list(image_urls, video_urls, media_items=None):
    items = []
    if media_items:
        try:
            items = json.loads(media_items)
        except (TypeError, ValueError):
            items = []
    if isinstance(items, list) and items:
        normalized = []
        for item in items:
            if isinstance(item, dict):
                url = item.get('url')
                media_type = item.get('type', 'image')
                if url:
                    normalized.append({"type": media_type, "url": url})
        if normalized:
            return normalized
    result = []
    for url in image_urls:
        result.append({"type": "image", "url": url})
    for url in video_urls:
        result.append({"type": "video", "url": url})
    return result


@app.get("/api/auth/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user



@app.get("/api/tours", response_model=List[TourOut])
def get_tours(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    tours = db.query(Tour).order_by(Tour.id.asc()).offset(skip).limit(limit).all()
    for tour in tours:
        image_urls = parse_media_list(tour.image_urls)
        video_urls = parse_media_list(tour.video_urls)
        front_media_url = tour.front_media_url if tour.front_media_url in (image_urls + video_urls) else (image_urls[0] if image_urls else (video_urls[0] if video_urls else None))
        tour.image_urls = image_urls
        tour.video_urls = video_urls
        tour.front_media_url = front_media_url
    return tours


@app.get("/api/tours/{tour_id}", response_model=TourOut)
def get_tour(tour_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    tour = db.query(Tour).filter(Tour.id == tour_id).first()
    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found")
    image_urls = parse_media_list(tour.image_urls)
    video_urls = parse_media_list(tour.video_urls)
    front_media_url = tour.front_media_url if tour.front_media_url in (image_urls + video_urls) else (image_urls[0] if image_urls else (video_urls[0] if video_urls else None))
    tour.image_urls = image_urls
    tour.video_urls = video_urls
    tour.front_media_url = front_media_url
    return tour


@app.post("/api/bookings")
def create_booking(payload: BookingCreate, db: Session = Depends(get_db)):
    try:
        tour = db.query(Tour).filter(Tour.id == payload.tour_id).first()
        if not tour:
            raise HTTPException(status_code=404, detail="Tour not found")

        normalized_email = payload.email.lower()
        user = db.query(User).filter(User.email == normalized_email).first()
        if not user:
            user = User(
                email=normalized_email,
                name=payload.name,
                is_active=True,
                is_admin=(normalized_email == ADMIN_EMAIL.lower()),
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
            email=normalized_email,
            phone=payload.phone,
            date_of_booking=payload.date_of_booking,
            status="Pending",
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)

        # Booking details are stored in the admin dashboard and visible to the super admin immediately.
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
        if not booking.tour:
            continue
        image_urls = parse_media_list(booking.tour.image_urls)
        video_urls = parse_media_list(booking.tour.video_urls)
        booking.tour.image_urls = image_urls
        booking.tour.video_urls = video_urls
    return bookings


@app.get("/api/admin/bookings", response_model=List[BookingOut])
def admin_list_bookings(admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    bookings = db.query(Booking).order_by(Booking.created_at.desc()).all()
    result = []
    for booking in bookings:
        tour = db.query(Tour).filter(Tour.id == booking.tour_id).first()
        if not tour:
            continue
        booking.tour = tour
        image_urls = parse_media_list(tour.image_urls)
        video_urls = parse_media_list(tour.video_urls)
        tour.image_urls = image_urls
        tour.video_urls = video_urls
        tour.front_media_url = tour.front_media_url if tour.front_media_url in (image_urls + video_urls) else (image_urls[0] if image_urls else (video_urls[0] if video_urls else None))
        if hasattr(tour, 'media'):
            tour.media = build_media_list(image_urls, video_urls, tour.media_items)
        result.append(booking)
    return result


@app.put("/api/admin/bookings/{booking_id}")
def admin_update_booking(booking_id: int, status: str = Body(...), admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    booking.status = status
    db.commit()
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
        media_items=json.dumps([
            {"type": "image", "url": url} for url in image_urls
        ] + [
            {"type": "video", "url": url} for url in video_urls
        ]),
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
    tour.media_items = json.dumps([
        {"type": "image", "url": url} for url in image_urls
    ] + [
        {"type": "video", "url": url} for url in video_urls
    ])
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

    db.query(Booking).filter(Booking.tour_id == tour_id).delete()
    db.delete(tour)
    db.commit()

    try:
        if engine.dialect.name == 'postgresql':
            max_id = db.execute(text("SELECT COALESCE(MAX(id), 0) FROM tours")).scalar() or 0
            db.execute(text(f"ALTER SEQUENCE tours_id_seq RESTART WITH {max_id + 1}"))
            db.commit()
        elif engine.dialect.name == 'sqlite':
            db.execute(text("DELETE FROM sqlite_sequence WHERE name = 'tours'"))
            db.commit()
    except Exception:
        pass

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
