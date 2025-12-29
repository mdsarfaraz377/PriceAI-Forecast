
import os
from django.core.wsgi import get_wsgi_application

import sys
from pathlib import Path

# Add the project directory to sys.path
path = Path(__file__).resolve().parent.parent
if str(path) not in sys.path:
    sys.path.append(str(path))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'price_forecast.settings')

application = get_wsgi_application()
app = application
