# EduPDF - Digital Learning Platform

A comprehensive Flask-based web application for managing and distributing educational PDF materials. This platform supports user registration, PDF management, news updates, and administrative controls with both email and Google authentication.

## 🌟 Features

### User Features

- User Registration & Authentication
  - Email/password registration
  - Google OAuth integration
  - Secure session management

- PDF Management
  - Browse subjects and PDFs
  - View PDFs in browser
  - Download PDF files

- User Experience
  - Dark/Light mode toggle
  - Responsive design
  - News updates ticker
  - Modern UI with animations

### Admin Features

- Complete Dashboard with statistics and analytics
- User Management - Activate/deactivate, promote to admin, delete users
- PDF Management - Upload, edit, activate/deactivate, delete PDFs
- Subject Management - Create, manage, and organize subjects
- News Management - Post updates and announcements
- Content Moderation - Full control over all platform content

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ (see notes for macOS below)
- pip (Python package manager)

### Installation

1. Clone or Download the Project

```bash
# If using git
git clone <repository-url>
cd pdf_website
```

2. Create Virtual Environment

```bash
python -m venv venv

# On macOS / Linux
source venv/bin/activate

# On Windows (PowerShell)
venv\Scripts\Activate.ps1
```

3. Install Dependencies

```bash
pip install -r requirements.txt
```

4. Run the Application

```bash
python app.py
```

5. Access the Application

Open your browser and go to: http://localhost:5000

Default admin login: `admin` / `admin123`
Default user login: `user` / `user123`

## 📁 Project Structure

```
pdf_website/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── database.db                     # SQLite database (auto-generated)
├── README.md                       # This file
├── uploads/                        # PDF storage directory (auto-created)
│   └── [uploaded-pdf-files]
├── static/
│   ├── style.css                   # Main stylesheet with dark/light themes
│   ├── script.js                   # JavaScript for animations and interactions
│   └── images/                     # Static images directory
└── templates/
    ├── base.html                   # Base template with navigation and footer
    ├── index.html                  # Homepage
    ├── about.html                  # About page
    ├── login.html                  # Login page with Google auth
    ├── register.html               # User registration
    ├── dashboard.html              # User dashboard
    ├── subjects.html               # Subject PDF listing
    ├── 404.html                    # 404 error page
    ├── 500.html                    # 500 error page
    ├── admin_dashboard.html        # Admin control panel
    ├── manage_users.html           # User management
    ├── manage_pdfs.html            # PDF management
    ├── manage_subjects.html        # Subject management
    ├── manage_news.html            # News management
    ├── upload.html                 # PDF upload form
    ├── add_news.html               # Add news form
    ├── edit_news.html              # Edit news form
    └── edit_pdf.html               # Edit PDF details
```

## 🗃️ Database Schema

See `app.py` for the full schema. Key tables:

- `users` - stores user accounts, hashed passwords, google_id, admin flag, active flag
- `subjects` - subject name, year, created_at, is_active
- `pdfs` - filename, original_filename, description, upload_date, subject_id, is_active
- `news` - title, content, created_by, timestamps, is_active

## ⚙️ Configuration

Create a `.env` file in the project root (recommended for production):

```
SECRET_KEY=your-secure-secret-key-here
GOOGLE_CLIENT_ID=your-google-oauth-client-id
GOOGLE_CLIENT_SECRET=your-google-oauth-client-secret
```

In `app.py` the application uses a `Config` class to read environment variables or fall back to sensible defaults.

## 🧭 macOS — Python 3.8 notes

Homebrew's main formulae may not provide older patch versions like `python@3.8`. If you specifically need Python 3.8 on macOS, use `pyenv` to install it alongside other Python versions:

```bash
# Install pyenv if not already installed
brew update
brew install pyenv

# Install build dependencies (macOS)
brew install openssl readline sqlite3 xz zlib

# Install Python 3.8.16 (example patch version)
pyenv install 3.8.16

# Set local project Python version
pyenv local 3.8.16

# Now create venv using that python
python -m venv venv
source venv/bin/activate
```

If you don't strictly need 3.8, Python 3.9+ is widely compatible and easier to install via Homebrew:

```bash
# Install latest supported python, e.g., 3.11 or 3.12
brew install python@3.11
```

## 🎨 Customization Guide

(Shortened in README — see original project README for full customization steps.)

## 🔧 Administration Guide

Default Admin Access

- Username: `admin`
- Password: `admin123`
- Email: `admin@edupdf.com`

## 🌐 Deployment

For production use a WSGI server like Gunicorn behind a reverse proxy (nginx). Example:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 🔒 Security

- Passwords hashed with Werkzeug
- File upload validation and secure filenames
- Session management and admin checks

## 🐛 Troubleshooting

Common fixes: delete `database.db` to regenerate schema, ensure `uploads/` exists and is writable, verify Google OAuth settings.

## 🤝 Contributing

Fork, create a branch, commit, push, open a PR.

---

*Generated and added README.md by assistant.*
