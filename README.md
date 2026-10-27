# Accounts Receivable

Welcome to the Accounts Receivable system! This system is responsible for creating,
sending, and tracking invoices sent to clients so we can be paid for our products and
services.

> **Status: domain complete.** All five tables from the Rails source — clients, products,
> services, invoices, and line items — are built end to end: models, seed data, CRUD pages
> behind the application shell, and a read-only JSON API. The invoice page prices each
> line item, subtotals it, and totals the invoice.

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

Optionally load development seed data (two clients, two products, two services, and two
Acme invoices with five line items between them):

    $ uv run python manage.py seed

That command is safe to re-run; it will not duplicate rows.

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
deviations from FactoryBot are documented in the module docstring. Pydantic schemas
need no adapter — PolyFactory supports them natively.

Domain factories live in `tests/factories/domain.py`. `tests/testapp/` holds throwaway
models used only to exercise the adapter, with their factories in
`tests/factories/models.py`; neither is part of the domain.

> Never name a pytest fixture `client` — pytest-django reserves it for the Django test
> client, and this domain's central noun is `Client`.

### Preserved defects

The Rails source is an interview exercise and is **deliberately flawed** in its money and
total arithmetic. This port reproduces those flaws rather than fixing them, because
fixing them silently would destroy the exercise. Two sites carry them, each commented and
covered by tests that assert the wrong answer on purpose:

* `accounts_receivable/templatetags/money.py` — the formatter drops the leading zero
  below a dollar, omits thousands separators, misplaces a minus sign, and raises
  `IndexError` under ten cents.
* `InvoiceDetailView` in `accounts_receivable/views.py` — a line item priced from a
  zero-cost product or service is dropped from the invoice table and its total.

The JSON API does **not** reproduce the second one: `Invoice.total_cents` is the honest
sum, and the Rails app has no API for it to be faithful to. The invoice page and
`GET /api/invoices/<id>` can therefore report different totals, which is intended.

### Project decisions

`CLAUDE.md` records the standing decisions behind this project, including the one that
shapes the most code: this application will never have authentication or login sessions.
