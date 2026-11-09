"""Unit tests for the choice which requests go straight to Keycloak (REQ-018). No Frappe needed: python -m unittest."""
import unittest

from compass_sso.login_redirect import app_routes_of, goes_to_keycloak, sends_to_overview


class GoesToKeycloakTest(unittest.TestCase):
	def test_guest_opening_the_login_page_or_the_app(self):
		for path in ("/login", "/", "/crm", "/crm/leads/view"):
			self.assertTrue(goes_to_keycloak("GET", path, "Guest", ("crm",)), path)

	def test_signed_in_user_is_not_redirected(self):
		self.assertFalse(goes_to_keycloak("GET", "/login", "alice@example.test", ("crm",)))

	def test_post_is_not_redirected(self):
		self.assertFalse(goes_to_keycloak("POST", "/login", "Guest", ("crm",)))

	def test_other_paths_are_not_redirected(self):
		for path in ("/api/method/ping", "/api/method/compass_sso.api.backchannel_logout", "/app", "/login/x", "/crmx", "/assets/crm/x.js"):
			self.assertFalse(goes_to_keycloak("GET", path, "Guest", ("crm",)), path)

	def test_every_app_of_the_site_goes_to_keycloak(self):
		for path in ("/crm", "/helpdesk/tickets", "/raven", "/apps"):
			self.assertTrue(goes_to_keycloak("GET", path, "Guest", ("crm", "helpdesk", "raven", "apps")), path)
		self.assertFalse(goes_to_keycloak("GET", "/helpdesk", "Guest", ("crm",)))

	def test_routes_come_from_the_apps_screen_hooks(self):
		screen = [{"route": "/crm"}, {"route": "/helpdesk"}, {"name": "no-route"}]
		self.assertEqual(app_routes_of(screen, None), {"crm", "helpdesk", "apps", "start"})
		self.assertEqual(app_routes_of([], "raven"), {"raven", "apps", "start"})


if __name__ == "__main__":
	unittest.main()


class SendsToOverviewTest(unittest.TestCase):
	def test_a_signed_in_user_on_the_deprecated_app_switcher_goes_to_the_overview(self):
		for path in ("/apps", "/apps/"):
			self.assertTrue(sends_to_overview("GET", path, "alice@example.test"), path)

	def test_a_guest_a_post_and_other_paths_stay(self):
		self.assertFalse(sends_to_overview("GET", "/apps", "Guest"))
		self.assertFalse(sends_to_overview("POST", "/apps", "alice@example.test"))
		for path in ("/crm", "/desk", "/appstore", "/apps/x"):
			self.assertFalse(sends_to_overview("GET", path, "alice@example.test"), path)
