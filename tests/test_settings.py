"""The toolchain and Django configuration are what we think they are."""

import sys

import django
from django.conf import settings


def test_running_on_the_pinned_python() -> None:
    """The venv is on the interpreter .tool-versions pins, not Homebrew's python3.

    Homebrew ships a 3.14.x that also satisfies requires-python, so uv can silently
    pick it if the asdf interpreter isn't passed explicitly.
    """
    with open(".tool-versions") as handle:
        pinned = next(line.split()[1] for line in handle if line.startswith("python "))

    actual = ".".join(str(part) for part in sys.version_info[:3])
    assert actual == pinned


def test_running_the_expected_django() -> None:
    assert django.get_version().startswith("6.1")


def test_database_is_sqlite() -> None:
    assert settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"


def test_expected_apps_are_installed() -> None:
    assert "accounts_receivable" in settings.INSTALLED_APPS


def test_auth_and_admin_are_deliberately_absent() -> None:
    """The source application is unauthenticated and has no admin."""
    assert "django.contrib.admin" not in settings.INSTALLED_APPS
    assert "django.contrib.auth" not in settings.INSTALLED_APPS


def test_timezone_matches_the_rails_source_app() -> None:
    assert settings.USE_TZ is True
    assert settings.TIME_ZONE == "UTC"
