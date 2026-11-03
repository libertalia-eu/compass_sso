"""Unit tests for the choice which requests go straight to Keycloak (REQ-018). No Frappe needed: python -m unittest."""
import unittest

from compass_sso.login_redirect import goes_to_keycloak


class GoesToKeycloakTest(unittest.TestCase):
	def test_guest_opening_the_login_page_or_the_app(self):
		for path in ("/login", "/crm", "/crm/leads/view"):
			self.assertTrue(goes_to_keycloak("GET", path, "Guest", "crm"), path)

	def test_signed_in_user_is_not_redirected(self):
		self.assertFalse(goes_to_keycloak("GET", "/login", "alice@example.test", "crm"))

	def test_post_is_not_redirected(self):
		self.assertFalse(goes_to_keycloak("POST", "/login", "Guest", "crm"))

	def test_other_paths_are_not_redirected(self):
		for path in ("/api/method/ping", "/api/method/compass_sso.api.backchannel_logout", "/app", "/login/x", "/crmx", "/assets/crm/x.js"):
			self.assertFalse(goes_to_keycloak("GET", path, "Guest", "crm"), path)


if __name__ == "__main__":
	unittest.main()
