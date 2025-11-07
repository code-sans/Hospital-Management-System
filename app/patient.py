from flask import Blueprint
bp = Blueprint('patient', __name__)

from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps

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
    return render_template('patient/dashboard.html')
