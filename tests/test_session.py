"""Unit tests for the choice what a request does about the Keycloak session (COMPASS REQ-058). No Frappe site needed: python -m unittest."""
import unittest

from compass_sso.session import CHECK_INTERVAL_SECONDS, next_step


class NextStepTest(unittest.TestCase):
	def test_a_session_without_a_remembered_token_ends(self):
		self.assertEqual(next_step(None, 1000.0), "end")
		self.assertEqual(next_step({}, 1000.0), "end")

	def test_a_recent_check_is_not_repeated(self):
		self.assertEqual(next_step({"checked_at": 1000.0 - CHECK_INTERVAL_SECONDS + 1}, 1000.0), "skip")

	def test_an_old_check_renews_the_token(self):
		self.assertEqual(next_step({"checked_at": 1000.0 - CHECK_INTERVAL_SECONDS}, 1000.0), "check")


class EndSessionTest(unittest.TestCase):
	def end(self, redirect):
		from unittest import mock

		import frappe

		from compass_sso import session

		fake = mock.Mock(SessionExpired=frappe.SessionExpired)
		with mock.patch.object(session, "frappe", fake), mock.patch.object(session.store, "forget"), \
			mock.patch.object(session, "redirect_guest_to_keycloak", redirect):
			session._end_session()

	def test_the_redirect_for_a_page_comes_before_the_expired_error(self):
		from unittest import mock

		class Redirected(Exception):
			pass

		redirect = mock.Mock(side_effect=Redirected)
		with self.assertRaises(Redirected):
			self.end(redirect)
		redirect.assert_called_once_with("Guest")

	def test_without_a_redirect_the_session_expires(self):
		import frappe

		with self.assertRaises(frappe.SessionExpired):
			self.end(lambda user: None)
