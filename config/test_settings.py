"""Test-only settings.

Adds `tests.testapp`, which holds throwaway models used to exercise the PolyFactory
Django adapter. Keeping them out of `accounts_receivable` means the adapter is proven
without inventing application models or a migration we would later throw away.

`tests.testapp` ships no migrations package, so Django's test-database setup creates
its tables via `migrate --run-syncdb`.
"""

from config.settings import *  # noqa: F403
from config.settings import INSTALLED_APPS

INSTALLED_APPS = [*INSTALLED_APPS, "tests.testapp"]
