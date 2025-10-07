from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, index=True)  # can be admin, doctor, or patient
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f'<User {self.username}>'

class Admin(db.Model):
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    access_level = db.Column(db.String(20), default='super_admin')  # different permission levels
    phone = db.Column(db.String(15))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Connect back to the main user record
    user = db.relationship('User', backref=db.backref('admin_profile', uselist=False), lazy=True)

    def __repr__(self):
        return f'<Admin {self.user.username}>'

class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    code = db.Column(db.String(10), unique=True, nullable=False)  # e.g., CARD, NEURO, ORTHO
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    doctors = db.relationship('Doctor', backref='department', lazy=True, cascade='all, delete-orphan')
    specializations = db.relationship('Specialization', backref='department', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Department {self.name}>'

class Specialization(db.Model):
    __tablename__ = 'specializations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    doctors = db.relationship('Doctor', backref='specialization', lazy=True)

    def __repr__(self):
        return f'<Specialization {self.name}>'

class Doctor(db.Model):
    __tablename__ = 'doctors'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    specialization_id = db.Column(db.Integer, db.ForeignKey('specializations.id'), nullable=True)
    license_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(15))
    experience_years = db.Column(db.Integer, default=0)
    qualification = db.Column(db.String(200))
    consultation_fee = db.Column(db.Float, default=0.0)
    is_available = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('doctor_profile', uselist=False), lazy=True)
    appointments = db.relationship('Appointment', backref='doctor', lazy=True, cascade='all, delete-orphan')
    availability = db.relationship('DoctorAvailability', backref='doctor', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Doctor {self.user.username}>'

class Patient(db.Model):
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    patient_id = db.Column(db.String(20), unique=True, nullable=False, index=True)  # P001, P002, etc.
    phone = db.Column(db.String(15))
    address = db.Column(db.Text)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))  # Male, Female, Other
    blood_group = db.Column(db.String(5))  # A+, B-, O+, etc.
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(15))
    emergency_contact_relation = db.Column(db.String(50))
    medical_history = db.Column(db.Text)
    allergies = db.Column(db.Text)
    current_medications = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('patient_profile', uselist=False), lazy=True)
    appointments = db.relationship('Appointment', backref='patient', lazy=True, cascade='all, delete-orphan')

    @property
    def age(self):
        if self.date_of_birth:
            return (datetime.now().date() - self.date_of_birth).days // 365
        return None

    def __repr__(self):
        return f'<Patient {self.patient_id}>'

class DoctorAvailability(db.Model):
    __tablename__ = 'doctor_availability'

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_available = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint to prevent overlapping availability for same doctor and day
    __table_args__ = (db.UniqueConstraint('doctor_id', 'day_of_week', 'start_time', name='unique_doctor_availability'),)

    def __repr__(self):
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return f'<Availability {self.doctor.user.username} on {days[self.day_of_week]}>'

class DoctorSchedule(db.Model):
    __tablename__ = 'doctor_schedules'

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_available = db.Column(db.Boolean, default=True, nullable=False)
    notes = db.Column(db.Text)  # Special notes for this day
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    doctor = db.relationship('Doctor', backref='schedules', lazy=True)

    def __repr__(self):
        return f'<Schedule {self.doctor.user.username} on {self.date}>'

class Appointment(db.Model):
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.String(20), unique=True, nullable=False, index=True)  # APT001, APT002, etc.
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False, index=True)
    appointment_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='Scheduled', nullable=False)  # Scheduled, Confirmed, In-Progress, Completed, Cancelled, No-Show
    appointment_type = db.Column(db.String(30), default='Consultation')  # Consultation, Follow-up, Emergency, Check-up
    reason = db.Column(db.Text)
    notes = db.Column(db.Text)
    priority = db.Column(db.String(10), default='Normal')  # Low, Normal, High, Emergency
    estimated_duration = db.Column(db.Integer, default=30)  # in minutes
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    treatments = db.relationship('Treatment', backref='appointment', lazy=True, cascade='all, delete-orphan')

    # Unique constraint to prevent double booking
    __table_args__ = (db.UniqueConstraint('doctor_id', 'appointment_date', 'appointment_time', name='unique_appointment_slot'),)

    def __repr__(self):
        return f'<Appointment {self.appointment_id}>'

class Treatment(db.Model):
    __tablename__ = 'treatments'

    id = db.Column(db.Integer, primary_key=True)
    treatment_id = db.Column(db.String(20), unique=True, nullable=False, index=True)  # TRT001, TRT002, etc.
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)
    diagnosis = db.Column(db.Text, nullable=False)
    symptoms = db.Column(db.Text)
    prescription = db.Column(db.Text)
    treatment_plan = db.Column(db.Text)
    treatment_notes = db.Column(db.Text)
    follow_up_date = db.Column(db.Date)
    follow_up_instructions = db.Column(db.Text)
    treatment_cost = db.Column(db.Float, default=0.0)
    is_completed = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Treatment {self.treatment_id}>'

# Additional models for comprehensive hospital management

class MedicalRecord(db.Model):
    __tablename__ = 'medical_records'

    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    visit_date = db.Column(db.Date, nullable=False)
    chief_complaint = db.Column(db.Text)
    vital_signs = db.Column(db.Text)  # JSON or structured data
    examination_findings = db.Column(db.Text)
    lab_results = db.Column(db.Text)
    imaging_results = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    patient = db.relationship('Patient', backref='medical_records', lazy=True)
    doctor = db.relationship('Doctor', backref='medical_records', lazy=True)

    def __repr__(self):
        return f'<MedicalRecord {self.record_id}>'

class Prescription(db.Model):
    __tablename__ = 'prescriptions'

    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    treatment_id = db.Column(db.Integer, db.ForeignKey('treatments.id'), nullable=False)
    medication_name = db.Column(db.String(200), nullable=False)
    dosage = db.Column(db.String(100), nullable=False)
    frequency = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.String(100))
    instructions = db.Column(db.Text)
    quantity = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    treatment = db.relationship('Treatment', backref='prescriptions', lazy=True)

    def __repr__(self):
        return f'<Prescription {self.prescription_id}>'
