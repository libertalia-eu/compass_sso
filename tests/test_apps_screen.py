"""Unit tests for the Nextcloud entry of the app overview (COMPASS REQ-039). No Frappe needed: python -m unittest."""
import unittest

from compass_sso.apps_screen import desk_entry, nextcloud_entry


class NextcloudEntryTest(unittest.TestCase):
	def test_url_gives_one_entry_with_logo_and_route(self):
		self.assertEqual(
			nextcloud_entry("https://cloud.example.org"),
			[{"name": "nextcloud", "logo": "https://cloud.example.org/apps/theming/icon", "title": "Nextcloud", "route": "https://cloud.example.org", "has_permission": "compass_sso.apps_screen.has_nextcloud_access"}],
		)

	def test_trailing_slash_and_spaces_are_dropped(self):
		self.assertEqual(nextcloud_entry(" https://cloud.example.org/ ")[0]["route"], "https://cloud.example.org")

	def test_no_url_gives_no_entry(self):
		self.assertEqual(nextcloud_entry(None), [])
		self.assertEqual(nextcloud_entry("  "), [])


class DeskEntryTest(unittest.TestCase):
	def test_one_entry_to_desk_for_users_who_may_open_it(self):
		self.assertEqual(
			desk_entry(),
			[{"name": "desk", "logo": "/assets/frappe/images/framework.png", "title": "Desk", "route": "/desk", "has_permission": "compass_sso.apps_screen.has_desk_access"}],
		)
