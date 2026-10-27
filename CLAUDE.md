# Project decisions

Standing decisions for the Accounts Receivable Django app. `README.md` covers how to run
and test the project; this file records the choices behind it, so a later pass does not
quietly undo them.

## No authentication, ever

**This application will never have authentication, login, or sessions.** It is a
single-tenant internal tool with no users, and the Rails app it ports has none either.
This is not a "not yet" — there is nothing to add later.

What follows from it:

* Do not add `django.contrib.auth`, `django.contrib.sessions`, or `django.contrib.admin`
  to `INSTALLED_APPS`. They are omitted on purpose (`config/settings.py`).
* `MESSAGE_STORAGE` is cookie-backed precisely because sessions is not installed. Leave
  it that way.
* No `login_required`, no `LoginRequiredMiddleware`, no permission classes, no
  `request.user`, no `created_by`/`owner` columns, no per-user query scoping.
* The JSON API is unauthenticated and CSRF-exempt — Django Ninja's default, and correct
  here.
* `SECRET_KEY` is committed in plain text and `DEBUG = True`. There is no deployment, so
  there is no secret to protect.
* If a task appears to need a current user, the task is wrong. Ask rather than inventing
  an auth layer.

Data entry happens through the app's own views, so the usual reason to reach for the
Django admin — and the `auth` dependency it drags in — does not apply.

## A port, not a greenfield app

This is a port of the Rails app at `accounts-receivable-rails`. Three sibling ports
(Node, .NET, and the Rails original) model the same domain, so **fidelity to the Rails
source is the tie-breaker** on schema and behaviour questions: `db/schema.rb` decides
field shapes, `db/seeds.rb` decides seed data, and the model files decide validations.

Where Python or Django forces a divergence (e.g. `CharField` requires `max_length`, which
Rails' SQLite schema does not declare), note it in a comment at the site.

## Python is pinned to 3.14.9

`.tool-versions` is the single source of truth — there is deliberately no
`.python-version`. The pin is 3.14.9 rather than 3.15 because Django's 3.15 support lands
in Django 6.1.3 (expected 2026-11-03). `requires-python` already allows 3.15, so the bump
is a one-line change once that ships. See README "Python version".

## Configuration

One settings module (`config/settings.py`), with test-only overrides in
`config/test_settings.py`. There is no deployment story and no environment-based
configuration; add neither speculatively.

## Factories, and the `client` fixture trap

Test data goes through the hand-written PolyFactory adapter in `tests/factories/base.py`
(PolyFactory ships no `DjangoModelFactory`). Domain factories live in
`tests/factories/domain.py`; `tests/factories/models.py` is for the throwaway models in
`tests/testapp/` that exercise the adapter itself.

**Never name a pytest fixture, or a parameter that shadows one, `client`.** pytest-django
reserves `client` for the Django test client, and this domain's central noun is `Client`
— shadowing it breaks every view test in a baffling way. Use `acme`, `clients`, or a
similar name instead.

## Seed data

`uv run python manage.py seed` loads development data and is safe to re-run: it uses
`get_or_create`, mirroring the Rails seed's `find_or_create_by`. A management command
rather than a `loaddata` fixture, because fixtures pin primary keys and overwrite rows on
every load.
