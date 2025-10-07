from app import db
from app.models import (
    User, Admin, Department, Specialization, Doctor, Patient, 
    Appointment, Treatment, DoctorAvailability, DoctorSchedule,
    MedicalRecord, Prescription
)
from datetime import datetime, date, time
import sqlite3

def init_database():
    """Initialize the database only if it doesn't exist or is missing tables"""
    try:
        # Check if database tables already exist by trying to query User table
        try:
            existing_users = User.query.count()
            print(f"Database already exists with {existing_users} users")
            print("Skipping database initialization to preserve existing data")
            return
        except Exception:
            # Tables don't exist yet, so we need to create them
            print("Database tables don't exist yet, creating new database...")
        
        # Create all our database tables based on the models we've defined
        print("Building new database tables...")
        db.create_all()
        print("Database tables created successfully!")

        # Now let's add some basic data that we need to get started
        create_default_admin()
        create_sample_departments()
        create_sample_specializations()

        print("Database initialization completed!")
        print_database_structure()
        
    except Exception as e:
        print(f"Database initialization failed: {str(e)}")
        db.session.rollback()
        raise

def reset_database():
    """Reset the database from scratch - WARNING: This will delete all existing data!"""
    try:
        print("WARNING: This will delete all existing data!")
        print("Removing any existing database tables...")
        db.drop_all()
        
        # Create all our database tables based on the models we've defined
        print("Building new database tables...")
        db.create_all()
        print("Database tables created successfully!")

        # Now let's add some basic data that we need to get started
        create_default_admin()
        create_sample_departments()
        create_sample_specializations()

        print("Database reset completed!")
        print_database_structure()
        
    except Exception as e:
        print(f"Database reset failed: {str(e)}")
        db.session.rollback()
        raise

def create_default_admin():
    """Set up the default administrator account for the system"""
    try:
        # First, let's check if we already have an admin user
        existing_admin = User.query.filter_by(username='admin', role='admin').first()
        if existing_admin:
            print("Admin user already exists in the system")
            return

        # Create the main admin user account
        admin_user = User(
            username='admin',
            email='admin@hospital.com',
            role='admin',
            first_name='System',
            last_name='Administrator'
        )
        admin_user.set_password('admin123')  # This is the default password
        db.session.add(admin_user)
        db.session.flush()  # This gives us the user ID we need

        # Now create the admin profile with additional details
        admin_profile = Admin(
            user_id=admin_user.id,
            employee_id='EMP001',
            access_level='super_admin',
            phone='+1234567890'
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

def create_sample_specializations():
    """Create sample specializations for departments"""
    specializations_data = [
        # Cardiology
        {'name': 'Interventional Cardiology', 'dept_code': 'CARD'},
        {'name': 'Pediatric Cardiology', 'dept_code': 'CARD'},
        {'name': 'Cardiac Surgery', 'dept_code': 'CARD'},
        
        # Neurology
        {'name': 'Neurosurgery', 'dept_code': 'NEURO'},
        {'name': 'Pediatric Neurology', 'dept_code': 'NEURO'},
        {'name': 'Neuropsychology', 'dept_code': 'NEURO'},
        
        # Orthopedics
        {'name': 'Sports Medicine', 'dept_code': 'ORTHO'},
        {'name': 'Joint Replacement', 'dept_code': 'ORTHO'},
        {'name': 'Spine Surgery', 'dept_code': 'ORTHO'},
        
        # General Medicine
        {'name': 'Internal Medicine', 'dept_code': 'GENMED'},
        {'name': 'Family Medicine', 'dept_code': 'GENMED'},
    ]

    try:
        created_count = 0
        for spec_data in specializations_data:
            dept = Department.query.filter_by(code=spec_data['dept_code']).first()
            if dept:
                existing_spec = Specialization.query.filter_by(
                    name=spec_data['name'], 
                    department_id=dept.id
                ).first()
                
                if not existing_spec:
                    specialization = Specialization(
                        name=spec_data['name'],
                        department_id=dept.id,
                        description=f"{spec_data['name']} under {dept.name}"
                    )
                    db.session.add(specialization)
                    created_count += 1

        db.session.commit()
        print(f" {created_count} specializations created")
        
    except Exception as e:
        print(f" Error creating specializations: {str(e)}")
        db.session.rollback()
        raise

def reset_database():
    """Reset the entire database - USE WITH CAUTION"""
    db.drop_all()
    print("All tables dropped")
    init_database()

def print_database_structure():
    """Display information about our database structure and how tables connect"""
    print("\n" + "="*60)
    print("DATABASE STRUCTURE AND TABLE RELATIONSHIPS")
    print("="*60)
    
    # The main data types we store
    print("PRIMARY DATA TABLES:")
    print("   - Users (handles login and basic user info)")
    print("   - Admins (hospital management staff)")
    print("   - Departments (different medical departments)")
    print("   - Specializations (specific areas within departments)")
    print("   - Doctors (medical staff and their details)")
    print("   - Patients (people receiving medical care)")
    
    # The operational data we track
    print("\nOPERATIONAL DATA TABLES:")
    print("   - Appointments (scheduled meetings between patients and doctors)")
    print("   - Treatments (medical procedures and their details)")
    print("   - Medical Records (patient medical history)")
    print("   - Prescriptions (medication information)")
    print("   - Doctor Availability (when doctors are available)")
    print("   - Doctor Schedules (specific daily schedules)")
    
    # How the tables connect to each other
    print("\nHOW TABLES CONNECT:")
    print("   Each User can be an Admin, Doctor, or Patient")
    print("   Departments contain multiple Specializations")
    print("   Doctors belong to Departments and may have Specializations")
    print("   Appointments connect Patients with Doctors")
    print("   Treatments record what happened during Appointments")
    print("   Prescriptions detail medications from Treatments")
    print("="*60)

def get_database_stats():
    """Get comprehensive statistics about the database"""
    try:
        stats = {
            'total_users': User.query.count(),
            'total_admins': Admin.query.count(),
            'total_doctors': Doctor.query.count(),
            'total_patients': Patient.query.count(),
            'total_departments': Department.query.count(),
            'total_specializations': Specialization.query.count(),
            'total_appointments': Appointment.query.count(),
            'total_treatments': Treatment.query.count(),
            'total_medical_records': MedicalRecord.query.count(),
            'total_prescriptions': Prescription.query.count(),
            'active_doctors': Doctor.query.filter_by(is_available=True).count(),
            'active_patients': Patient.query.filter_by(is_active=True).count(),
        }
        
        # Appointment statistics
        appointment_stats = {
            'scheduled': Appointment.query.filter_by(status='Scheduled').count(),
            'completed': Appointment.query.filter_by(status='Completed').count(),
            'cancelled': Appointment.query.filter_by(status='Cancelled').count(),
        }
        
        stats.update(appointment_stats)
        return stats
        
    except Exception as e:
        print(f"Error getting database stats: {str(e)}")
        return {}

def backup_database(backup_file='hospital_backup.sql'):
    """Create a backup of the database"""
    try:
        conn = sqlite3.connect('hospital_management.db')
        with open(backup_file, 'w') as f:
            for line in conn.iterdump():
                f.write('%s\n' % line)
        conn.close()
        print(f"Database backed up to {backup_file}")
        return True
    except Exception as e:
        print(f"Backup failed: {str(e)}")
        return False

def check_db_connection():
    """Check if database connection is working"""
    try:
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        return True
    except Exception as e:
        print(f"Database connection failed: {str(e)}")
        return False
