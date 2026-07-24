🏍️ Bike Price Analysis System
A full-stack Django web application for exploring, searching, and analyzing a real-world dataset of bike listings. It combines an authenticated dashboard, dynamic search/filtering, interactive analytics (built with hand-rolled SVG/JS charts — no external chart library needed), a side-by-side comparison tool, and a full admin CRUD panel that keeps the database and the source CSV in sync.
![Python](https://img.shields.io/badge/Python-3.12-blue)
![Django](https://img.shields.io/badge/Django-6.0-092E20?logo=django&logoColor=white)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)
---
✨ Features
🔐 Authentication with email verification — sign-up flow requiring a 6-digit code sent to the user's email before the account is activated, plus standard login/logout.
📊 Dashboard / Home — key stats at a glance: total records, average/min/max price, number of distinct brands and years, and featured (highest-priced) bikes.
🔍 Advanced Search & Filters — filter listings by name/brand keyword, brand, year, fuel type, and price range, with live result counts.
📈 Analytics Page — price distribution histogram, fuel-type breakdown (petrol vs. electric), brand-wise average price, price trend by year, and an engine-capacity-vs-price scatter plot — all rendered with lightweight custom SVG charts.
⚖️ Compare Tool — select multiple bikes and compare their specs and prices side by side.
🛠️ Admin Records Panel — a staff-only dashboard to search, add, edit, and delete bike records.
📥 CSV Import — bulk-upload a CSV of bike listings directly into the database (staff-only).
🔄 DB ↔ CSV Sync — every create/update/delete through the admin panel automatically rewrites `data/bikes.csv` so the flat file always mirrors the database.
---
🖼️ Screenshots
> Place the images from the `screenshots/` folder (included with this README) into your repository, then these will render automatically on GitHub.
Login
![Login Page](screenshots/login.png)
Dashboard
![Dashboard](screenshots/dashboard.png)
Search & Filters
![Search Page](screenshots/search.png)
Analytics
![Analytics Page](screenshots/analytics.png)
Compare Bikes
![Compare Page](screenshots/compare.png)
Admin Records Panel
![Admin Records](screenshots/admin_records.png)
Sign Up
![Sign Up Page](screenshots/signup.png)
---
🧰 Tech Stack
Layer	Technology
Backend	Python, Django 6
Database	SQLite (`db.sqlite3`)
Frontend	Django Templates, HTML, CSS, vanilla JS
Charts	Custom SVG + JS (no external charting library)
Auth	Django's built-in auth + custom email OTP flow
Data	CSV import/export kept in sync with the DB
---
📁 Project Structure
```
bike_analysis_with_auth2/
├── bike_analysis/          # Project settings, URLs, WSGI/ASGI
│   ├── settings.py
│   └── urls.py
├── bikes/                  # Main app
│   ├── models.py           # Bike, EmailVerification
│   ├── views.py            # All views: auth, search, analytics, admin CRUD
│   ├── admin.py
│   └── migrations/
├── data/
│   └── bikes.csv           # Source dataset, kept in sync with the DB
├── static/
│   └── css/style.css
├── templates/
│   └── bikes/               # home, search, analytics, compare, admin, auth pages
├── screenshots/             # README screenshots
├── db.sqlite3
└── manage.py
```
---
⚙️ Getting Started
Prerequisites
Python 3.10+
pip
1. Clone the repository
```bash
git clone https://github.com/ianasaslam2209/Bike-Price-Analysis-System.git
cd Bike-Price-Analysis-System
```
2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate       # On Windows: venv\Scripts\activate
```
3. Install dependencies
```bash
pip install django
```
(Add a `requirements.txt` with `pip freeze > requirements.txt` if you'd like others to install with `pip install -r requirements.txt`.)
4. Apply migrations
```bash
python manage.py migrate
```
5. Create a superuser (for the admin panel)
```bash
python manage.py createsuperuser
```
6. Run the development server
```bash
python manage.py runserver
```
Visit http://127.0.0.1:8000/ in your browser 🎉
---
🔑 Key URLs
URL	Description
`/`	Dashboard (login required)
`/signup/`	Create an account (email OTP verification)
`/login/`	Log in
`/search/`	Search & filter bikes
`/analytics/`	Charts & insights
`/compare/`	Compare selected bikes
`/bike/<id>/`	Bike detail page
`/admin-records/`	Staff-only: manage records
`/import-csv/`	Staff-only: bulk CSV import
`/admin/`	Django's built-in admin site
---
⚠️ Important Security Note
Before pushing this repository publicly (or if it's already public), please rotate/remove the following from `bike_analysis/settings.py`:
`EMAIL_HOST_PASSWORD` / `EMAIL_HOST_USER` — a real Gmail app password is currently hardcoded. If this has already been pushed to GitHub, revoke that app password in your Google Account immediately and generate a new one.
`SECRET_KEY` — currently hardcoded; generate a fresh one for production.
`DEBUG = True` and `ALLOWED_HOSTS = ['*']` — fine for local development, but should be disabled/restricted before any real deployment.
The recommended fix is to move these into environment variables (e.g. using `python-decouple` or `django-environ`) and load them via a local `.env` file that is added to `.gitignore`, rather than committing them to the repo.
---
📌 Roadmap Ideas
[ ] Add `requirements.txt`
[ ] Move secrets to environment variables
[ ] Add pagination to search & admin records pages
[ ] Add unit tests for filtering and CRUD views
[ ] Deploy (Render / Railway / PythonAnywhere)
---
📄 License
This project is licensed under the MIT License — feel free to use and modify it.
---
🙋 Author
ianasaslam2209
Repository: Bike-Price-Analysis-System
