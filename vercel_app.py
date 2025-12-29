
import os
import sys

# Get the directory where this file resides
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# The Django 'price_forecast' directory (with manage.py and the inner price_forecast folder)
PROJECT_DIR = os.path.join(BASE_DIR, 'price_forecast')

# Add PROJECT_DIR to path so we can import 'price_forecast.wsgi'
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

# Also add Root to path just in case
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'price_forecast.settings')

# Import the application
from django.core.wsgi import get_wsgi_application
app = get_wsgi_application()
