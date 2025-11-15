from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, Doctor, Patient, Appointment, Treatment, DoctorAvailability, Department
from datetime import datetime, date, timedelta, time
from functools import wraps

bp = Blueprint('patient', __name__)

def patient_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'patient':
            flash('Access denied. Patient privileges required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/dashboard')
@login_required
@patient_required
def dashboard():
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    if not patient:
        flash('Patient profile not found.', 'error')
        return redirect(url_for('auth.logout'))

    # Get departments
    departments = Department.query.all()

    # Get upcoming appointments
    today = date.today()
    upcoming_appointments = Appointment.query.filter(
        Appointment.patient_id == patient.id,
        Appointment.appointment_date >= today,
        Appointment.status.in_(['Scheduled', 'Confirmed'])
    ).order_by(Appointment.appointment_date, Appointment.appointment_time).limit(5).all()

    # Get recent appointments
    recent_appointments = Appointment.query.filter_by(
        patient_id=patient.id
    ).order_by(Appointment.appointment_date.desc()).limit(5).all()

    # Get statistics
    total_appointments = Appointment.query.filter_by(patient_id=patient.id).count()
    completed_appointments = Appointment.query.filter_by(
        patient_id=patient.id,
        status='Completed'
    ).count()

    return render_template('patient/dashboard.html',
                         patient=patient,
                         departments=departments,
                         upcoming_appointments=upcoming_appointments,
                         recent_appointments=recent_appointments,
                         total_appointments=total_appointments,
                         completed_appointments=completed_appointments)

@bp.route('/doctors')
@login_required
@patient_required
def search_doctors():
    search = request.args.get('search', '')
    department_id = request.args.get('department', '')
    page = request.args.get('page', 1, type=int)

    # Return Doctor objects and filter via joins; relationships used in template
    query = Doctor.query.\
        join(User, Doctor.user_id == User.id).\
        join(Department, Doctor.department_id == Department.id).\
        filter(User.is_active == True)

    if search:
        query = query.filter(
            db.or_(
                User.username.contains(search),
                Department.name.contains(search),
                Doctor.qualification.contains(search)
            )
        )

    if department_id:
        query = query.filter(Doctor.department_id == department_id)

    doctors = db.paginate(query, page=page, per_page=10, error_out=False)
    departments = Department.query.all()

    return render_template('patient/search_doctors.html',
                         doctors=doctors,
                         departments=departments,
                         search=search,
                         selected_department=department_id)

@bp.route('/book_appointment/<int:doctor_id>')
@login_required
@patient_required
def book_appointment(doctor_id):
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    doctor = Doctor.query.get_or_404(doctor_id)

    # Get doctor's weekly availability pattern
    today = date.today()
    end_date = today + timedelta(days=7)

    # Get doctor's general availability by day of week
    weekly_availability = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == doctor_id,
        DoctorAvailability.is_available == True
    ).all()

    availability = []
    for i in range(7):
        check_date = today + timedelta(days=i)
        day_of_week = check_date.weekday()  # 0=Monday, 6=Sunday
        
        day_availability = [av for av in weekly_availability if av.day_of_week == day_of_week]
        for av in day_availability:
            availability.append({
                'date': check_date,
                'start_time': av.start_time,
                'end_time': av.end_time,
                'day_of_week': day_of_week
            })

    existing_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.appointment_date.between(today, end_date),
        Appointment.status.in_(['Scheduled', 'Confirmed', 'In-Progress'])
    ).all()

    return render_template('patient/book_appointment.html',
                         doctor=doctor,
                         patient=patient,
                         availability=availability,
                         existing_appointments=existing_appointments)


@bp.route('/confirm_appointment', methods=['POST'])
@login_required
@patient_required
def confirm_appointment():
    patient = Patient.query.filter_by(user_id=current_user.id).first()

    doctor_id = request.form.get('doctor_id')
    appointment_date_str = request.form.get('appointment_date')
    appointment_time_str = request.form.get('appointment_time')
    reason = request.form.get('reason', '')

    if not all([doctor_id, appointment_date_str, appointment_time_str]):
        flash('Missing required fields.', 'error')
        return redirect(url_for('patient.book_appointment', doctor_id=doctor_id))

    try:
        appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
        appointment_time = datetime.strptime(appointment_time_str, '%H:%M').time()
    except ValueError:
        flash('Invalid date/time format.', 'error')
        return redirect(url_for('patient.book_appointment', doctor_id=doctor_id))

    # Exclude Cancelled appointments from conflict
    conflict = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.appointment_date == appointment_date,
        Appointment.appointment_time == appointment_time,
        Appointment.status.in_(['Scheduled', 'Confirmed', 'In-Progress'])
    ).first()

    if conflict:
        flash('This time slot is already booked.', 'error')
        return redirect(url_for('patient.book_appointment', doctor_id=doctor_id))

    # Generate ID
    last = Appointment.query.order_by(Appointment.id.desc()).first()
    new_id = f"APT{(int(last.appointment_id[3:]) + 1):03d}" if last else "APT001"

    # Create appointment
    appt = Appointment(
        appointment_id=new_id,
        patient_id=patient.id,
        doctor_id=doctor_id,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        status='Scheduled',
        appointment_type='Consultation',
        reason=reason,
        priority='Normal',
        estimated_duration=30
    )
    db.session.add(appt)
    db.session.commit()

    flash('Appointment booked successfully!', 'success')
    return redirect(url_for('patient.appointments'))


@bp.route('/appointments')
@login_required
@patient_required
def appointments():
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    status_filter = request.args.get('status', '').strip()
    page = request.args.get('page', 1, type=int)

    query = Appointment.query.filter_by(patient_id=patient.id)

    if not status_filter:
        query = query.filter(Appointment.status != 'Cancelled')
    else:
        query = query.filter(Appointment.status == status_filter)

    appointments = db.paginate(
        query.order_by(
            Appointment.appointment_date.desc(),
            Appointment.appointment_time.desc()
        ),
        page=page,
        per_page=10,
        error_out=False,
    )

    return render_template(
        'patient/appointments.html',
        appointments=appointments,
        status_filter=status_filter or 'active'  
    )

@bp.route('/cancel_appointment/<int:appointment_id>')
@login_required
@patient_required
def cancel_appointment(appointment_id):
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    appointment = Appointment.query.filter_by(
        id=appointment_id,
        patient_id=patient.id
    ).first_or_404()

    if appointment.status not in ['Scheduled', 'Confirmed']:
        flash('Only scheduled or confirmed appointments can be cancelled.', 'error')
        return redirect(url_for('patient.appointments'))

    appointment_datetime = datetime.combine(appointment.appointment_date, appointment.appointment_time)
    if appointment_datetime - datetime.now() < timedelta(hours=24):
        flash('Appointments can only be cancelled at least 24 hours in advance.', 'warning')
        return redirect(url_for('patient.appointments'))

    try:
        appointment.status = 'Cancelled'
        appointment.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Appointment cancelled successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to cancel appointment.', 'error')

    return redirect(url_for('patient.appointments'))

@bp.route('/appointment_history')
@login_required
@patient_required
def appointment_history():
    patient = Patient.query.filter_by(user_id=current_user.id).first()

    # Get all appointments with treatments
    appointments_with_treatments = db.session.query(Appointment, Treatment).\
        outerjoin(Treatment, Appointment.id == Treatment.appointment_id).\
        filter(Appointment.patient_id == patient.id).\
        order_by(Appointment.appointment_date.desc()).all()

    return render_template('patient/appointment_history.html',
                         patient=patient,
                         appointments_with_treatments=appointments_with_treatments)

@bp.route('/profile')
@login_required
@patient_required
def profile():
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    return render_template('patient/profile.html', patient=patient)

@bp.route('/update_profile', methods=['POST'])
@login_required
@patient_required
def update_profile():
    patient = Patient.query.filter_by(user_id=current_user.id).first()

    try:
        # Update user email
        patient.user.email = request.form.get('email')

        # Update patient profile
        patient.phone = request.form.get('phone')
        patient.address = request.form.get('address')
        patient.emergency_contact = request.form.get('emergency_contact')
        patient.blood_group = request.form.get('blood_group')
        patient.medical_history = request.form.get('medical_history')

        date_of_birth = request.form.get('date_of_birth')
        if date_of_birth:
            patient.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()

        db.session.commit()
        flash('Profile updated successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash('Failed to update profile.', 'error')
        print(f"Update profile error: {str(e)}")

    return redirect(url_for('patient.profile'))
