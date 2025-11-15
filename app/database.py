from app import db
from app.models import (
    User, Admin, Department, Specialization, Doctor, Patient, 
    Appointment, Treatment, DoctorAvailability, DoctorSchedule,
    MedicalRecord, Prescription
)
from datetime import datetime, date, time
import sqlite3

def init_database():
    """Make the database only if it doesn't exist or is missing tables"""
    try:
        try:
            existing_users = User.query.count()
            print(f"There are total {existing_users} users")
            print("Skipping database initialization because of existing data")
            return
        except Exception:
            # Tables don't exist yet, so we need to create them
            print("Database tables don't exist yet, creating new database...")
        
        # Create all our database tables based on  models.py
        print("Building new database tables.....................")
        db.create_all()
        print("Database tables created successfully!")

        # Now let's add some basic data that we need to get started
        create_default_admin()
        create_sample_departments()

        print("Database initialization completed!")
        
    except Exception as e:
        print(f"Database initialization failed: {str(e)}")
        db.session.rollback()
        raise

def reset_database():
    """Reset the database from scratch"""
    try:
        print("WARNING: This will delete all existing data!")
        print("Removing any existing database tables...")
        db.drop_all()
        
        # Create all our database tables based on the models defined
        print("In process of Building new database tables")
        db.create_all()
        print(" tables created successfully!")

        create_default_admin()
        create_sample_departments()
        

        print("Database reset completed!")
        
    except Exception as e:
        print(f"Database reset failed: {str(e)}")
        db.session.rollback()
        raise

def create_default_admin():
    """Setting up the default administrator"""
    try:
        existing_admin = User.query.filter_by(username='admin', role='admin').first()
        if existing_admin:
            print("Admin user already exists in the system")
            return

        # Create the main admin
        admin_user = User(
            username='admin',
            email='admin@test.com',
            role='admin',
            first_name='System',
            last_name='Administrator'
        )
        admin_user.set_password('admin123') 
        db.session.add(admin_user)
        db.session.flush()  # This gives us the user ID we need

        admin_profile = Admin(
            user_id=admin_user.id,
            employee_id='EMP01',
            access_level='super_admin',
            phone='+911234567890'
        )
        db.session.add(admin_profile)
        db.session.commit()
        
        print("Default admin account created:")
        print("   Username: admin")
        print("   Password: admin123")
        print("   Employee ID: EMP001")
        
    except Exception as e:
        print(f"Error creating admin account: {str(e)}")
        db.session.rollback()
        raise

def create_sample_departments():
    """Create sample medical departments"""
    sample_departments = [
        {'name': 'Cardiology', 'code': 'CARD', 'description': 'Heart and cardiovascular system'},
        {'name': 'Neurology', 'code': 'NEURO', 'description': 'Nervous system and brain'},
        {'name': 'Orthopedics', 'code': 'ORTHO', 'description': 'Bones, joints, and muscles'},
        {'name': 'Pediatrics', 'code': 'PEDI', 'description': 'Children healthcare'},
        {'name': 'Gynecology', 'code': 'GYN', 'description': 'Women health and reproductive system'},
        {'name': 'Dermatology', 'code': 'DERM', 'description': 'Skin and related conditions'},
        {'name': 'General Medicine', 'code': 'GENMED', 'description': 'General healthcare and consultation'},
        {'name': 'Emergency Medicine', 'code': 'EMERG', 'description': 'Emergency and trauma care'},
        {'name': 'Psychiatry', 'code': 'PSYCH', 'description': 'Mental health and behavioral disorders'},
        {'name': 'Radiology', 'code': 'RAD', 'description': 'Medical imaging and diagnostics'}
    ]

    try:
        created_count = 0
        for dept_data in sample_departments:
            existing_dept = Department.query.filter_by(name=dept_data['name']).first()
            if not existing_dept:
                department = Department(
                    name=dept_data['name'],
                    code=dept_data['code'],
                    description=dept_data['description']
                )
                db.session.add(department)
                created_count += 1

        db.session.commit()
        print(f"{created_count} departments created")
        
    except Exception as e:
        print(f" Error creating departments: {str(e)}")
        db.session.rollback()
        raise

def reset_database():
    """Reset the entire database - USE WITH CAUTION"""
    db.drop_all()
    print("All tables dropped")
    init_database()
