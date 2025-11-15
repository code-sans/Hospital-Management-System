from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from app import db, login_manager
from app.models import User, Patient
from datetime import datetime

bp = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Please fill in all fields', 'error')
            return render_template('login.html')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=True)
            flash(f'Welcome, {user.username}!')



            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'doctor':
                return redirect(url_for('doctor.dashboard'))
            elif user.role == 'patient':
                return redirect(url_for('patient.dashboard'))
        else:
            flash('Invalid username or password')

    return render_template('login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        date_of_birth = request.form.get('date_of_birth')
        gender = request.form.get('gender')
      
        phone = request.form.get('phone')
        address = request.form.get('address')
        
        blood_group = request.form.get('blood_group')
        emergency_contact = request.form.get('emergency_contact')

        # Validation
        if not all([first_name, last_name, username, email, password, confirm_password]):
            flash('Please fill in all required fields', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')

        if len(password) < 4:
            flash('Password should be at least 4 characters long', 'error')
            return render_template('register.html')

        if (
            User.query.filter_by(username=username).first() or
            User.query.filter_by(email=email).first() or
            Patient.query.filter_by(phone=phone).first()
        ):
            flash("Similar details already exist", "error")
            return render_template('register.html')


        try:
            # Create new user
            user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role='patient'  # Because Only patients will be registering themselves
            )
            user.set_password(password)
            db.session.add(user)
            db.session.flush() #  to get user.id

# Genrate patientID
            last_patient = Patient.query.order_by(Patient.id.desc()).first()
            if last_patient:
                last_id_num = int(last_patient.patient_id[1:])  # Extract number from P001
                new_patient_id = f"P{last_id_num + 1:02d}"  # P02, P03, etc.
            else:
                new_patient_id = "P01"  # First patient

            # Create patient profile
            patient = Patient(
                user_id=user.id,
                patient_id=new_patient_id,
                phone=phone,
                address=address,
                date_of_birth=datetime.strptime(date_of_birth, '%Y-%m-%d').date() if date_of_birth else None,
                gender=gender,
                blood_group=blood_group,
                emergency_contact_phone=emergency_contact  # Updated field name
            )
            db.session.add(patient)
            db.session.commit()

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            print(f"Registration error: {str(e)}")

    return render_template('register.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('auth.login'))

@bp.route('/dashboard')
@login_required
def dashboard():

    """dashboard based on user role"""
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif current_user.role == 'doctor':
        return redirect(url_for('doctor.dashboard'))
    elif current_user.role == 'patient':
        return redirect(url_for('patient.dashboard'))
    else:
        flash('Invalid user role', 'error')
        return redirect(url_for('auth.logout'))

@bp.route('/')
def index():
    """redirect to login if no authenticated"""
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))
    return redirect(url_for('auth.login'))
