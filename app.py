import os
import secrets
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import requests

# Initialize Flask app
app = Flask(__name__)

# Configuration
# class Config:
#     SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
#     UPLOAD_FOLDER = 'uploads'
#     MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
#     DATABASE = 'database.db'
#     ALLOWED_EXTENSIONS = {'pdf'}
#     # Google OAuth Configuration
#     GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
#     GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
#     GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    DATABASE = 'database.db'
    ALLOWED_EXTENSIONS = {'pdf'}
    # Google OAuth - Use demo values for development
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', 'demo-google-client-id')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', 'demo-google-client-secret')
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

app.config.from_object(Config)

def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def migrate_database():
    """Migrate database schema to latest version"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if users table has email column
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add missing columns to users table
        if 'email' not in columns:
            print("Adding email column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN email TEXT UNIQUE")
        
        if 'google_id' not in columns:
            print("Adding google_id column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN google_id TEXT UNIQUE")
        
        if 'created_at' not in columns:
            print("Adding created_at column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        
        if 'is_active' not in columns:
            print("Adding is_active column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
        
        # Check if subjects table has is_active column
        cursor.execute("PRAGMA table_info(subjects)")
        subject_columns = [column[1] for column in cursor.fetchall()]
        
        if 'is_active' not in subject_columns:
            print("Adding is_active column to subjects table...")
            cursor.execute("ALTER TABLE subjects ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
        
        # Check if pdfs table has is_active and description columns
        cursor.execute("PRAGMA table_info(pdfs)")
        pdf_columns = [column[1] for column in cursor.fetchall()]
        
        if 'is_active' not in pdf_columns:
            print("Adding is_active column to pdfs table...")
            cursor.execute("ALTER TABLE pdfs ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
        
        if 'description' not in pdf_columns:
            print("Adding description column to pdfs table...")
            cursor.execute("ALTER TABLE pdfs ADD COLUMN description TEXT")
        
        conn.commit()
        print("Database migration completed successfully!")
        
    except Exception as e:
        print(f"Database migration error: {e}")
        conn.rollback()
    finally:
        conn.close()

def init_db():
    """Initialize the database with required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table with all columns
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  email TEXT UNIQUE,
                  password TEXT,
                  is_admin BOOLEAN DEFAULT FALSE,
                  google_id TEXT UNIQUE,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  is_active BOOLEAN DEFAULT TRUE)''')
    
    # Subjects table
    cursor.execute('''CREATE TABLE IF NOT EXISTS subjects
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  year TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  is_active BOOLEAN DEFAULT TRUE)''')
    
    # PDFs table
    cursor.execute('''CREATE TABLE IF NOT EXISTS pdfs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  subject_id INTEGER,
                  filename TEXT NOT NULL,
                  original_filename TEXT NOT NULL,
                  description TEXT,
                  upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  is_active BOOLEAN DEFAULT TRUE,
                  FOREIGN KEY (subject_id) REFERENCES subjects (id))''')
    
    # News table
    cursor.execute('''CREATE TABLE IF NOT EXISTS news
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT NOT NULL,
                  content TEXT NOT NULL,
                  is_active BOOLEAN DEFAULT TRUE,
                  created_by INTEGER,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (created_by) REFERENCES users (id))''')
    
    # Create default admin user if not exists
    try:
        # Check if admin user exists
        admin_exists = cursor.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()
        
        if not admin_exists:
            admin_password = generate_password_hash('admin123')
            cursor.execute("INSERT INTO users (username, email, password, is_admin) VALUES (?, ?, ?, ?)",
                          ('admin', 'admin@edupdf.com', admin_password, True))
            print("Created default admin user")
        
        # Check if test user exists
        user_exists = cursor.execute("SELECT id FROM users WHERE username = 'user'").fetchone()
        
        if not user_exists:
            user_password = generate_password_hash('user123')
            cursor.execute("INSERT INTO users (username, email, password, is_admin) VALUES (?, ?, ?, ?)",
                          ('user', 'user@edupdf.com', user_password, False))
            print("Created default test user")
            
    except sqlite3.IntegrityError as e:
        print(f"User creation error: {e}")
    
    # Create sample news if not exists
    try:
        news_count = cursor.execute("SELECT COUNT(*) FROM news").fetchone()[0]
        if news_count == 0:
            sample_news = [
                ("🎉 New Mathematics PDFs Added", "We've added new mathematics study materials for 2024 curriculum.", 1),
                ("📚 Physics Materials Updated", "Latest physics textbooks and reference materials are now available.", 1),
                ("🌟 Dark/Light Mode Support", "Website now supports both dark and light themes for better reading experience.", 1),
            ]
            
            for title, content, created_by in sample_news:
                cursor.execute("INSERT INTO news (title, content, created_by) VALUES (?, ?, ?)",
                              (title, content, created_by))
            print("Created sample news items")
    except Exception as e:
        print(f"News creation error: {e}")
    
    # Create sample subjects if not exists
    try:
        subject_count = cursor.execute("SELECT COUNT(*) FROM subjects").fetchone()[0]
        if subject_count == 0:
            sample_subjects = [
                ('Mathematics', '2024'),
                ('Physics', '2024'),
                ('Computer Science', '2024'),
                ('Chemistry', '2024'),
                ('Biology', '2024')
            ]
            
            for subject_name, year in sample_subjects:
                cursor.execute("INSERT INTO subjects (name, year) VALUES (?, ?)",
                              (subject_name, year))
            print("Created sample subjects")
    except Exception as e:
        print(f"Subject creation error: {e}")
    
    conn.commit()
    conn.close()

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_active_news():
    """Get all active news items"""
    conn = get_db_connection()
    news = conn.execute('''
        SELECT n.*, u.username as author 
        FROM news n 
        LEFT JOIN users u ON n.created_by = u.id 
        WHERE n.is_active = TRUE 
        ORDER BY n.created_at DESC
    ''').fetchall()
    conn.close()
    return news

def get_google_provider_cfg():
    """Get Google OAuth provider configuration"""
    try:
        return requests.get(app.config['GOOGLE_DISCOVERY_URL']).json()
    except:
        return {}

def login_required(f):
    """Decorator to require login for routes"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin privileges for routes"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        if not session.get('is_admin'):
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    """Home page route"""
    news_items = get_active_news()
    return render_template('index.html', news_items=news_items)

@app.route('/about')
def about():
    """About page route"""
    return render_template('about.html')

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login route"""
    if 'user_id' in session:
        if session.get('is_admin'):
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Please fill in all fields.', 'danger')
            return render_template('login.html')
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND is_active = TRUE', (username,)
        ).fetchone()
        conn.close()
        
        if user and user['password'] and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = bool(user['is_admin'])
            session['login_method'] = 'email'
            
            flash(f'Welcome back, {user["username"]}!', 'success')
            
            if user['is_admin']:
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html', google_client_id=app.config['GOOGLE_CLIENT_ID'])

@app.route('/google-login')
def google_login():
    """Initialize Google OAuth flow"""
    if not app.config['GOOGLE_CLIENT_ID']:
        flash('Google login is not configured.', 'warning')
        return redirect(url_for('login'))
    
    try:
        google_provider_cfg = get_google_provider_cfg()
        if not google_provider_cfg:
            flash('Google login is temporarily unavailable.', 'warning')
            return redirect(url_for('login'))
        
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]
        
        request_uri = f"{authorization_endpoint}?client_id={app.config['GOOGLE_CLIENT_ID']}&response_type=code&scope=openid%20email%20profile&redirect_uri={url_for('google_callback', _external=True)}"
        
        return redirect(request_uri)
    except Exception as e:
        flash('Google login is currently unavailable.', 'warning')
        return redirect(url_for('login'))

@app.route('/google-callback')
def google_callback():
    """Google OAuth callback"""
    if not app.config['GOOGLE_CLIENT_ID']:
        flash('Google login is not configured.', 'warning')
        return redirect(url_for('login'))
    
    # Get authorization code Google sent back
    code = request.args.get("code")
    
    if not code:
        flash('Google login failed. Please try again.', 'danger')
        return redirect(url_for('login'))
    
    try:
        # Get token endpoint
        google_provider_cfg = get_google_provider_cfg()
        token_endpoint = google_provider_cfg["token_endpoint"]
        
        # Prepare and send token request
        token_url, headers, body = requests.auth.HTTPBasicAuth(
            app.config['GOOGLE_CLIENT_ID'], app.config['GOOGLE_CLIENT_SECRET']
        ).prepare_token_request(
            token_endpoint,
            authorization_response=request.url,
            redirect_url=url_for('google_callback', _external=True),
            code=code
        )
        
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(app.config['GOOGLE_CLIENT_ID'], app.config['GOOGLE_CLIENT_SECRET']),
        )
        
        # Parse tokens
        tokens = token_response.json()
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        userinfo_response = requests.get(
            userinfo_endpoint,
            headers={'Authorization': f"Bearer {tokens['access_token']}"},
        )
        
        userinfo = userinfo_response.json()
        
        # Check if user exists or create new user
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE google_id = ? OR email = ?', 
            (userinfo['sub'], userinfo['email'])
        ).fetchone()
        
        if user:
            # Update google_id if not set
            if not user['google_id']:
                conn.execute('UPDATE users SET google_id = ? WHERE id = ?', (userinfo['sub'], user['id']))
                conn.commit()
        else:
            # Create new user
            username = userinfo['email'].split('@')[0]
            # Ensure username is unique
            counter = 1
            original_username = username
            while conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone():
                username = f"{original_username}{counter}"
                counter += 1
            
            conn.execute(
                "INSERT INTO users (username, email, google_id, is_admin) VALUES (?, ?, ?, ?)",
                (username, userinfo['email'], userinfo['sub'], False)
            )
            conn.commit()
            user = conn.execute('SELECT * FROM users WHERE google_id = ?', (userinfo['sub'],)).fetchone()
        
        conn.close()
        
        # Log the user in
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['is_admin'] = bool(user['is_admin'])
        session['login_method'] = 'google'
        
        flash(f'Welcome, {user["username"]}!', 'success')
        
        if user['is_admin']:
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('dashboard'))
            
    except Exception as e:
        print(f"Google login error: {e}")
        flash('Google login failed. Please try again.', 'danger')
        return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not username or not email or not password:
            flash('Please fill in all fields.', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
        
        if len(username) < 3:
            flash('Username must be at least 3 characters long.', 'danger')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html')
        
        conn = get_db_connection()
        
        try:
            hashed_password = generate_password_hash(password)
            conn.execute(
                "INSERT INTO users (username, email, password, is_admin) VALUES (?, ?, ?, ?)",
                (username, email, hashed_password, False)
            )
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError as e:
            if 'username' in str(e):
                flash('Username already exists. Please choose a different one.', 'danger')
            elif 'email' in str(e):
                flash('Email already exists. Please use a different email.', 'danger')
            else:
                flash('Registration failed. Please try again.', 'danger')
        except Exception as e:
            flash('An error occurred during registration. Please try again.', 'danger')
        finally:
            conn.close()
    
    return render_template('register.html', google_client_id=app.config['GOOGLE_CLIENT_ID'])

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard showing all subjects"""
    conn = get_db_connection()
    subjects = conn.execute(
        'SELECT * FROM subjects WHERE is_active = TRUE ORDER BY name'
    ).fetchall()
    conn.close()
    
    return render_template('dashboard.html', subjects=subjects)

# Admin Dashboard and Management
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard with comprehensive statistics"""
    conn = get_db_connection()
    
    # Get counts for admin dashboard
    subject_count = conn.execute('SELECT COUNT(*) FROM subjects WHERE is_active = TRUE').fetchone()[0]
    pdf_count = conn.execute('SELECT COUNT(*) FROM pdfs WHERE is_active = TRUE').fetchone()[0]
    user_count = conn.execute('SELECT COUNT(*) FROM users WHERE is_admin = FALSE AND is_active = TRUE').fetchone()[0]
    news_count = conn.execute('SELECT COUNT(*) FROM news WHERE is_active = TRUE').fetchone()[0]
    total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    total_pdfs = conn.execute('SELECT COUNT(*) FROM pdfs').fetchone()[0]
    
    # Get recent uploads
    recent_uploads = conn.execute('''
        SELECT p.original_filename, s.name as subject_name, p.upload_date 
        FROM pdfs p 
        JOIN subjects s ON p.subject_id = s.id 
        WHERE p.is_active = TRUE
        ORDER BY p.upload_date DESC 
        LIMIT 5
    ''').fetchall()
    
    # Get recent users
    recent_users = conn.execute('''
        SELECT username, email, created_at, google_id IS NOT NULL as is_google_user
        FROM users 
        WHERE is_admin = FALSE 
        ORDER BY created_at DESC 
        LIMIT 5
    ''').fetchall()
    
    # Get recent news
    recent_news = conn.execute('''
        SELECT n.title, n.created_at, u.username as author 
        FROM news n 
        LEFT JOIN users u ON n.created_by = u.id 
        WHERE n.is_active = TRUE 
        ORDER BY n.created_at DESC 
        LIMIT 5
    ''').fetchall()
    
    conn.close()
    
    return render_template('admin_dashboard.html', 
                         subject_count=subject_count,
                         pdf_count=pdf_count,
                         user_count=user_count,
                         news_count=news_count,
                         total_users=total_users,
                         total_pdfs=total_pdfs,
                         recent_uploads=recent_uploads,
                         recent_users=recent_users,
                         recent_news=recent_news)

# User Management
@app.route('/admin/users')
@admin_required
def manage_users():
    """Manage users page"""
    conn = get_db_connection()
    users = conn.execute('''
        SELECT id, username, email, is_admin, is_active, created_at, 
               google_id IS NOT NULL as is_google_user
        FROM users 
        ORDER BY created_at DESC
    ''').fetchall()
    conn.close()
    
    return render_template('manage_users.html', users=users)

@app.route('/admin/users/toggle/<int:user_id>')
@admin_required
def toggle_user(user_id):
    """Toggle user active status"""
    if user_id == session['user_id']:
        flash('You cannot deactivate your own account.', 'danger')
        return redirect(url_for('manage_users'))
    
    conn = get_db_connection()
    try:
        user = conn.execute('SELECT is_active FROM users WHERE id = ?', (user_id,)).fetchone()
        if user:
            new_status = not user['is_active']
            conn.execute(
                "UPDATE users SET is_active = ? WHERE id = ?",
                (new_status, user_id)
            )
            conn.commit()
            status_text = "activated" if new_status else "deactivated"
            flash(f'User {status_text} successfully!', 'success')
    except Exception as e:
        flash('Error updating user. Please try again.', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('manage_users'))

@app.route('/admin/users/delete/<int:user_id>')
@admin_required
def delete_user(user_id):
    """Delete user"""
    if user_id == session['user_id']:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('manage_users'))
    
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        flash('User deleted successfully!', 'success')
    except Exception as e:
        flash('Error deleting user. Please try again.', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('manage_users'))

@app.route('/admin/users/make-admin/<int:user_id>')
@admin_required
def make_admin(user_id):
    """Make user an admin"""
    if user_id == session['user_id']:
        flash('You are already an admin.', 'info')
        return redirect(url_for('manage_users'))
    
    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE users SET is_admin = TRUE WHERE id = ?",
            (user_id,)
        )
        conn.commit()
        flash('User promoted to admin successfully!', 'success')
    except Exception as e:
        flash('Error promoting user. Please try again.', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('manage_users'))

@app.route('/admin/users/change-password/<int:user_id>', methods=['POST'])
@admin_required
def change_user_password(user_id):
    """Change user password"""
    new_password = request.form.get('new_password', '')
    
    if not new_password:
        flash('Please enter a new password.', 'danger')
        return redirect(url_for('manage_users'))
    
    if len(new_password) < 6:
        flash('Password must be at least 6 characters long.', 'danger')
        return redirect(url_for('manage_users'))
    
    conn = get_db_connection()
    try:
        hashed_password = generate_password_hash(new_password)
        conn.execute(
            "UPDATE users SET password = ? WHERE id = ?",
            (hashed_password, user_id)
        )
        conn.commit()
        flash('Password changed successfully!', 'success')
    except Exception as e:
        flash('Error changing password. Please try again.', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('manage_users'))

# PDF Management
@app.route('/admin/pdfs')
@admin_required
def manage_pdfs():
    """Manage all PDFs"""
    conn = get_db_connection()
    pdfs = conn.execute('''
        SELECT p.*, s.name as subject_name, s.year as subject_year
        FROM pdfs p 
        JOIN subjects s ON p.subject_id = s.id 
        ORDER BY p.upload_date DESC
    ''').fetchall()
    conn.close()
    
    return render_template('manage_pdfs.html', pdfs=pdfs)

@app.route('/admin/pdfs/toggle/<int:pdf_id>')
@admin_required
def toggle_pdf(pdf_id):
    """Toggle PDF active status"""
    conn = get_db_connection()
    try:
        pdf = conn.execute('SELECT is_active FROM pdfs WHERE id = ?', (pdf_id,)).fetchone()
        if pdf:
            new_status = not pdf['is_active']
            conn.execute(
                "UPDATE pdfs SET is_active = ? WHERE id = ?",
                (new_status, pdf_id)
            )
            conn.commit()
            status_text = "activated" if new_status else "deactivated"
            flash(f'PDF {status_text} successfully!', 'success')
    except Exception as e:
        flash('Error updating PDF. Please try again.', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('manage_pdfs'))

@app.route('/admin/pdfs/delete/<int:pdf_id>')
@admin_required
def delete_pdf(pdf_id):
    """Delete PDF"""
    conn = get_db_connection()
    try:
        pdf = conn.execute('SELECT filename FROM pdfs WHERE id = ?', (pdf_id,)).fetchone()
        if pdf:
            # Delete file from filesystem
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf['filename'])
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Delete from database
            conn.execute("DELETE FROM pdfs WHERE id = ?", (pdf_id,))
            conn.commit()
            flash('PDF deleted successfully!', 'success')
    except Exception as e:
        flash('Error deleting PDF. Please try again.', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('manage_pdfs'))

@app.route('/admin/pdfs/edit/<int:pdf_id>', methods=['GET', 'POST'])
@admin_required
def edit_pdf(pdf_id):
    """Edit PDF details"""
    conn = get_db_connection()
    
    if request.method == 'POST':
        description = request.form.get('description', '').strip()
        
        try:
            conn.execute(
                "UPDATE pdfs SET description = ? WHERE id = ?",
                (description, pdf_id)
            )
            conn.commit()
            flash('PDF updated successfully!', 'success')
            return redirect(url_for('manage_pdfs'))
        except Exception as e:
            flash('Error updating PDF. Please try again.', 'danger')
        finally:
            conn.close()
    
    pdf = conn.execute('''
        SELECT p.*, s.name as subject_name 
        FROM pdfs p 
        JOIN subjects s ON p.subject_id = s.id 
        WHERE p.id = ?
    ''', (pdf_id,)).fetchone()
    conn.close()
    
    if not pdf:
        flash('PDF not found.', 'danger')
        return redirect(url_for('manage_pdfs'))
    
    return render_template('edit_pdf.html', pdf=pdf)

# Subject Management
@app.route('/admin/subjects')
@admin_required
def manage_subjects():
    """Admin page to manage subjects"""
    conn = get_db_connection()
    
    subjects = conn.execute('''
        SELECT s.*, COUNT(p.id) as pdf_count 
        FROM subjects s 
        LEFT JOIN pdfs p ON s.id = p.subject_id AND p.is_active = TRUE
        GROUP BY s.id 
        ORDER BY s.name
    ''').fetchall()
    
    conn.close()
    
    return render_template('manage_subjects.html', subjects=subjects)

@app.route('/admin/subjects/toggle/<int:subject_id>')
@admin_required
def toggle_subject(subject_id):
    """Toggle subject active status"""
    conn = get_db_connection()
    try:
        subject = conn.execute('SELECT is_active FROM subjects WHERE id = ?', (subject_id,)).fetchone()
        if subject:
            new_status = not subject['is_active']
            conn.execute(
                "UPDATE subjects SET is_active = ? WHERE id = ?",
                (new_status, subject_id)
            )
            conn.commit()
            status_text = "activated" if new_status else "deactivated"
            flash(f'Subject {status_text} successfully!', 'success')
    except Exception as e:
        flash('Error updating subject. Please try again.', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('manage_subjects'))

@app.route('/admin/subjects/delete/<int:subject_id>')
@admin_required
def delete_subject(subject_id):
    """Delete subject and its PDFs"""
    conn = get_db_connection()
    try:
        # Get all PDFs for this subject to delete files
        pdfs = conn.execute('SELECT filename FROM pdfs WHERE subject_id = ?', (subject_id,)).fetchall()
        
        # Delete PDF files from filesystem
        for pdf in pdfs:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf['filename'])
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # Delete from database
        conn.execute("DELETE FROM pdfs WHERE subject_id = ?", (subject_id,))
        conn.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
        conn.commit()
        flash('Subject and all associated PDFs deleted successfully!', 'success')
    except Exception as e:
        flash('Error deleting subject. Please try again.', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('manage_subjects'))

# News Management
@app.route('/admin/news')
@admin_required
def manage_news():
    """Manage news page"""
    conn = get_db_connection()
    news_items = conn.execute('''
        SELECT n.*, u.username as author 
        FROM news n 
        LEFT JOIN users u ON n.created_by = u.id 
        ORDER BY n.created_at DESC
    ''').fetchall()
    conn.close()
    
    return render_template('manage_news.html', news_items=news_items)

@app.route('/admin/news/add', methods=['GET', 'POST'])
@admin_required
def add_news():
    """Add new news item"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        is_active = request.form.get('is_active', 'false') == 'true'
        
        if not title or not content:
            flash('Please fill in all fields.', 'danger')
            return render_template('add_news.html')
        
        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO news (title, content, is_active, created_by) VALUES (?, ?, ?, ?)",
                (title, content, is_active, session['user_id'])
            )
            conn.commit()
            flash('News item added successfully!', 'success')
            return redirect(url_for('manage_news'))
        except Exception as e:
            flash('Error adding news item. Please try again.', 'danger')
        finally:
            conn.close()
    
    return render_template('add_news.html')

@app.route('/admin/news/edit/<int:news_id>', methods=['GET', 'POST'])
@admin_required
def edit_news(news_id):
    """Edit news item"""
    conn = get_db_connection()
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        is_active = request.form.get('is_active', 'false') == 'true'
        
        if not title or not content:
            flash('Please fill in all fields.', 'danger')
            news_item = conn.execute('SELECT * FROM news WHERE id = ?', (news_id,)).fetchone()
            conn.close()
            return render_template('edit_news.html', news_item=news_item)
        
        try:
            conn.execute(
                "UPDATE news SET title = ?, content = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (title, content, is_active, news_id)
            )
            conn.commit()
            flash('News item updated successfully!', 'success')
            return redirect(url_for('manage_news'))
        except Exception as e:
            flash('Error updating news item. Please try again.', 'danger')
        finally:
            conn.close()
    
    news_item = conn.execute('SELECT * FROM news WHERE id = ?', (news_id,)).fetchone()
    conn.close()
    
    if not news_item:
        flash('News item not found.', 'danger')
        return redirect(url_for('manage_news'))
    
    return render_template('edit_news.html', news_item=news_item)

@app.route('/admin/news/delete/<int:news_id>')
@admin_required
def delete_news(news_id):
    """Delete news item"""
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM news WHERE id = ?", (news_id,))
        conn.commit()
        flash('News item deleted successfully!', 'success')
    except Exception as e:
        flash('Error deleting news item. Please try again.', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('manage_news'))

@app.route('/admin/news/toggle/<int:news_id>')
@admin_required
def toggle_news(news_id):
    """Toggle news item active status"""
    conn = get_db_connection()
    try:
        news_item = conn.execute('SELECT is_active FROM news WHERE id = ?', (news_id,)).fetchone()
        if news_item:
            new_status = not news_item['is_active']
            conn.execute(
                "UPDATE news SET is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (new_status, news_id)
            )
            conn.commit()
            status_text = "activated" if new_status else "deactivated"
            flash(f'News item {status_text} successfully!', 'success')
    except Exception as e:
        flash('Error updating news item. Please try again.', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('manage_news'))

# PDF Upload
@app.route('/admin/upload', methods=['GET', 'POST'])
@admin_required
def upload_pdf():
    """Admin PDF upload route"""
    conn = get_db_connection()
    subjects = conn.execute('SELECT * FROM subjects WHERE is_active = TRUE ORDER BY name').fetchall()
    
    if request.method == 'POST':
        subject_id = request.form.get('subject_id', '').strip()
        pdf_file = request.files.get('pdf_file')
        description = request.form.get('description', '').strip()
        
        # Validate form data
        if not subject_id:
            flash('Please select a subject.', 'danger')
            return render_template('upload.html', subjects=subjects)
        
        if not pdf_file or pdf_file.filename == '':
            flash('Please select a PDF file.', 'danger')
            return render_template('upload.html', subjects=subjects)
        
        if not allowed_file(pdf_file.filename):
            flash('Only PDF files are allowed.', 'danger')
            return render_template('upload.html', subjects=subjects)
        
        # Secure the filename and create unique name
        filename = secure_filename(pdf_file.filename)
        unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        try:
            # Save the file
            pdf_file.save(file_path)
            
            # Insert PDF record
            conn.execute(
                "INSERT INTO pdfs (subject_id, filename, original_filename, description) VALUES (?, ?, ?, ?)",
                (subject_id, unique_filename, filename, description)
            )
            
            conn.commit()
            flash(f'PDF "{filename}" uploaded successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
            
        except Exception as e:
            # Clean up uploaded file if database operation fails
            if os.path.exists(file_path):
                os.remove(file_path)
            flash('Error uploading file. Please try again.', 'danger')
        finally:
            conn.close()
    
    conn.close()
    return render_template('upload.html', subjects=subjects)

# Existing routes for subjects, PDF viewing, etc.
@app.route('/subject/<int:subject_id>')
@login_required
def subject_pdfs(subject_id):
    """Show all PDFs for a specific subject"""
    conn = get_db_connection()
    
    # Get subject details
    subject = conn.execute(
        'SELECT * FROM subjects WHERE id = ? AND is_active = TRUE', (subject_id,)
    ).fetchone()
    
    if not subject:
        flash('Subject not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get all PDFs for this subject
    pdfs = conn.execute(
        '''SELECT * FROM pdfs 
           WHERE subject_id = ? AND is_active = TRUE
           ORDER BY upload_date DESC''', 
        (subject_id,)
    ).fetchall()
    
    conn.close()
    
    return render_template('subjects.html', subject=subject, pdfs=pdfs)

@app.route('/view_pdf/<int:pdf_id>')
@login_required
def view_pdf(pdf_id):
    """View PDF in browser"""
    conn = get_db_connection()
    pdf = conn.execute(
        'SELECT filename, original_filename FROM pdfs WHERE id = ? AND is_active = TRUE', (pdf_id,)
    ).fetchone()
    conn.close()
    
    if not pdf:
        flash('PDF not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf['filename'])
    
    if not os.path.exists(pdf_path):
        flash('PDF file not found on server.', 'danger')
        return redirect(url_for('dashboard'))
    
    return send_file(pdf_path, as_attachment=False)

@app.route('/download_pdf/<int:pdf_id>')
@login_required
def download_pdf(pdf_id):
    """Download PDF file"""
    conn = get_db_connection()
    pdf = conn.execute(
        'SELECT filename, original_filename FROM pdfs WHERE id = ? AND is_active = TRUE', (pdf_id,)
    ).fetchone()
    conn.close()
    
    if not pdf:
        flash('PDF not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf['filename'])
    
    if not os.path.exists(pdf_path):
        flash('PDF file not found on server.', 'danger')
        return redirect(url_for('dashboard'))
    
    return send_file(
        pdf_path, 
        as_attachment=True, 
        download_name=pdf['original_filename']
    )

@app.route('/logout')
def logout():
    """Logout user"""
    username = session.get('username', 'User')
    session.clear()
    flash(f'Goodbye, {username}! You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# Context processors
@app.context_processor
def inject_news():
    news_items = get_active_news()
    return dict(news_items=news_items)

@app.context_processor
def utility_processor():
    return dict(
        is_admin=lambda: session.get('is_admin', False),
        is_logged_in=lambda: 'user_id' in session,
        login_method=lambda: session.get('login_method', 'email')
    )

# Replace the existing if __name__ == '__main__' section with:

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('static/images', exist_ok=True)
    
    # Initialize database
    init_db()
    
    print("=" * 60)
    print("EduPDF Application Starting...")
    print(f"Secret Key: {app.config['SECRET_KEY']}")
    # print("Default Admin: admin / admin123")
    # print("Default User: user / user123")
    if app.config['GOOGLE_CLIENT_ID'] and app.config['GOOGLE_CLIENT_ID'] != 'demo-google-client-id':
        print("Google Login: ENABLED")
    else:
        print("Google Login: DISABLED")
    print("=" * 60)
    
    # For production, use this:
    app.run(debug=False, host='0.0.0.0', port=5000)