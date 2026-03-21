"""
Test-specific Django settings.

Usage:
    python manage.py test --settings=shop.test_settings <test_path>

Or set DJANGO_SETTINGS_MODULE once and forget it:
    export DJANGO_SETTINGS_MODULE=shop.test_settings

What this changes vs. shop.settings:
- Removes debug_toolbar from INSTALLED_APPS and MIDDLEWARE (it can't run with
  DEBUG=False, which Django enforces during tests).
- Uses an in-memory SQLite database so tests don't touch your real database.
- Disables password hashing to speed up UserFactory.create() calls.
- Silences the sorl/easy-thumbnails template-tag warning.
"""

from shop.settings import *  # noqa: F401, F403

# --- Remove debug_toolbar (incompatible with tests) -------------------------
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'debug_toolbar']
MIDDLEWARE = [m for m in MIDDLEWARE if 'debug_toolbar' not in m]

# --- Fast in-memory test database -------------------------------------------
# Using "file:mem" + ATOMIC_REQUESTS keeps each test isolated while still
# allowing the connection to be shared within a test (needed by
# StaticLiveServerTestCase).
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'file:testdb?mode=memory&cache=shared',
        'TEST': {
            'NAME': 'file:testdb?mode=memory&cache=shared',
        },
    }
}

# --- Fast password hashing ---------------------------------------------------
# MD5 is intentionally insecure but 1000× faster than PBKDF2.
# Only ever use this in tests.
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# --- Email goes to /dev/null during tests ------------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

# --- Use plain (non-hashed) static files storage ----------------------------
# ManifestStaticFilesStorage requires `collectstatic` to have been run first,
# which is not the case in a CI/test environment.  Switch to the simple
# storage backend so template {% static %} tags resolve without a manifest.
STORAGES = {
    **STORAGES,
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# --- Silence the sorl/easy-thumbnails duplicate-tag warning -----------------
SILENCED_SYSTEM_CHECKS = ['templates.W003']
