"""Django accuracy fixture: env + MIDDLEWARE list."""
import os

SECRET_KEY = os.environ["DJANGO_SECRET"]

MIDDLEWARE = [
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "corsheaders.middleware.CorsMiddleware",
]
