"""Unit tests for the Nextcloud entry of the app overview (COMPASS REQ-039). No Frappe needed: python -m unittest."""
import unittest

from compass_sso.apps_screen import desk_entry, landing_path, nextcloud_entry, window_name


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


class LandingPathTest(unittest.TestCase):
	def test_the_deprecated_app_switcher_becomes_the_overview(self):
		self.assertEqual(landing_path("https://team.example.org/apps"), "https://team.example.org/start")
		self.assertEqual(landing_path("/apps/"), "/start")

	def test_any_other_address_stays(self):
		for location in ("/crm", "/desk", "https://team.example.org/helpdesk/tickets", "/appstore"):
			self.assertEqual(landing_path(location), location)


class WindowNameTest(unittest.TestCase):
	def test_an_app_has_one_window_by_its_name(self):
		self.assertEqual(window_name({"name": "crm", "title": "CRM"}), "compass-crm")

	def test_the_entries_of_compass_sso_are_told_apart_by_title(self):
		self.assertEqual(window_name({"name": "compass_sso", "title": "Desk"}), "compass-desk")
		self.assertEqual(window_name({"name": "compass_sso", "title": "Nextcloud"}), "compass-nextcloud")
