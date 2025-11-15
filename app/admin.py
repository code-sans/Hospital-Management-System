from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from datetime import datetime
from functools import wraps
from app import db
from app.models import (
    User, Admin, Doctor, Patient, Department, Appointment, Treatment, DoctorAvailability
)

bp = Blueprint('admin', __name__)



def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not (current_user.is_authenticated and current_user.role == 'admin'):
            flash('Admin access required.', 'error')
            return redirect(url_for('auth.login'))
        return func(*args, **kwargs)
    return wrapper




@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    stats = {
        "doctors": Doctor.query.count(),
        "patients": Patient.query.count(),
        "appointments":Appointment.query.count(),
        "departments": Department.query.count(),
    }

    appt_status = {
        "booked": Appointment.query.filter(Appointment.status.in_(["Scheduled", "Confirmed"])).count(),
        "completed": Appointment.query.filter_by(status='Completed').count(),
        "cancelled": Appointment.query.filter_by(status='Cancelled').count(),
    }

    latest = (
        Appointment.query.options(
            joinedload(Appointment.patient).joinedload(Patient.user),
            joinedload(Appointment.doctor).joinedload(Doctor.user)
        )
        .order_by(Appointment.created_at.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "admin/dashboard.html",stats=stats,appt_status=appt_status,recent=latest
    )



@bp.route('/manage_doctors')
@login_required
@admin_required
def manage_doctors():
    keyword = request.args.get("search", "")
    page_no = request.args.get("page", 1, type=int)

    query = (
        Doctor.query.options(joinedload(Doctor.user), joinedload(Doctor.department))
        .join(User)
        .join(Department)
    )

    if keyword:
        key = f"%{keyword}%"
        query = query.filter(
            db.or_(
                User.username.ilike(key),
                User.email.ilike(key),
                Department.name.ilike(key),
                Doctor.license_number.ilike(key)
            )
        )

    doctors = db.paginate(query.order_by(Doctor.id.desc()), page=page_no, per_page=10, error_out=False)

    return render_template(
        "admin/manage_doctors.html",
        doctors=doctors,
        departments=Department.query.all(),
        search=keyword
    )


@bp.route('/add_doctor', methods=['POST'])
@login_required
@admin_required
def add_doctor():
    form = request.form

    required = ["username", "email", "password", "first_name", "last_name", "department_id", "license_number"]
    if not all(form.get(field) for field in required):
        flash("Please complete all required fields.", "error")
        return redirect(url_for("admin.manage_doctors"))

    if User.query.filter_by(username=form["username"]).first():
        flash("This username is taken.", "error")
        return redirect(url_for("admin.manage_doctors"))

    if User.query.filter_by(email=form["email"]).first():
        flash("Email already exists.", "error")
        return redirect(url_for("admin.manage_doctors"))

    if Doctor.query.filter_by(license_number=form["license_number"]).first():
        flash("License number must be unique.", "error")
        return redirect(url_for("admin.manage_doctors"))

    try:
        user = User(
            username=form["username"],
            email=form["email"],
            first_name=form["first_name"],
            last_name=form["last_name"],
            role="doctor",
        )
        user.set_password(form["password"])
        db.session.add(user)
        db.session.flush()

        doctor = Doctor(
            user_id=user.id,
            department_id=form["department_id"],
            license_number=form["license_number"],
            phone=form.get("phone"),
            experience_years=int(form.get("experience_years") or 0),
            qualification=form.get("qualification"),
            consultation_fee=float(form.get("consultation_fee") or 0),
        )
        db.session.add(doctor)
        db.session.commit()

        flash("Doctor added successfully.", "success")

    except Exception as err:
        db.session.rollback()
        print("Error adding doctor:", err)
        flash("Could not add doctor. Try again.", "error")

    return redirect(url_for("admin.manage_doctors"))


@bp.route('/update_doctor/<int:doctor_id>', methods=['POST'])
@login_required
@admin_required
def update_doctor(doctor_id):
    doctor = db.get_or_404(Doctor, doctor_id)
    form = request.form

    try:
        doctor.user.email = form.get("email")
        doctor.department_id = form.get("department_id")
        doctor.phone = form.get("phone")
        doctor.experience_years = int(form.get("experience_years", 0))
        doctor.qualification = form.get("qualification")
        doctor.consultation_fee = float(form.get("consultation_fee", 0))

        db.session.commit()
        flash("Doctor details updated.", "success")

    except Exception as err:
        db.session.rollback()
        print("Update error:", err)
        flash("Unable to update doctor.", "error")

    return redirect(url_for("admin.manage_doctors"))


@bp.route('/deactivate_doctor/<int:doctor_id>')
@login_required
@admin_required
def deactivate_doctor(doctor_id):
    doctor = db.get_or_404(Doctor, doctor_id)
    try:
        doctor.user.is_active = False
        db.session.commit()
        flash("Doctor deactivated.", "success")
    except Exception as err:
        db.session.rollback()
        print("Deactivate doctor failed:", err)
        flash("Could not deactivate doctor.", "error")

    return redirect(url_for("admin.manage_doctors"))



@bp.route('/manage_patients')
@login_required
@admin_required
def manage_patients():
    keyword = request.args.get("search", "")
    page_no = request.args.get("page", 1, type=int)

    query = Patient.query.options(joinedload(Patient.user)).join(User)

    if keyword:
        key = f"%{keyword}%"
        query = query.filter(
            db.or_(
                User.username.ilike(key),
                User.email.ilike(key),
                Patient.phone.ilike(key),
            )
        )

    patients = db.paginate(query.order_by(Patient.id.desc()), page=page_no, per_page=10, error_out=False)

    return render_template("admin/manage_patients.html", patients=patients, search=keyword)


@bp.route('/deactivate_patient/<int:patient_id>')
@login_required
@admin_required
def deactivate_patient(patient_id):
    pat = db.get_or_404(Patient, patient_id)
    try:
        pat.user.is_active = False
        db.session.commit()
        flash("Patient account disabled.", "success")
    except Exception as err:
        db.session.rollback()
        print("Deactivate patient error:", err)
        flash("Could not deactivate patient.", "error")

    return redirect(url_for("admin.manage_patients"))



@bp.route('/view_appointments')
@login_required
@admin_required
def view_appointments():
    search = request.args.get("search", "")
    status = request.args.get("status", "")
    filter_date = request.args.get("date", "")
    page_no = request.args.get("page", 1, type=int)

    query = (
        Appointment.query.options(
            joinedload(Appointment.patient).joinedload(Patient.user),
            joinedload(Appointment.doctor).joinedload(Doctor.user)
        )
        .join(Patient)
        .join(Doctor)
    )

    if search:
        query = query.join(User, Patient.user_id == User.id).filter(
            User.username.ilike(f"%{search}%")
        )

    if status:
        query = query.filter(Appointment.status == status)

    if filter_date:
        query = query.filter(Appointment.appointment_date == filter_date)

    appointments = db.paginate(
        query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()),
        page=page_no,
        per_page=15,
        error_out=False
    )

    return render_template(
        "admin/view_appointments.html",
        appointments=appointments,
        search=search,
        status_filter=status,
        date_filter=filter_date
    )

@bp.route('/patient_history/<int:patient_id>')
@login_required
@admin_required
def patient_history(patient_id):
    patient = Patient.query.get_or_404(patient_id)

    history = (
        db.session.query(Appointment, Treatment, Doctor, User)
        .join(Treatment, Treatment.appointment_id == Appointment.id)  # must have treatment
        .join(Doctor, Doctor.id == Appointment.doctor_id)
        .join(User, User.id == Doctor.user_id)
        .filter(
            Appointment.patient_id == patient_id,
            Appointment.status == 'Completed'
        )
        .order_by(Appointment.appointment_date.desc())
        .all()
    )

    return render_template(
        "admin/patient_history.html",
        patient=patient,
        history=history
    )


@bp.route('/cancel_appointment/<int:appointment_id>')
@login_required
@admin_required
def cancel_appointment(appointment_id):
    appt = db.get_or_404(Appointment, appointment_id)
    try:
        appt.status = "Cancelled"
        appt.updated_at = datetime.utcnow()
        db.session.commit()
        flash("Appointment cancelled.", "success")
    except Exception as err:
        db.session.rollback()
        print("Cancel appt error:", err)
        flash("Unable to cancel appointment.", "error")

    return redirect(url_for("admin.view_appointments"))
