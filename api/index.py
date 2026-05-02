import os
import sys

# Add your project directory to the Python path
# Assuming your Django project is in the 'second' directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'second')))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'second.settings')

import django
django.setup()

from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

# Get the Django WSGI application
application = get_wsgi_application()

# Wrap the Django application with WhiteNoise for static files
# This is important for serving static files in a serverless environment
application = WhiteNoise(application, root=os.path.join(os.path.dirname(__file__), 'staticfiles'))
# If you have other static files not collected by collectstatic, add them here
# application.add_files(os.path.join(os.path.dirname(__file__), 'static'), prefix='static/')
