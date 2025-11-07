from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, Admin, Doctor, Patient, Department, Specialization, Appointment, Treatment, DoctorAvailability
from datetime import datetime, date, timedelta
from functools import wraps
from sqlalchemy.orm import joinedload

bp = Blueprint('admin', __name__)

# ------------------------------------------------------------

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


# ------------------------------------------------------------

@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard showing key statistics."""
    total_doctors = Doctor.query.count()
    total_patients = Patient.query.count()
    total_appointments = Appointment.query.count()
    total_departments = Department.query.count()

    # Appointment breakdown
    booked_appointments = Appointment.query.filter(Appointment.status.in_(['Scheduled', 'Confirmed'])).count()
    completed_appointments = Appointment.query.filter_by(status='Completed').count()
    cancelled_appointments = Appointment.query.filter_by(status='Cancelled').count()

    # Recent 10 appointments
    recent_appointments = (
        Appointment.query.options(
            joinedload(Appointment.patient).joinedload(Patient.user),
            joinedload(Appointment.doctor).joinedload(Doctor.user),
        )
        .order_by(Appointment.created_at.desc())
        .limit(10)
        .all()
    )

    return render_template(
        'admin/dashboard.html',
        total_doctors=total_doctors,
        total_patients=total_patients,
        total_appointments=total_appointments,
        total_departments=total_departments,
        booked_appointments=booked_appointments,
        completed_appointments=completed_appointments,
        cancelled_appointments=cancelled_appointments,
        recent_appointments=recent_appointments,
    )


# ------------------------------------------------------------

@bp.route('/manage_doctors')
@login_required
@admin_required
def manage_doctors():
    """Admin view to manage all doctors."""
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)

    query = (
        Doctor.query.options(joinedload(Doctor.user), joinedload(Doctor.department))
        .join(User)
        .join(Department)
    )

    if search:
        query = query.filter(
            db.or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                Department.name.ilike(f"%{search}%"),
                Doctor.license_number.ilike(f"%{search}%")
            )
        )

    doctors = db.paginate(query.order_by(Doctor.id.desc()), page=page, per_page=10, error_out=False)
    departments = Department.query.all()

    return render_template(
        'admin/manage_doctors.html',
        doctors=doctors,
        departments=departments,
        search=search
    )


@bp.route('/add_doctor', methods=['POST'])
@login_required
@admin_required
def add_doctor():
    """Add a new doctor record."""
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    department_id = request.form.get('department_id')
    license_number = request.form.get('license_number')
    phone = request.form.get('phone')
    experience_years = request.form.get('experience_years')
    qualification = request.form.get('qualification')
    consultation_fee = request.form.get('consultation_fee')

    if not all([username, email, password, first_name, last_name, department_id, license_number]):
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('admin.manage_doctors'))

    if User.query.filter_by(username=username).first():
        flash('Username already exists.', 'error')
        return redirect(url_for('admin.manage_doctors'))
    if User.query.filter_by(email=email).first():
        flash('Email already registered.', 'error')
        return redirect(url_for('admin.manage_doctors'))
    if Doctor.query.filter_by(license_number=license_number).first():
        flash('License number already exists.', 'error')
        return redirect(url_for('admin.manage_doctors'))

    try:
        # Create user record
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role='doctor'
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # flush to get user.id

        # Create doctor profile
        doctor = Doctor(
            user_id=user.id,
            department_id=department_id,
            license_number=license_number,
            phone=phone,
            experience_years=int(experience_years or 0),
            qualification=qualification,
            consultation_fee=float(consultation_fee or 0.0)
        )
        db.session.add(doctor)
        db.session.commit()
        flash(f'Doctor {username} added successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash('Failed to add doctor. Please try again.', 'error')
        print(f"[ERROR] Add doctor: {str(e)}")

    return redirect(url_for('admin.manage_doctors'))


@bp.route('/update_doctor/<int:doctor_id>', methods=['POST'])
@login_required
@admin_required
def update_doctor(doctor_id):
    """Update doctor details."""
    doctor = db.get_or_404(Doctor, doctor_id)
    try:
        doctor.user.email = request.form.get('email')
        doctor.department_id = request.form.get('department_id')
        doctor.phone = request.form.get('phone')
        doctor.experience_years = int(request.form.get('experience_years', 0))
        doctor.qualification = request.form.get('qualification')
        doctor.consultation_fee = float(request.form.get('consultation_fee', 0))
        db.session.commit()
        flash('Doctor information updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to update doctor information.', 'error')
        print(f"[ERROR] Update doctor: {str(e)}")

    return redirect(url_for('admin.manage_doctors'))


@bp.route('/deactivate_doctor/<int:doctor_id>')
@login_required
@admin_required
def deactivate_doctor(doctor_id):
    """Deactivate doctor account."""
    doctor = db.get_or_404(Doctor, doctor_id)
    try:
        doctor.user.is_active = False
        db.session.commit()
        flash(f'Doctor {doctor.user.username} deactivated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to deactivate doctor.', 'error')
        print(f"[ERROR] Deactivate doctor: {str(e)}")

    return redirect(url_for('admin.manage_doctors'))


# ------------------------------------------------------------
@bp.route('/manage_patients')
@login_required
@admin_required
def manage_patients():
    """Admin view to manage patients."""
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)

    query = Patient.query.options(joinedload(Patient.user)).join(User)
    if search:
        query = query.filter(
            db.or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                Patient.phone.ilike(f"%{search}%")
            )
        )

    patients = db.paginate(query.order_by(Patient.id.desc()), page=page, per_page=10, error_out=False)
    return render_template('admin/manage_patients.html', patients=patients, search=search)


@bp.route('/deactivate_patient/<int:patient_id>')
@login_required
@admin_required
def deactivate_patient(patient_id):
    """Deactivate patient account."""
    patient = db.get_or_404(Patient, patient_id)
    try:
        patient.user.is_active = False
        db.session.commit()
        flash(f'Patient {patient.user.username} deactivated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to deactivate patient.', 'error')
        print(f"[ERROR] Deactivate patient: {str(e)}")

    return redirect(url_for('admin.manage_patients'))


# ------------------------------------------------------------
@bp.route('/view_appointments')
@login_required
@admin_required
def view_appointments():
    """Admin view of all appointments."""
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    date_filter = request.args.get('date', '')
    page = request.args.get('page', 1, type=int)

    query = (
        Appointment.query.options(
            joinedload(Appointment.patient).joinedload(Patient.user),
            joinedload(Appointment.doctor).joinedload(Doctor.user),
        )
        .join(Patient)
        .join(Doctor)
    )

    if search:
        query = query.join(User, Patient.user_id == User.id).filter(User.username.ilike(f"%{search}%"))
    if status_filter:
        query = query.filter(Appointment.status == status_filter)
    if date_filter:
        query = query.filter(Appointment.appointment_date == date_filter)

    appointments = db.paginate(
        query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()),
        page=page,
        per_page=15,
        error_out=False,
    )

    return render_template(
        'admin/view_appointments.html',
        appointments=appointments,
        search=search,
        status_filter=status_filter,
        date_filter=date_filter
    )


@bp.route('/cancel_appointment/<int:appointment_id>')
@login_required
@admin_required
def cancel_appointment(appointment_id):
    """Cancel an appointment."""
    appointment = db.get_or_404(Appointment, appointment_id)
    try:
        appointment.status = 'Cancelled'
        appointment.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Appointment cancelled successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to cancel appointment.', 'error')
        print(f"[ERROR] Cancel appointment: {str(e)}")

    return redirect(url_for('admin.view_appointments'))
