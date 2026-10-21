# Accounts Receivable

Welcome to the Accounts Receivable system! This system is responsible for creating,
sending, and tracking invoices sent to clients so we can be paid for our products and
services.

> **Status: foundation skeleton.** The toolchain and every library in the stack are set
> up and proven by the test suite, but no domain features are built yet. Clients,
> products, services, invoices, and line items arrive in the next pass.

## Getting started

This project is a [Django](https://www.djangoproject.com/) application written in
Python. It uses [SQLite](https://sqlite.org/) for the database and the Django ORM,
with [Django Ninja](https://django-ninja.dev/) and [Pydantic](https://docs.pydantic.dev/)
for the JSON API. Python versions are managed with [asdf](https://asdf-vm.com/) and
dependencies with [uv](https://docs.astral.sh/uv/).

### Prerequisites

Before you get started, be sure to:

* Have a recent version of git installed (e.g. `brew install git` on a Mac)
* Have asdf installed, with the python plugin (`asdf plugin add python`)
* Have uv 0.13 or newer installed (e.g. `brew install uv` on a Mac)

### Initial setup

    $ ./setup.sh

That installs the pinned Python, creates the virtualenv, installs dependencies, and
applies migrations. If you would rather run the steps yourself:

1. Install the Python version this project pins:

        $ asdf install

2. Create the virtualenv on that interpreter:

        $ uv venv --python "$(asdf which python)"

   (The interpreter is passed explicitly on purpose. uv does not read
   `.tool-versions`, and a Homebrew Python on your `PATH` may also satisfy this
   project's `requires-python` — so without it you can silently get the wrong one.)

3. Install dependencies:

        $ uv sync

4. Apply migrations:

        $ uv run python manage.py migrate

Then start the server:

    $ ./run.sh

And you should be able to see the app in a browser:
[http://localhost:8000](http://localhost:8000)

The JSON API is mounted at `/api`, with interactive docs at
[http://localhost:8000/api/docs](http://localhost:8000/api/docs).

> The API is unauthenticated and CSRF-exempt, which is Django Ninja's default. That
> matches the source application, which has no users at all.

### Tests

To run the suite of tests:

    $ ./test.sh

To run a single test file:

    $ ./test.sh tests/test_django_factory.py

To check linting and formatting:

    $ ./lint.sh

## Notes

### The stack

| Layer | Tool | Rails equivalent |
| --- | --- | --- |
| Language | Python | Ruby |
| Version manager | asdf | asdf / rbenv |
| Project + dependencies | uv | Bundler |
| Web framework | Django | Rails |
| ORM | Django ORM | ActiveRecord |
| Migrations | Django Migrations | Rails migrations |
| Views / templates | Django Template Language | ERB |
| JSON API | Django Ninja + Pydantic | — |
| Test runner | pytest | RSpec |
| Django test integration | pytest-django | rspec-rails |
| Mocking | pytest-mock | rspec-mocks |
| Test data factories | PolyFactory | FactoryBot |
| Lint + format | ruff | standardrb |

### Python version

`.tool-versions` is the single source of truth for the Python version — there is
deliberately no `.python-version`, which uv would honour and asdf would ignore.

This project currently pins **Python 3.14.9** rather than 3.15. Python 3.15 shipped on
2026-10-09, but Django's support for it lands in **Django 6.1.3, expected 2026-11-03**;
pytest-django and django-ninja have not published 3.15 support either. `requires-python`
in `pyproject.toml` already allows 3.15, so the bump is a one-line change to
`.tool-versions` once those land.

### Test data factories

PolyFactory has no Django ORM support — it covers Pydantic, attrs, msgspec and
SQLAlchemy, but ships no `DjangoModelFactory`. `tests/factories/base.py` is a small
adapter built on PolyFactory's `BaseFactory` that fills the FactoryBot role for Django
models; its own behaviour is covered by `tests/test_django_factory.py`, and its
deviations from FactoryBot are documented in the module docstring. Pydantic schemas use
PolyFactory directly, with no adapter.

`tests/testapp/` holds throwaway models used only to exercise that adapter. They are
not domain models.
