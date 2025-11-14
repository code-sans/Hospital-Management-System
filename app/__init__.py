from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config

db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_name='default'):
    app = Flask(
        __name__,
        static_folder='../static',
        template_folder='../templates',
    )
    app.config.from_object(config[config_name])

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Log in to access this page.'
    login_manager.login_message_category = 'info'

    from . import models
    from .auth import bp as auth_bp
    from .admin import bp as admin_bp
    from .doctor import bp as doctor_bp
    from .patient import bp as patient_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(doctor_bp, url_prefix='/doctor')
    app.register_blueprint(patient_bp, url_prefix='/patient')

    return app
