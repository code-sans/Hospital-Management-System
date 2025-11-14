from flask import Flask, render_template, redirect, url_for
from app import create_app, db
from app.database import init_database, get_database_stats
import os
app = create_app('development')
@app.route('/')
def index():
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    with app.app_context():
        # Create database
        if not os.path.exists('hospital_management.db'):
            print("Creating database first time")
            init_database()
        else:
            print("Database exists")
   
    print("HOSPITAL MANAGEMENT SYSTEM")
    print("Default:")
    print("Username: admin ,Password: admin123")
    app.run(debug=True, host='0.0.0.0', port=5000)
