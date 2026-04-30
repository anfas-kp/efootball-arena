# ⚽ eFootball Arena — Tournament Management Platform

A comprehensive Django web application for organizing and managing e-football tournaments (EA FC / eFootball). Teams can register, compete in structured leagues, submit match results with screenshot proof, and track transparent tournament standings.

---

## 🎯 Features

### For Team Captains
- **Team Registration** — Register your team with logo, platform, and game preference
- **Roster Management** — Add up to 20 players with gaming IDs, positions, and jersey numbers (locked during active tournaments)
- **Open Enrollment** — Browse open tournaments and self-apply with a verified team
- **Match Result Submission** — Submit scores with mandatory screenshot proof
- **Match Details** — Log goals, assists, disciplinary cards (with SS proof), and top 3 rated players per team
- **Live Standings & Leaderboards** — View auto-calculated league tables, top scorers, assists, ratings, and disciplinary records in real time

### For Administrators
- **Admin Dashboard** — Centralized overview of tournaments, pending teams, applications, and results
- **Team Verification** — Approve or reject team registrations with reasons
- **Tournament Creation** — Create tournaments with custom rules, prize pools, entry fees, and point systems
- **Open-for-all Toggle** — Enable `is_open` flag to allow teams to self-apply
- **Application Management** — Accept or reject tournament applications and instantly assign accepted teams to specific leagues
- **Multi-League Support** — Add multiple leagues under a single tournament (each with specific formats: Round Robin, 2-Leg, Knockout, etc.)
- **Fixture Generation** — Auto-generate round-robin fixtures with a single click
- **Result Verification** — Review and approve submitted match results with screenshots (auto-updates player aggregates)

### Platform Highlights
- 🎮 **Proof-Based System** — Mandatory screenshots eliminate result disputes
- 📊 **Auto-Calculated Standings** — Points, goal difference, and rankings update instantly
- 🏆 **Round-Robin Scheduling** — Smart fixture generation algorithm with no conflicts
- 🔐 **Role-Based Access** — Separate admin and captain permissions
- 🌙 **Premium Dark UI** — Gaming-themed design with glassmorphism and neon accents

---

## 🛠️ Tech Stack

| Layer       | Technology                          |
|-------------|-------------------------------------|
| Backend     | Django 5.x, Python 3.11+            |
| Database    | SQLite (dev) / PostgreSQL (prod)     |
| Frontend    | Django Templates, Bootstrap 5       |
| Styling     | Custom CSS (dark gaming theme)       |
| Fonts       | Orbitron, Inter (Google Fonts)        |
| Icons       | Font Awesome 6                       |
| Image Handling | Pillow                            |

---

## 📁 Project Structure

```
efootball/
├── manage.py                  # Django CLI entry point
├── requirements.txt           # Python dependencies
├── .gitignore
│
├── efootball_project/         # Project configuration
│   ├── settings.py            # Django settings
│   ├── urls.py                # Root URL routing
│   └── wsgi.py                # WSGI entry point
│
├── accounts/                  # Authentication & user management
│   ├── models.py              # Custom User model (admin/captain roles)
│   ├── forms.py               # Register & login forms
│   ├── views.py               # Auth views
│   └── urls.py
│
├── teams/                     # Team & player management
│   ├── models.py              # Team, Player models
│   ├── forms.py               # Team registration & player forms
│   ├── views.py               # CRUD + admin verification
│   └── urls.py
│
├── tournaments/               # Tournament, league & fixture management
│   ├── models.py              # Tournament, League, Fixture models
│   ├── forms.py               # Tournament & league forms
│   ├── views.py               # CRUD + fixture generation + standings
│   └── urls.py
│
├── matches/                   # Match results & verification
│   ├── models.py              # MatchResult, Goal, Card models
│   ├── forms.py               # Result & goal submission forms
│   ├── views.py               # Submission + admin approval
│   └── urls.py
│
├── core/                      # Landing page & shared utilities
│   ├── views.py
│   └── urls.py
│
├── templates/                 # All HTML templates
│   ├── base.html              # Base layout (navbar, footer, messages)
│   ├── core/                  # Home page
│   ├── accounts/              # Login, register, profile
│   ├── teams/                 # Team CRUD, admin verification
│   ├── tournaments/           # Tournament CRUD, standings, fixtures
│   └── matches/               # Result submission, verification
│
└── static/
    └── css/
        └── style.css          # Premium dark theme stylesheet
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)

### Installation

```bash
# 1. Clone or navigate to the project
cd d:\efootball

# 2. Create a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run database migrations
python manage.py makemigrations accounts teams tournaments matches
python manage.py migrate

# 5. Create a superuser (admin account)
python manage.py createsuperuser

# 6. Start the development server
python manage.py runserver
```

### Access the App

| URL                              | Description              |
|----------------------------------|--------------------------|
| http://127.0.0.1:8000/           | Home page                |
| http://127.0.0.1:8000/admin/     | Django admin panel       |
| http://127.0.0.1:8000/accounts/register/ | User registration |
| http://127.0.0.1:8000/accounts/login/    | User login        |
| http://127.0.0.1:8000/tournaments/admin/dashboard/ | Admin dashboard |

---

## 🌐 Deployment (Production)

The platform is configured to be easily hosted on platforms like **Render**, **Railway**, or **Heroku**. It uses `django-environ` for environment variables, `Whitenoise` for serving static files efficiently, and `Cloudinary` to permanently store media (since free-tier hosting wipes local files).

### 1. Set Environment Variables
In your hosting dashboard, set the following environment variables:
- `DEBUG=False`
- `SECRET_KEY=your_secure_random_key`
- `ALLOWED_HOSTS=your-app-url.onrender.com,yourdomain.com`
- `DATABASE_URL=postgres://user:pass@host/dbname` *(e.g., from Neon.tech or Render's PostgreSQL)*
- `CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME` *(Get this from your free Cloudinary account to store team logos and match screenshots)*

### 2. Build Command (Render)
If using Render, set the build command to use the included script:
```bash
bash build.sh
```
*This script automatically installs dependencies, collects static files, and runs the database migrations.*

### 3. Start Command (Render)
```bash
gunicorn efootball_project.wsgi:application
```

---

## 📖 Usage Guide

### 1. Initial Setup (Admin)
1. Log in with your superuser account
2. Go to Django admin (`/admin/`) and ensure your user's **role** is set to `admin`
3. Navigate to the **Admin Dashboard** (`/tournaments/admin/dashboard/`)

### 2. Create a Tournament
1. Click **New Tournament** from the admin dashboard
2. Fill in tournament details (name, dates, format, prize pool, point system)
3. Set status to `Registration Open` when ready

### 3. Register a Team (Captain)
1. Create a new account via `/accounts/register/`
2. Go to **My Team** → **Register Team**
3. Upload team logo, fill in details, and submit
4. Wait for admin approval

### 4. Verify Teams (Admin)
1. Go to **Verify Teams** from the dashboard
2. Review pending teams and click **Approve** or **Reject**

### 5. Browse & Apply to Tournaments (Captain)
1. Navigate to **Tournaments** → **Browse Open**
2. View available tournaments and click **Apply Now** (must be an approved team)
3. Wait for admin application review. Roster changes are locked once accepted!

### 6. Manage Applications & Leagues (Admin)
1. Go to Tournament Details → **Applications**
2. Review applications, select a league for the team, and click **Accept**
3. The team is instantly added to the selected league's roster
4. Click **Generate Fixtures** in the league details to auto-create round-robin matchups

### 7. Submit Match Results (Captain)
1. Go to **Fixtures** → find your match → **Submit Result**
2. Enter the score and upload a screenshot of the final scoreline
3. Add match details (goals, assists, cards with proof, and top rated players)

### 8. Verify Results (Admin)
1. Go to **Verify Results** from the dashboard
2. Review the score, screenshot, and match details
3. Click **Approve** to finalize — standings and player aggregates update automatically

---

## 🗄️ Data Models

```
Tournament ──┐
             ├── League ──┐
             │             ├── Team ── Player
             │             │
             │             └── Fixture ── MatchResult ──┬── Goal
             │                                          └── Card
             └── (multiple leagues per tournament)
```

| Model        | Key Fields                                         |
|--------------|-----------------------------------------------------|
| User         | username, email, role (admin/captain), phone         |
| Team         | name, logo, captain, platform, game, status, is_roster_locked |
| Player       | name, gaming_id, position, jersey_number, aggregates |
| Tournament   | name, dates, status, is_open, registration_deadline  |
| League       | name, format, max_teams, teams (M2M)                 |
| TournamentApp| tournament, team, status, assigned_league            |
| Fixture      | league, home_team, away_team, matchday, status       |
| MatchResult  | fixture, scores, screenshot, status, submitted_by    |
| Goal         | result, scorer, assist, minute, goal_type            |
| Card         | result, player, card_type, minute, screenshot        |
| PlayerRating | result, player, rating, screenshot                   |

---

## 🎨 UI Theme

The platform uses a **dark gaming aesthetic** designed to feel premium and immersive:

- **Color Palette**: Dark backgrounds (`#0a0e1a`) with neon green (`#06d6a0`) and blue (`#118ab2`) accents
- **Typography**: Orbitron (headings) + Inter (body) from Google Fonts
- **Effects**: Glassmorphism cards, glow shadows, smooth hover animations
- **Responsive**: Fully mobile-friendly with Bootstrap 5 grid

---

## 🔮 Future Enhancements

- [ ] Email notifications (SendGrid / Mailgun)
- [ ] Opponent cross-verification of results
- [ ] Public spectator view with shareable links
- [ ] CSV/PDF export for standings and fixtures
- [ ] Mobile app (React Native)
- [ ] Discord bot integration

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).

---

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request.

---

<p align="center">
  Built with ❤️ for the competitive e-football community<br>
  <strong>eFootball Arena</strong> &copy; 2026
</p>
