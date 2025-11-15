from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, Doctor, Patient, Appointment, Treatment, DoctorAvailability, Department
from datetime import datetime, date, timedelta, time
from functools import wraps

bp = Blueprint('doctor', __name__)

def doctor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'doctor':
            flash('Access denied. Doctor privileges required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/dashboard')
@login_required
@doctor_required
def dashboard():
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    if not doctor:
        flash('Doctor profile not found.', 'error')
        return redirect(url_for('auth.logout'))

    # Get today's appointments
    today = date.today()
    today_appointments = Appointment.query.filter_by(
        doctor_id=doctor.id,
        appointment_date=today
    ).all()

    # Get upcoming appointments (next 7 days)
    end_date = today + timedelta(days=7)
    upcoming_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.appointment_date.between(today, end_date),
        Appointment.status.in_(['Scheduled', 'Confirmed'])
    ).order_by(Appointment.appointment_date, Appointment.appointment_time).all()

    # Get statistics
    total_patients = db.session.query(Patient).join(Appointment).filter(
        Appointment.doctor_id == doctor.id
    ).distinct().count()

    completed_appointments = Appointment.query.filter_by(
        doctor_id=doctor.id,
        status='Completed'
    ).count()

    pending_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.status.in_(['Scheduled', 'Confirmed'])
    ).count()

    return render_template('doctor/dashboard.html',
                         doctor=doctor,
                         today_appointments=today_appointments,
                         upcoming_appointments=upcoming_appointments,
                         total_patients=total_patients,
                         completed_appointments=completed_appointments,
                         pending_appointments=pending_appointments)

@bp.route('/appointments')
@login_required
@doctor_required
def appointments():
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    date_filter = request.args.get('date', '')
    status_filter = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)

    query = Appointment.query.filter_by(doctor_id=doctor.id)

    if date_filter:
        query = query.filter(Appointment.appointment_date == date_filter)

    if status_filter:
        query = query.filter(Appointment.status == status_filter)

    appointments = db.paginate(
        query.order_by(
            Appointment.appointment_date.desc(),
            Appointment.appointment_time.desc()
        ),
        page=page,
        per_page=15,
        error_out=False,
    )

    return render_template('doctor/appointments.html',
                         appointments=appointments,
                         date_filter=date_filter,
                         status_filter=status_filter)

@bp.route('/complete_appointment/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
@doctor_required
def complete_appointment(appointment_id):
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    appointment = db.first_or_404(
        Appointment.query.filter_by(id=appointment_id, doctor_id=doctor.id)
    )

    if request.method == 'POST':
        diagnosis = request.form.get('diagnosis')
        prescription = request.form.get('prescription')
        treatment_notes = request.form.get('treatment_notes')
        follow_up_date = request.form.get('follow_up_date')

        if not diagnosis:
            flash('Diagnosis is required', 'error')
            return render_template('doctor/complete_appointment.html', appointment=appointment)

        try:
            # Update appointment status
            appointment.status = 'Completed'
            appointment.updated_at = datetime.utcnow()

            # Generate treatment ID
            last_treatment = Treatment.query.order_by(Treatment.id.desc()).first()
            if last_treatment:
                last_id_num = int(last_treatment.treatment_id[3:])  # Extract number from TRT001
                new_treatment_id = f"TRT{last_id_num + 1:03d}"  # TRT002, TRT003, etc.
            else:
                new_treatment_id = "TRT001"  # First treatment

            # Create treatment record
            treatment = Treatment(
                treatment_id=new_treatment_id,
                appointment_id=appointment.id,
                diagnosis=diagnosis,
                prescription=prescription,
                treatment_notes=treatment_notes,
                follow_up_date=datetime.strptime(follow_up_date, '%Y-%m-%d').date() if follow_up_date else None
            )

            db.session.add(treatment)
            db.session.commit()

            flash('Appointment completed successfully!', 'success')
            return redirect(url_for('doctor.appointments'))

        except Exception as e:
            db.session.rollback()
            flash('Failed to complete appointment.', 'error')
            print(f"Complete appointment error: {str(e)}")

    return render_template('doctor/complete_appointment.html', appointment=appointment)

@bp.route('/cancel_appointment/<int:appointment_id>')
@login_required
@doctor_required
def cancel_appointment(appointment_id):
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    appointment = db.first_or_404(
        Appointment.query.filter_by(id=appointment_id, doctor_id=doctor.id)
    )

    try:
        appointment.status = 'Cancelled'
        appointment.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Appointment cancelled successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to cancel appointment.', 'error')

    return redirect(url_for('doctor.appointments'))

@bp.route('/patient_history/<int:patient_id>')
@login_required
@doctor_required
def patient_history(patient_id):
    patient = Patient.query.get_or_404(patient_id)

    # Get all completed appointments with treatments for this patient
    appointments_with_treatments = db.session.query(Appointment, Treatment).\
        outerjoin(Treatment, Appointment.id == Treatment.appointment_id).\
        filter(Appointment.patient_id == patient_id).\
        order_by(Appointment.appointment_date.desc()).all()

    return render_template('doctor/patient_history.html',
                         patient=patient,
                         appointments_with_treatments=appointments_with_treatments)

@bp.route('/availability')
@login_required
@doctor_required
def availability():
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()

    # Get current weekly availability pattern
    availability = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == doctor.id
    ).order_by(DoctorAvailability.day_of_week, DoctorAvailability.start_time).all()

    return render_template('doctor/availability.html',
                         doctor=doctor,
                         availability=availability)

@bp.route('/set_availability', methods=['POST'])
@login_required
@doctor_required
def set_availability():
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()

    day_of_week = request.form.get('day_of_week')  # 0=Monday, 6=Sunday
    start_time = request.form.get('start_time')
    end_time = request.form.get('end_time')
    is_available = request.form.get('is_available') == 'on'

    if not all([day_of_week, start_time, end_time]):
        flash('Please fill in all fields', 'error')
        return redirect(url_for('doctor.availability'))

    try:
        day_of_week = int(day_of_week)
        
        # Check if availability already exists for this day of week and time
        existing = DoctorAvailability.query.filter_by(
            doctor_id=doctor.id,
            day_of_week=day_of_week,
            start_time=datetime.strptime(start_time, '%H:%M').time()
        ).first()

        if existing:
            # Update existing availability
            existing.end_time = datetime.strptime(end_time, '%H:%M').time()
            existing.is_available = is_available
        else:
            # Create new availability
            availability = DoctorAvailability(
                doctor_id=doctor.id,
                day_of_week=day_of_week,
                start_time=datetime.strptime(start_time, '%H:%M').time(),
                end_time=datetime.strptime(end_time, '%H:%M').time(),
                is_available=is_available
            )
            db.session.add(availability)

        db.session.commit()
        flash('Weekly availability updated successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash('Failed to update availability.', 'error')
        print(f"Set availability error: {str(e)}")

    return redirect(url_for('doctor.availability'))

@bp.route('/profile')
@login_required
@doctor_required
def profile():
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    departments = Department.query.all()
    return render_template('doctor/profile.html', doctor=doctor, departments=departments)

@bp.route('/update_profile', methods=['POST'])
@login_required
@doctor_required
def update_profile():
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()

    try:
        # Update user email
        doctor.user.email = request.form.get('email')

        # Update doctor profile
        doctor.phone = request.form.get('phone')
        doctor.qualification = request.form.get('qualification')
        doctor.experience_years = int(request.form.get('experience_years', 0))
        doctor.consultation_fee = float(request.form.get('consultation_fee', 0))

        db.session.commit()
        flash('Profile updated successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash('Failed to update profile.', 'error')
        print(f"Update profile error: {str(e)}")

    return redirect(url_for('doctor.profile'))
