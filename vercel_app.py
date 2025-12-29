import os
import sys

# Get the directory where this file sits (the project root)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# The Django 'price_forecast' directory (with manage.py)
PROJECT_DIR = os.path.join(BASE_DIR, 'price_forecast')

# Add it to sys.path
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

# Set the settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'price_forecast.settings')

# Import the WSGI app from the inner price_forecast folder
try:
    from price_forecast.wsgi import app
except ImportError:
    # Backup import if the above fails
    from price_forecast.price_forecast.wsgi import app

# Vercel looks for 'app' or 'application'
application = app
