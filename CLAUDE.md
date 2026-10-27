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

The schema is the Rails schema, including where the field names read oddly. `invoices`
has `net_days` and `note` — there is **no** `subject` or `issue_date` column. The show
page renders the note as the invoice's subject line and derives a due date from
`created_at + net_days`; `created_at` is the issue date. The override column on
`line_items` is `price_override_cents`, not `price_cents_override`.

## Planted bugs are preserved

The Rails source is an interview exercise and is deliberately flawed: its git history
includes a commit that reverted correct money formatting back to broken string surgery.
**This port reproduces those flaws.** Fixing them silently destroys the exercise, so they
are commented as intentional at each site and pinned by tests that assert the wrong
answer:

* `accounts_receivable/templatetags/money.py` — `to_money` splices a decimal point into
  the digit string, so `50` renders as `$.50`, `100000` as `$1000.00`, `-5` as `$.-5`,
  and anything under ten cents raises `IndexError`. Covered by `tests/test_money.py`.
* `InvoiceDetailView.get_context_data` — ports Rails'
  `where("products.price_cents != 0")`, so a line item priced from a zero-cost product or
  service vanishes from the invoice table and its total, even when a price override says
  to bill for it. Covered by `tests/test_invoices.py`.

If a test here fails because someone corrected the arithmetic, the correction is the
regression. Confirm with Kyle Adams before changing either site.

Two things are deliberately **not** flawed. `Invoice.total_cents` and the JSON API give
the honest total — the Rails app has no API, so there is nothing to be faithful to, and
the page and `GET /api/invoices/<id>` are expected to disagree. And
`InvoicesController`'s `after_action :save_line_items`, a no-op re-save of every child
row, is not ported: it is dead weight rather than observable behaviour.

**One trap that is not a planted bug.** Rails writes
`price_override_cents || product.price_cents`, and Ruby's `||` only falls through on
`nil` — so an override of **`0`** is honoured there as a genuinely free line. Python's
`or` and the DTL's `|default:` both treat `0` as falsy and would silently charge the
catalog price. `LineItem.unit_price_cents` therefore tests `is not None`, and
`test_an_override_of_zero_is_honoured` exists to keep it that way.

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

The same collision bites on the import side. A view test needs both `Client` the model
and `Client` the test client, and the obvious alias is a trap: `from django.test import
Client as TestClient` makes pytest try to **collect** `TestClient` as a test class, and
the whole module errors out during collection. Alias it to something that does not start
with `Test` — these tests use `DjangoClient`.

## UI and templates

Pages follow the design prototype: a fixed dark (`#1a1a1a`) sidebar, a monospace
breadcrumb bar, serif page titles, and white cards with a `#e4e4e4` hairline border. The
teal is `#0d6e6e`, declared once as `brand` in the Tailwind CDN config in `base.html`
rather than repeated as an arbitrary value.

Every resource in the domain is now built, so every sidebar item is a real `<a>`; the
muted, non-clickable `<span>` placeholders are gone. Line items live at `/line_items/`
with an underscore, because that is the path Rails' `resources :line_items` generates.

**Django template comments are single-line.** `{# ... #}` spanning two lines is served to
the browser verbatim; use `{% comment %}` blocks for anything longer than one line.

## Seed data

`uv run python manage.py seed` loads development data and is safe to re-run: it uses
`get_or_create`, mirroring the Rails seed's `find_or_create_by`. A management command
rather than a `loaddata` fixture, because fixtures pin primary keys and overwrite rows on
every load.

Clients, products and services are keyed on `name`, which `_load` handles. Invoices and
line items have no name, so they get their own methods, keyed on `(client, note)` and
`(invoice, description)` respectively — unique within the seed data.
