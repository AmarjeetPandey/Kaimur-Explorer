# Kaimur Explorer

Full-stack tourist website for Kaimur district, Bihar, India.

## Structure

- `backend/` - FastAPI backend, SQLite database, JWT auth and Flask-Mail integration.
- `frontend/` - React + Vite + Tailwind CSS frontend with OTP login, tour listing, booking, user dashboard and admin panel.

## Setup

### Backend

1. Create a Python virtual environment and activate it.
2. Install backend dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Create `.env` in `backend/` with values from `.env.example`.
4. Start the API:
   ```bash
   uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
   ```

The backend will create `tour.db` and pre-populate 12 tour packages.

### Frontend

1. Open `frontend/`.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the React app:
   ```bash
   npm run dev
   ```

The frontend will launch on `http://localhost:5173` and talk to the API at `http://localhost:8000`.

## Admin Access

- Email: `admin@kaimurexplorer.com`
- Login using OTP via email.

## Features

- Email-based OTP login for users and admin.
- JWT-protected routes.
- Tour listings, detail pages, booking requests.
- Admin dashboard with tours CRUD, user management, booking approvals, stats.
- Responsive design with Tailwind CSS and animation using Framer Motion.
- Email notifications via Flask-Mail using Mailtrap or any SMTP.

## Notes

- Ensure `MAIL_USERNAME` and `MAIL_PASSWORD` are set in backend `.env`.
- You can update `SITE_URL` for SEO and links.
