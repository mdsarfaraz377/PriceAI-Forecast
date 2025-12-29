
import os
import sys
from pathlib import Path

# Add the project folder to the path
current_dir = Path(__file__).resolve().parent
project_dir = current_dir / "price_forecast"
if str(project_dir) not in sys.path:
    sys.path.append(str(project_dir))

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'price_forecast.settings')

application = get_wsgi_application()
app = application
