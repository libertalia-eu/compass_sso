"""Unit tests for the language that follows Keycloak (COMPASS REQ-088). No Frappe needed: python -m unittest."""
import unittest

from compass_sso.language import language_of


class LanguageOfTest(unittest.TestCase):
	def test_a_supported_locale_is_taken(self):
		self.assertEqual(language_of({"locale": "de"}), "de")
		self.assertEqual(language_of({"locale": "en"}), "en")

	def test_no_locale_or_an_unknown_one_gives_english(self):
		self.assertEqual(language_of({}), "en")
		self.assertEqual(language_of({"locale": "fr"}), "en")
