from flask import Flask, render_template, redirect, url_for
from app import create_app, db
from app.database import init_database, get_database_stats
import os

# Create Flask app
app = create_app('development')

@app.route('/')
def index():
    """Main landing page"""
    return redirect(url_for('auth.login'))

@app.route('/stats')
def stats():
    """Database statistics page (for development)"""
    stats = get_database_stats()
    return f"<h1>Database Stats</h1><pre>{stats}</pre>"

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        # Create database tables and initial data
        if not os.path.exists('hospital_management.db'):
            print("Creating database for the first time...")
            init_database()
        else:
            print("Database already exists")

    print("\n" + "="*50)
    print("HOSPITAL MANAGEMENT SYSTEM")
    print("="*50)
    print("Starting Flask application...")
    print("Default Admin Credentials:")
    print("Username: admin")
    print("Password: admin123")
    print("="*50)

    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000)
