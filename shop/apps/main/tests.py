"""
Selenium UI tests for Phygitalist.

Running tests:
    cd /home/arun/Projects/zite69/Project-Phygitalist
    python manage.py test shop.apps.main.tests --settings=shop.test_settings --verbosity=2

Requirements:
    pip install selenium webdriver-manager

Watch the browser while debugging (disables headless mode):
    SELENIUM_HEADLESS=0 python manage.py test shop.apps.main.tests --settings=shop.test_settings

Multi-site setup:
    The project serves two sites:
      - Buyer site:  www.z69.local   (SITE_ID=1, urls.py)
      - Seller site: seller.z69.local (SITE_ID=2, urls_seller.py)

    DynamicSiteMiddleware resolves the site by matching request.get_host()
    (which includes the port) against the Site.domain in the database.

    StaticLiveServerTestCase starts on a random port and binds to 127.0.0.1.
    Both hostnames resolve to 127.0.0.1 via /etc/hosts:
        127.0.0.1 www.z69.local seller.z69.local

    SiteFixtureMixin.setUp() creates the two Site rows after the server has
    started, storing the domain WITH port (e.g. www.z69.local:8081) so that
    the middleware lookup succeeds.
"""

import os
import time
from pathlib import Path

import environ

_env = environ.Env()
_env.read_env(Path(__file__).resolve().parents[3] / '.env')

import factory
from allauth.socialaccount.models import SocialApp
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import TestCase
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

User = get_user_model()

# ---------------------------------------------------------------------------
# Site constants — match /etc/hosts entries
# ---------------------------------------------------------------------------

BUYER_HOST = _env.str('BUYER_HOST', default='www.z69.local')
SELLER_HOST = _env.str('SELLER_HOST', default='seller.z69.local')

# Match settings.py SITE_ID / SELLER_SITE_ID
BUYER_SITE_ID = 1
SELLER_SITE_ID = 2


# ---------------------------------------------------------------------------
# Site fixture mixin
# ---------------------------------------------------------------------------

class SiteFixtureMixin:
    """
    Creates / updates the two Site rows before each test.

    For Selenium tests the domain is stored with port (e.g. www.z69.local:8081)
    because DynamicSiteMiddleware matches on request.get_host(), which includes
    the port for non-standard ports.

    Subclasses must provide a ``_server_port`` class attribute (set in
    setUpClass once the live server has started) or leave it as None, in which
    case the domains are stored without a port (suitable for Django test-client
    tests that never go through the middleware's Site lookup).
    """

    _server_port = None  # overridden in SeleniumTestCase.setUpClass

    def setUp(self):
        super().setUp()
        self._setup_sites()

    def _setup_sites(self):
        port = self.__class__._server_port

        def domain(host):
            return f'{host}:{port}' if port else host

        buyer_site, _ = Site.objects.update_or_create(
            id=BUYER_SITE_ID,
            defaults={'domain': domain(BUYER_HOST), 'name': 'Buyer Site (test)'},
        )
        Site.objects.update_or_create(
            id=SELLER_SITE_ID,
            defaults={'domain': domain(SELLER_HOST), 'name': 'Seller Site (test)'},
        )

        # The login template renders {% provider_login_url 'google' %} even
        # inside HTML comments (Django processes template tags before HTML
        # parsing).  A SocialApp row must exist or allauth raises DoesNotExist.
        google_app, _ = SocialApp.objects.get_or_create(
            provider='google',
            defaults={
                'name': 'Google (test)',
                'client_id': 'test-client-id',
                'secret': 'test-secret',
            },
        )
        google_app.sites.add(buyer_site)


# ---------------------------------------------------------------------------
# Factories — test-data helpers using factory_boy
# ---------------------------------------------------------------------------

class UserFactory(factory.django.DjangoModelFactory):
    """
    Creates a regular (buyer) user with a known password.

    Usage:
        user = UserFactory()                             # default password: testpass123
        user = UserFactory(username='alice', password='secret99')
        assert user.check_password('secret99')           # True

    The raw password is hashed via create_user() so the DB stores only the
    hash.  The plain-text password is attached to the instance as
    user._raw_password for convenience.
    """

    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'testuser{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True

    _password = 'testpass123'

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop('password', cls._password)
        # The custom UserManager.create_user(username, ...) hard-codes several
        # fields (email from username, is_active, is_staff, is_superuser,
        # last_login, date_joined).  Passing them as extra kwargs causes
        # "multiple values for keyword argument" errors, so pop them first and
        # re-apply the ones that matter after creation.
        email = kwargs.pop('email', None)
        is_active = kwargs.pop('is_active', True)
        is_staff = kwargs.pop('is_staff', False)
        is_superuser = kwargs.pop('is_superuser', False)

        user = model_class.objects.create_user(*args, **kwargs)
        user.set_password(password)
        # Override any hardcoded values in create_user that differ from factory.
        user.is_active = is_active
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        if email:
            user.email = email
        user.save()
        user._raw_password = password
        return user


class StaffUserFactory(UserFactory):
    """Creates a staff/admin user."""
    username = factory.Sequence(lambda n: f'staffuser{n}')
    is_staff = True


# ---------------------------------------------------------------------------
# Selenium base class
# ---------------------------------------------------------------------------

def _make_chrome_driver():
    """
    Return a configured Chromium WebDriver.

    Uses the system-installed chromedriver (/usr/bin/chromedriver) and
    Chromium binary (/usr/bin/chromium) so the versions always match without
    needing webdriver-manager.  Set SELENIUM_HEADLESS=0 to watch the browser.
    """
    opts = ChromeOptions()
    opts.binary_location = '/usr/bin/chromium'
    headless = os.environ.get('SELENIUM_HEADLESS', '1') != '0'
    if headless:
        opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--window-size=1280,900')
    service = ChromeService(executable_path='/usr/bin/chromedriver')
    return webdriver.Chrome(service=service, options=opts)


class SeleniumTestCase(SiteFixtureMixin, StaticLiveServerTestCase):
    """
    Base class for all Selenium UI tests.

    The test server binds to 127.0.0.1 so that both www.z69.local and
    seller.z69.local (both pointing to 127.0.0.1 in /etc/hosts) route to it.

    After the server starts we record the port and write it into the Site rows
    (via SiteFixtureMixin) so DynamicSiteMiddleware can resolve the correct
    site from the Host header.

    Provides:
      self.driver        — Chrome WebDriver
      self.wait          — WebDriverWait (10 s)
      self.url(path)     — buyer-site URL  (http://www.z69.local:PORT/path)
      self.seller_url(p) — seller-site URL (http://seller.z69.local:PORT/path)
    """

    host = '127.0.0.1'  # bind address; both .local names resolve here

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # live_server_url is now set, e.g. "http://127.0.0.1:8081"
        cls._server_port = cls.live_server_url.rsplit(':', 1)[-1]
        cls.driver = _make_chrome_driver()
        cls.driver.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        super().setUp()  # calls SiteFixtureMixin.setUp → _setup_sites
        self.wait = WebDriverWait(self.driver, timeout=10)

    def url(self, path):
        """Buyer-site URL: http://www.z69.local:PORT/path"""
        return f'http://{BUYER_HOST}:{self._server_port}{path}'

    def seller_url(self, path):
        """Seller-site URL: http://seller.z69.local:PORT/path"""
        return f'http://{SELLER_HOST}:{self._server_port}{path}'

    # ------------------------------------------------------------------
    # Login helper
    # ------------------------------------------------------------------

    def _fill_login_form(self, login_value, password):
        """
        Navigate to the buyer-site login page and submit the classic
        username+password form (not the OTP form above it).

        Form fields (from templates/account/login.html):
            <input id="id_login"    name="login"    …>
            <input id="id_password" name="password" …>
        """
        self.driver.get(self.url('/accounts/login/'))

        login_input = self.wait.until(
            EC.presence_of_element_located((By.ID, 'id_login'))
        )
        password_input = self.driver.find_element(By.ID, 'id_password')

        login_input.clear()
        login_input.send_keys(login_value)
        password_input.clear()
        password_input.send_keys(password)

        # The login template has multiple forms (OTP, classic password, signup).
        # The classic password form's submit button has value="login":
        #   <button type="submit" name="submit" value="login">Login</button>
        submit_btn = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'button[type="submit"][value="login"]'))
        )
        # Scroll into view, then JS-click to bypass any overlay (e.g. a sticky
        # header or cookie banner) that intercepts a native pointer click.
        self.driver.execute_script(
            'arguments[0].scrollIntoView({block: "center"}); arguments[0].click();',
            submit_btn,
        )


# ---------------------------------------------------------------------------
# Login page tests
# ---------------------------------------------------------------------------

class LoginPageTests(SeleniumTestCase):
    """Selenium tests for the buyer-site login page."""

    def test_login_page_loads(self):
        """Login page renders the username and password inputs."""
        self.driver.get(self.url('/accounts/login/'))

        login_input = self.wait.until(
            EC.presence_of_element_located((By.ID, 'id_login'))
        )
        self.assertTrue(login_input.is_displayed(), 'Login input should be visible.')
        self.assertTrue(
            self.driver.find_element(By.ID, 'id_password').is_displayed(),
            'Password input should be visible.',
        )

    def test_login_fails_with_wrong_credentials(self):
        """
        Entering username 'abcd' and password 'pass123' (neither exists)
        must NOT redirect away from the login page.  An error message
        should appear on the page.
        """
        self._fill_login_form('abcd', 'pass123')

        time.sleep(1)  # allow redirect / page-load to settle

        # Primary assertion: should still be on the login page.
        # A successful login would redirect away (to / or the next URL).
        self.assertIn(
            '/accounts/login/',
            self.driver.current_url,
            'Browser should stay on login page after bad credentials.',
        )

        # Secondary assertion: the login form must still be present on the
        # page (not a "you are now logged in" page).
        # Note: the custom login template does not render {{ form.errors }}, so
        # we cannot check for allauth error text — the URL check above is the
        # authoritative signal that login was rejected.
        login_input = self.driver.find_element(By.ID, 'id_login')
        self.assertTrue(
            login_input.is_displayed(),
            'Login form should still be visible after failed attempt.',
        )

    def test_login_succeeds_with_valid_credentials(self):
        """
        A user created via UserFactory can log in through the browser.
        On success allauth redirects away from /accounts/login/.
        """
        user = UserFactory(username='buyer1', password='MySecret!99')

        self._fill_login_form('buyer1', 'MySecret!99')

        time.sleep(1)

        self.assertNotIn(
            '/accounts/login/',
            self.driver.current_url,
            f'Expected redirect after successful login for {user.username}.',
        )


# ---------------------------------------------------------------------------
# Pure Django test-client tests (fast, no browser)
# ---------------------------------------------------------------------------

class UserModelTests(SiteFixtureMixin, TestCase):
    """
    Non-Selenium tests using Django's test client.
    Fast — use these for business-logic assertions that don't need a browser.

    The test client sends requests with SERVER_NAME='testserver' by default.
    DynamicSiteMiddleware can't find 'testserver' in the Site table and falls
    back to DEFAULT_SITE_ID=1 (buyer site), which is the correct behaviour
    for buyer-site tests.

    To test the seller site, pass SERVER_NAME=SELLER_HOST:
        self.client.post('/...', data={...}, SERVER_NAME=SELLER_HOST)
    """

    def test_create_user_via_factory(self):
        """UserFactory creates an active user with a correctly hashed password."""
        user = UserFactory()
        self.assertTrue(user.is_active)
        self.assertTrue(user.has_usable_password())
        self.assertTrue(user.check_password('testpass123'))

    def test_login_view_rejects_bad_credentials(self):
        """
        POSTing a non-existent username/password to the login endpoint should
        NOT produce a redirect — allauth re-renders the form with errors (200).
        """
        response = self.client.post(
            '/accounts/login/',
            data={'login': 'abcd', 'password': 'pass123'},
            follow=False,
        )
        # allauth returns 200 (form re-render) on bad creds, not 302.
        self.assertNotEqual(
            response.status_code, 302,
            'A failed login must not redirect.',
        )

    def test_login_view_accepts_valid_credentials(self):
        """Correct credentials should produce a 302 redirect."""
        UserFactory(username='gooduser', password='GoodPass!1')
        response = self.client.post(
            '/accounts/login/',
            data={'login': 'gooduser', 'password': 'GoodPass!1'},
            follow=False,
        )
        self.assertEqual(
            response.status_code, 302,
            'A successful login should redirect (302).',
        )
