# Django-ს სტანდარტული WSGI შესასვლელი. ჰოსტინგის სერვერი აქედან იღებს აპლიკაციას.
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_wsgi_application()
