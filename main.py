# main.py
import os
import sqlite3
from functools import wraps
from flask import (Flask, render_template, redirect, url_for, request, abort,
                   session, flash)

app = Flask(__name__)


app.secret_key = os.environ.get('SECRET_KEY', 'dev-only-change-me')

# Demo account 
USERNAME = 'admin'
PASSWORD = 'admin'


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'App', 'instance', 'database.db')


def login_required(view):
    """Send logged-out users to the login page instead of running the view."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('user'):
            flash('Please log in to see your notes.')
            return redirect(url_for('login', next=request.path))
        return view(*args, **kwargs)
    return wrapped


def is_safe_next(target):
    """Only allow redirects back to pages on this site."""
    return bool(target) and target.startswith('/') and not target.startswith('//')


@app.route('/login', methods=('GET', 'POST'))
def login():
    if session.get('user'):
        return redirect(url_for('index'))
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if username == USERNAME and password == PASSWORD:
            session.clear()
            session['user'] = username   # this is what "remembers" the login
            flash(f'Logged in as {username}.')
            next_page = request.args.get('next')
            return redirect(next_page if is_safe_next(next_page) else url_for('index'))
        error = 'Invalid credentials. Please try again.'
    return render_template('login.html', error=error)


@app.route('/logout', methods=('GET', 'POST'))
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_note(note_id):
    conn = get_db_connection()
    note = conn.execute('SELECT * FROM notes WHERE id = ?', (note_id,)).fetchone()
    conn.close()
    if note is None:
        abort(404)
    return note


def read_and_validate(form):
    """Return (values, error). error is None when the form is valid."""
    values = {
        'topic': form.get('topic', '').strip(),
        'description': form.get('description', '').strip(),
        'issue_details': form.get('issue_details', '').strip(),
        'status': form.get('status', 'open'),
        'attempts': form.get('attempts', '').strip(),
        'resolution': form.get('resolution', '').strip(),
        'lessons_learned': form.get('lessons_learned', '').strip(),
    }
    error = None
    if not values['topic'] or not values['description'] or not values['issue_details']:
        error = 'Topic, description, and issue details are required.'
    elif values['status'] not in ('open', 'resolved'):
        error = 'Status must be Open or Resolved.'
    elif values['status'] == 'resolved' and not (values['resolution'] and values['lessons_learned']):
        error = 'A resolved note needs both "How it was resolved" and "What I learned".'
    return values, error


@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    notes = conn.execute('SELECT * FROM notes ORDER BY created DESC').fetchall()
    conn.close()
    return render_template('index.html', notes=notes)


@app.route('/<int:note_id>')
@login_required
def note(note_id):
    item = get_note(note_id)
    return render_template('note.html', item=item)


@app.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    values, error = {}, None
    if request.method == 'POST':
        values, error = read_and_validate(request.form)
        if error is None:
            conn = get_db_connection()
            conn.execute(
                '''INSERT INTO notes (topic, description, issue_details, status,
                                      attempts, resolution, lessons_learned)
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (values['topic'], values['description'], values['issue_details'],
                 values['status'], values['attempts'], values['resolution'],
                 values['lessons_learned']))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
    return render_template('create.html', values=values, error=error)


@app.route('/<int:note_id>/edit', methods=('GET', 'POST'))
@login_required
def edit(note_id):
    item = get_note(note_id)
    values, error = item, None  # GET: pre-fill from the saved note
    if request.method == 'POST':
        values, error = read_and_validate(request.form)
        if error is None:
            conn = get_db_connection()
            conn.execute(
                '''UPDATE notes SET topic = ?, description = ?, issue_details = ?,
                                    status = ?, attempts = ?, resolution = ?,
                                    lessons_learned = ?, updated = CURRENT_TIMESTAMP
                   WHERE id = ?''',
                (values['topic'], values['description'], values['issue_details'],
                 values['status'], values['attempts'], values['resolution'],
                 values['lessons_learned'], note_id))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
    return render_template('edit.html', item=item, values=values, error=error)


@app.route('/<int:note_id>/delete', methods=('POST',))
@login_required
def delete(note_id):
    get_note(note_id)  # 404 if it doesn't exist
    conn = get_db_connection()
    conn.execute('DELETE FROM notes WHERE id = ?', (note_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))
