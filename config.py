import os
from datetime import timedelta

class Config:
    SECRET_KEY = 'temp'

    SQLALCHEMY_DATABASE_URI =  'sqlite:///hospital_management.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    DEBUG = True
    DEVELOPMENT = True


config = {
    'development': DevelopmentConfig,
}
