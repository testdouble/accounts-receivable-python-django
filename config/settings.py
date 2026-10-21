"""Django settings for the Accounts Receivable foundation skeleton.

A single settings module on purpose: this app has no deployment story yet, and the
sibling ports (Rails, Node, .NET) all run from one local configuration. Test-only
overrides live in `config.test_settings`.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Local-only development app. There is no deployment, so there is no secret to protect
# and nothing is gained by reading this from the environment.
SECRET_KEY = "django-insecure-foundation-skeleton-not-for-deployment"
DEBUG = True
ALLOWED_HOSTS: list[str] = ["localhost", "127.0.0.1", "[::1]"]

# The source application is entirely unauthenticated and has no admin, so
# `admin`, `auth`, and `sessions` are deliberately omitted. Re-add them if we
# later want the Django admin for data entry.
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts_receivable",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Cookie-backed, because `django.contrib.sessions` is not installed.
MESSAGE_STORAGE = "django.contrib.messages.storage.cookie.CookieStorage"

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "dev.sqlite3",
    }
}

LANGUAGE_CODE = "en-us"
# UTC to match the Rails source app's default, so date arithmetic agrees between ports.
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
