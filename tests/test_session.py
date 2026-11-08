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
