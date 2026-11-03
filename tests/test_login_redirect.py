"""Unit tests for the choice which requests go straight to Keycloak (REQ-018). No Frappe needed: python -m unittest."""
import unittest

from compass_sso.login_redirect import is_guest_login_page_request


class GuestLoginPageRequestTest(unittest.TestCase):
	def test_guest_opening_the_login_page(self):
		self.assertTrue(is_guest_login_page_request("GET", "/login", "Guest"))

	def test_signed_in_user_is_not_redirected(self):
		self.assertFalse(is_guest_login_page_request("GET", "/login", "alice@example.test"))

	def test_post_to_the_login_page_is_not_redirected(self):
		self.assertFalse(is_guest_login_page_request("POST", "/login", "Guest"))

	def test_other_paths_are_not_redirected(self):
		for path in ("/api/method/ping", "/api/method/compass_sso.api.backchannel_logout", "/app", "/login/x"):
			self.assertFalse(is_guest_login_page_request("GET", path, "Guest"), path)


if __name__ == "__main__":
	unittest.main()
