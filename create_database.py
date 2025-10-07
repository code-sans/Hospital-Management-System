#!/usr/bin/env python3
"""
Database Setup Script for Hospital Management System
Creates database tables and initial data.
"""

import os
import sys
from datetime import datetime

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def main():
    """This function handles the main database setup process"""
    print("Hospital Management System - Setting up Database")
    print("=" * 50)
    print(f"Starting setup on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Working in directory: {project_root}")
    print("=" * 50)
    
    try:
        # Import Flask app and database components
        from app import create_app, db
        from app.database import init_database, get_database_stats, print_database_structure
        
        # Create Flask application context
        app = create_app('development')
        
        with app.app_context():
            print("Setting up database tables and relationships...")
            
            # This creates all our database tables and adds initial data
            init_database()
            
            # Let's see what we've got in our database now
            print("\nDatabase Summary:")
            stats = get_database_stats()
            for key, value in stats.items():
                display_name = key.replace('_', ' ').title()
                print(f"   {display_name}: {value}")
            
            # Check if the database file was actually created
            db_path = os.path.join(project_root, 'instance', 'hospital_management.db')
            if os.path.exists(db_path):
                file_size = os.path.getsize(db_path)
                print(f"\nDatabase file successfully created at: {db_path}")
                print(f"File size: {file_size} bytes")
            else:
                print(f"\nWarning: Could not find database file at: {db_path}")
            
            print("\nDatabase setup completed successfully!")
            print("\nDefault admin login details:")
            print("   Username: admin")
            print("   Password: admin123")
            print("   Email: admin@hospital.com")
            
            return True
            
    except ImportError as e:
        print(f"Import Error: {str(e)}")
        print("Make sure you have installed all required packages:")
        print("   pip install -r requirements.txt")
        return False
        
    except Exception as e:
        print(f"Database setup failed: {str(e)}")
        return False

def verify_models():
    """Check if all our database models are working correctly"""
    try:
        from app.models import (
            User, Admin, Department, Specialization, Doctor, Patient,
            Appointment, Treatment, DoctorAvailability, DoctorSchedule,
            MedicalRecord, Prescription
        )
        
        models = [
            User, Admin, Department, Specialization, Doctor, Patient,
            Appointment, Treatment, DoctorAvailability, DoctorSchedule,
            MedicalRecord, Prescription
        ]
        
        print("Checking all database models:")
        for model in models:
            print(f"   {model.__name__} - OK")
            
        return True
        
    except ImportError as e:
        print(f"Model verification failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting Hospital Management System Database Setup...")
    print("This will create all the database tables and set up initial data.\n")
    
    # First, let's make sure all our models are working
    if not verify_models():
        sys.exit(1)
    
    # Now let's create the actual database
    if main():
        print("\nSUCCESS! The database is now ready for the Hospital Management System.")
        print("You can start the application by running: python app.py")
    else:
        print("\nFAILED! Please check the error messages above and try again.")
        sys.exit(1)