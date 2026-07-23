"""
AI Fit Pro Gateway Configuration
Environment-based configuration for different deployment scenarios
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

class BaseConfig:
    """Base configuration - common across all environments"""
    
    # Application
    APP_NAME = 'AI Fit Pro'
    VERSION = '2.0.0'
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Session
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    # File Upload
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    UPLOAD_FOLDER = BASE_DIR / 'data' / 'uploads'
    PROCESSED_FOLDER = BASE_DIR / 'data' / 'processed'
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov'}
    
    # API URLs (for microservices communication)
    NUTRI_AI_SERVICE_URL = os.environ.get('NUTRI_AI_SERVICE_URL', 'http://localhost:5001')
    MUSCLE_AI_SERVICE_URL = os.environ.get('MUSCLE_AI_SERVICE_URL', 'http://localhost:5002')
    
    # Database (for future use)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = BASE_DIR / 'logs' / 'fitlife.log'
    
    # CORS
    CORS_ORIGINS = ['*']
    
    # Rate Limiting (requests per minute)
    RATE_LIMIT = 60
    
    # Caching
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes


class DevelopmentConfig(BaseConfig):
    """Development environment configuration"""
    
    DEBUG = True
    TESTING = False
    
    # More verbose logging
    LOG_LEVEL = 'DEBUG'
    
    # Disable rate limiting in development
    RATE_LIMIT = None
    
    # Development database
    DATABASE_URL = os.environ.get('DEV_DATABASE_URL', 'sqlite:///dev_fitlife.db')


class ProductionConfig(BaseConfig):
    """Production environment configuration"""
    
    DEBUG = False
    TESTING = False
    
    # Production values are validated when selecting the config (see get_config),
    # so importing this module in development doesn't fail.
    SECRET_KEY = os.environ.get('SECRET_KEY')

    # Production database (optional for now; validate in get_config when required)
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    # Stricter CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',')
    
    # Production logging
    LOG_LEVEL = 'WARNING'
    
    # Enable caching
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')


class TestingConfig(BaseConfig):
    """Testing environment configuration"""
    
    DEBUG = True
    TESTING = True
    
    # Testing database
    DATABASE_URL = 'sqlite:///:memory:'
    
    # Disable rate limiting in tests
    RATE_LIMIT = None
    
    # Use file system for uploads during testing
    UPLOAD_FOLDER = BASE_DIR / 'tests' / 'uploads'
    PROCESSED_FOLDER = BASE_DIR / 'tests' / 'processed'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(env='development'):
    """Get configuration based on environment"""
    cfg = config.get(env, config['default'])
    if cfg is ProductionConfig:
        if not os.environ.get('SECRET_KEY'):
            raise ValueError("SECRET_KEY environment variable must be set in production")
        # If/when DB is required for production, uncomment this validation.
        # if not os.environ.get('DATABASE_URL'):
        #     raise ValueError("DATABASE_URL environment variable must be set in production")
    return cfg
